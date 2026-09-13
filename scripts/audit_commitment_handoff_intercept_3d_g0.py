"""Zero-training decision-switch audit for the commitment-level 3DOF task."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from envs.commitment_handoff_intercept_3d_env import RECONSTRUCT_FUTURE, RETAIN_CURRENT, CommitmentHandoffIntercept3DEnv
from envs.timed_handoff_intercept_3d_env import HANDOFF_CONTEXTS, TimedHandoffIntercept3DConfig


PROTOCOL = "COMMITMENT-HANDOFF-INTERCEPT-3D-G0-V3-OPTION-H16"
SEEDS = (72201, 72202, 72203, 72204, 72205, 72206)
MODES = ("retain_current", "reconstruct_future")


def run_episode(
    seed: int,
    context: str,
    mode: str,
    future_offset: float,
    authorization_hold: int,
    refresh_hold: int,
) -> dict[str, object]:
    env = CommitmentHandoffIntercept3DEnv(
        TimedHandoffIntercept3DConfig(
            seed=seed,
            handoff_context=context,
            authorization_start_step=12,
            authorization_deadline=28,
            branch_step=40,
            authorization_hold_steps=authorization_hold,
            refresh_hold_steps=refresh_hold,
            handoff_corridor_radius=900.0,
            future_corridor_lateral_offset=future_offset,
            communication_dropout_prob=0.0,
            radar_dropout_prob=0.0,
            message_delay_steps=0,
            max_target_message_age_steps=10,
            target_init_range_scale=0.65,
            postbranch_target_policy="weaving_mild",
            max_steps=260,
        )
    )
    env.reset()
    action = RETAIN_CURRENT if mode == "retain_current" else RECONSTRUCT_FUTURE
    info: dict[str, object] = {}
    for _ in range(env.config.max_steps):
        _, _, _, _, dones, info = env.step(np.asarray((RETAIN_CURRENT, action, RETAIN_CURRENT), dtype=np.int64))
        if bool(dones[0, 0]):
            break
    return {
        "seed": seed,
        "context": context,
        "mode": mode,
        "success": int(float(info.get("handoff_success", 0.0)) > 0.5),
        "timeout": int(float(info.get("timeout", 0.0)) > 0.5),
        "collision": int(float(info.get("collision", 0.0)) > 0.5),
        "steps": int(float(info.get("step", 0.0))),
        "authorization_handoff_observed": int(float(info.get("authorization_handoff_observed", 0.0)) > 0.5),
        "postbranch_refresh_observed": int(float(info.get("postbranch_refresh_observed", 0.0)) > 0.5),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--future-offset", type=float, default=1_500.0)
    parser.add_argument("--authorization-hold", type=int, default=8)
    parser.add_argument("--refresh-hold", type=int, default=16)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("pass --execute")
    if args.out_dir.exists():
        raise FileExistsError(f"refusing to overwrite {args.out_dir}")
    if args.future_offset <= 0.0 or args.authorization_hold <= 0 or args.refresh_hold <= 0:
        raise ValueError("future-offset and hold lengths must be positive")
    rows = [
        run_episode(seed, context, mode, args.future_offset, args.authorization_hold, args.refresh_hold)
        for context in HANDOFF_CONTEXTS
        for seed in SEEDS
        for mode in MODES
    ]
    args.out_dir.mkdir(parents=True)
    with (args.out_dir / "commitment_handoff_g0_rows.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    summary = {}
    signs = []
    for context in HANDOFF_CONTEXTS:
        values = {mode: [row["success"] for row in rows if row["context"] == context and row["mode"] == mode] for mode in MODES}
        retain = float(np.mean(values[MODES[0]]))
        reconstruct = float(np.mean(values[MODES[1]]))
        signs.append(int(np.sign(reconstruct - retain)))
        summary[context] = {"retain_success": retain, "reconstruct_success": reconstruct, "reconstruct_minus_retain": reconstruct - retain}
    passed = len(set(signs)) > 1 and 0 not in signs
    report = {
        "protocol": PROTOCOL,
        "artifact_class": "DEVELOPMENT_ONLY_ZERO_TRAINING_DECISION_SWITCH_AUDIT",
        "training_started": False,
        "contexts": list(HANDOFF_CONTEXTS),
        "relay_commitment_actions": list(MODES),
        "commitment_action_repeat": 8,
        "future_corridor_lateral_offset": args.future_offset,
        "authorization_hold_steps": args.authorization_hold,
        "refresh_hold_steps": args.refresh_hold,
        "summary": summary,
        "decision_preference_reversal_observed": passed,
        "verdict": "G0_COMMITMENT_DECISION_SWITCH_PASS" if passed else "G0_COMMITMENT_DECISION_SWITCH_NOT_YET_ESTABLISHED",
        "interpretation": "A pass establishes only a legal macro-commitment decision switch on the original 3DOF plant; it does not establish learnability or a method effect.",
    }
    (args.out_dir / "commitment_handoff_g0_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
