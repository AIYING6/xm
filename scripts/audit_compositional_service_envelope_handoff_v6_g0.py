"""Zero-training decision-switch audit for the V6 staged service contract."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from envs.commitment_handoff_intercept_3d_env import (  # noqa: E402
    RECONSTRUCT_FUTURE,
    RETAIN_CURRENT,
    CommitmentHandoffIntercept3DEnv,
)
from envs.timed_handoff_intercept_3d_env import SERVICE_ENVELOPE_PROFILES, TimedHandoffIntercept3DConfig  # noqa: E402


PROTOCOL = "COMMITMENT-HANDOFF-3D-V6-STAGED-SERVICE-G0-V1"
SEEDS = (83_201, 83_202, 83_203, 83_204, 83_205, 83_206)
MODES = ("always_retain", "always_reconstruct", "public_stage_aware")
BRANCH_STEP = 40
FUTURE_CORRIDOR_LATERAL_OFFSET = 900.0


def relay_action(env: CommitmentHandoffIntercept3DEnv, mode: str) -> int:
    if mode == "always_retain":
        return RETAIN_CURRENT
    if mode == "always_reconstruct":
        return RECONSTRUCT_FUTURE
    if mode == "public_stage_aware":
        return RECONSTRUCT_FUTURE if env.step_count >= env.handoff_config.branch_step else RETAIN_CURRENT
    raise ValueError(mode)


def run_episode(seed: int, profile: str, mode: str) -> dict[str, object]:
    env = CommitmentHandoffIntercept3DEnv(
        TimedHandoffIntercept3DConfig(
            seed=seed, handoff_context="current_authorization", authorization_start_step=12,
            authorization_deadline=28, branch_step=BRANCH_STEP, authorization_hold_steps=8,
            refresh_hold_steps=16, handoff_corridor_radius=900.0,
            future_corridor_lateral_offset=FUTURE_CORRIDOR_LATERAL_OFFSET, commitment_action_repeat=8,
            communication_dropout_prob=0.0, radar_dropout_prob=0.0, message_delay_steps=0,
            max_target_message_age_steps=10, target_init_range_scale=0.65,
            postbranch_target_policy="weaving_mild", max_steps=260,
            service_envelope_mode="compositional_v6_staged", service_envelope_profile=profile,
        )
    )
    env.reset(); info: dict[str, object] = {}
    for _ in range(env.config.max_steps):
        action = relay_action(env, mode)
        _, _, _, _, dones, info = env.step(np.asarray((RETAIN_CURRENT, action, RETAIN_CURRENT), dtype=np.int64))
        if bool(dones[0, 0]):
            break
    return {
        "seed": seed, "profile": profile, "mode": mode,
        "future_required": int(env._future_service_required()),
        "success": int(float(info.get("handoff_success", 0.0)) > 0.5),
        "timeout": int(float(info.get("timeout", 0.0)) > 0.5),
        "collision": int(float(info.get("collision", 0.0)) > 0.5),
        "authorization_observed": int(float(info.get("authorization_handoff_observed", 0.0)) > 0.5),
        "refresh_observed": int(float(info.get("postbranch_refresh_observed", 0.0)) > 0.5),
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
    summary: dict[str, dict[str, object]] = {}
    passed = True
    for profile in SERVICE_ENVELOPE_PROFILES:
        cell = [row for row in rows if row["profile"] == profile]
        rates = {mode: float(np.mean([row["success"] for row in cell if row["mode"] == mode])) for mode in MODES}
        future = bool(cell[0]["future_required"])
        # Current profiles must be solvable by retaining.  Future profiles
        # must need the public phase-aware preserve-then-reconstruct sequence.
        profile_pass = rates["always_retain"] > 0.0 if not future else (
            rates["public_stage_aware"] > 0.0
            and rates["public_stage_aware"] > rates["always_retain"]
            and rates["public_stage_aware"] > rates["always_reconstruct"]
        )
        passed = passed and profile_pass
        summary[profile] = {"future_required": int(future), "success_rate": rates, "passes_profile": profile_pass}
    args.out_dir.mkdir(parents=True)
    with (args.out_dir / "v6_g0_rows.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    report = {
        "protocol": PROTOCOL, "artifact_class": "DEVELOPMENT_ONLY_ZERO_TRAINING_STAGED_DECISION_AUDIT",
        "training_started": False, "profiles": list(SERVICE_ENVELOPE_PROFILES), "modes": list(MODES),
        "branch_step": BRANCH_STEP, "future_corridor_lateral_offset": FUTURE_CORRIDOR_LATERAL_OFFSET,
        "summary": summary,
        "verdict": "V6_G0_STAGED_DECISION_SWITCH_PASS" if passed else "V6_G0_NOT_YET_ESTABLISHED",
    }
    (args.out_dir / "v6_g0_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
