"""Zero-training G0 audit for V5 compositional service-envelope handoff."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from envs.commitment_handoff_intercept_3d_env import (
    RECONSTRUCT_FUTURE,
    RETAIN_CURRENT,
    CommitmentHandoffIntercept3DEnv,
)
from envs.timed_handoff_intercept_3d_env import SERVICE_ENVELOPE_PROFILES, TimedHandoffIntercept3DConfig


PROTOCOL = "COMMITMENT-HANDOFF-3D-V5-SERVICE-ENVELOPE-G0-V1"
SEEDS = (82_201, 82_202, 82_203, 82_204, 82_205, 82_206)
MODES = ("retain_current", "reconstruct_future")


def run_episode(seed: int, profile: str, mode: str) -> dict[str, object]:
    env = CommitmentHandoffIntercept3DEnv(
        TimedHandoffIntercept3DConfig(
            seed=seed,
            handoff_context="current_authorization",  # inert in V5
            authorization_start_step=12,
            authorization_deadline=28,
            branch_step=40,
            authorization_hold_steps=8,
            refresh_hold_steps=16,
            handoff_corridor_radius=900.0,
            future_corridor_lateral_offset=1_500.0,
            commitment_action_repeat=8,
            communication_dropout_prob=0.0,
            radar_dropout_prob=0.0,
            message_delay_steps=0,
            max_target_message_age_steps=10,
            target_init_range_scale=0.65,
            postbranch_target_policy="weaving_mild",
            max_steps=260,
            service_envelope_mode="compositional_v5",
            service_envelope_profile=profile,
        )
    )
    env.reset()
    action = RETAIN_CURRENT if mode == "retain_current" else RECONSTRUCT_FUTURE
    info: dict[str, object] = {}
    for _ in range(env.config.max_steps):
        _, _, _, _, dones, info = env.step(np.asarray((RETAIN_CURRENT, action, RETAIN_CURRENT), dtype=np.int64))
        if bool(dones[0, 0]):
            break
    current, future = env._service_envelopes()
    return {
        "seed": seed,
        "profile": profile,
        "mode": mode,
        "future_required": int(env._future_service_required()),
        "current_envelope": list(current),
        "future_envelope": list(future),
        "success": int(float(info.get("handoff_success", 0.0)) > 0.5),
        "timeout": int(float(info.get("timeout", 0.0)) > 0.5),
        "collision": int(float(info.get("collision", 0.0)) > 0.5),
        "steps": int(float(info.get("step", 0.0))),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("pass --execute")
    if args.out_dir.exists():
        raise FileExistsError(f"refusing to overwrite {args.out_dir}")
    rows = [run_episode(seed, profile, mode) for profile in SERVICE_ENVELOPE_PROFILES for seed in SEEDS for mode in MODES]
    args.out_dir.mkdir(parents=True)
    with (args.out_dir / "v5_g0_rows.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    summary: dict[str, dict[str, object]] = {}
    signs: list[int] = []
    required_routes: list[int] = []
    for profile in SERVICE_ENVELOPE_PROFILES:
        cell = [row for row in rows if row["profile"] == profile]
        retain = float(np.mean([row["success"] for row in cell if row["mode"] == "retain_current"]))
        reconstruct = float(np.mean([row["success"] for row in cell if row["mode"] == "reconstruct_future"]))
        sign = int(np.sign(reconstruct - retain))
        signs.append(sign)
        required_routes.append(int(cell[0]["future_required"]))
        summary[profile] = {
            "retain_success": retain,
            "reconstruct_success": reconstruct,
            "reconstruct_minus_retain": reconstruct - retain,
            "future_required": int(cell[0]["future_required"]),
            "current_envelope": cell[0]["current_envelope"],
            "future_envelope": cell[0]["future_envelope"],
        }
    passed = all(sign != 0 for sign in signs) and set(signs) == {-1, 1} and set(required_routes) == {0, 1}
    report = {
        "protocol": PROTOCOL,
        "artifact_class": "DEVELOPMENT_ONLY_ZERO_TRAINING_DECISION_SWITCH_AUDIT",
        "training_started": False,
        "profiles": list(SERVICE_ENVELOPE_PROFILES),
        "relay_commitment_actions": list(MODES),
        "summary": summary,
        "decision_preference_reversal_observed": passed,
        "verdict": "V5_G0_COMPOSITIONAL_DECISION_SWITCH_PASS" if passed else "V5_G0_NOT_YET_ESTABLISHED",
    }
    (args.out_dir / "v5_g0_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
