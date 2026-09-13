"""Zero-training geometry calibration for V6's public staged controller.

This bounded calibration selects a physically feasible branch time and future
corridor offset before any V6 learning run.  It never instantiates PPO.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from envs.commitment_handoff_intercept_3d_env import RECONSTRUCT_FUTURE, RETAIN_CURRENT, CommitmentHandoffIntercept3DEnv  # noqa: E402
from envs.timed_handoff_intercept_3d_env import TimedHandoffIntercept3DConfig  # noqa: E402


PROTOCOL = "COMMITMENT-HANDOFF-3D-V6-ZERO-TRAINING-GEOMETRY-CALIBRATION-V1"
SEEDS = (83_301, 83_302, 83_303)
BRANCH_STEPS = (32, 36, 40)
FUTURE_OFFSETS = (900.0, 1_100.0, 1_300.0, 1_500.0)
FUTURE_PROFILES = ("future_fresh", "future_durable")


def run_episode(seed: int, profile: str, branch_step: int, future_offset: float) -> dict[str, object]:
    env = CommitmentHandoffIntercept3DEnv(
        TimedHandoffIntercept3DConfig(
            seed=seed, handoff_context="current_authorization", authorization_start_step=12,
            authorization_deadline=28, branch_step=branch_step, authorization_hold_steps=8,
            refresh_hold_steps=16, handoff_corridor_radius=900.0,
            future_corridor_lateral_offset=future_offset, commitment_action_repeat=8,
            communication_dropout_prob=0.0, radar_dropout_prob=0.0, message_delay_steps=0,
            max_target_message_age_steps=10, target_init_range_scale=0.65,
            postbranch_target_policy="weaving_mild", max_steps=260,
            service_envelope_mode="compositional_v6_staged", service_envelope_profile=profile,
        )
    )
    env.reset(); info: dict[str, object] = {}
    for _ in range(env.config.max_steps):
        relay = RECONSTRUCT_FUTURE if env.step_count >= env.handoff_config.branch_step else RETAIN_CURRENT
        _, _, _, _, dones, info = env.step(np.asarray((RETAIN_CURRENT, relay, RETAIN_CURRENT), dtype=np.int64))
        if bool(dones[0, 0]):
            break
    return {
        "seed": seed, "profile": profile, "branch_step": branch_step, "future_offset": future_offset,
        "success": int(float(info.get("handoff_success", 0.0)) > 0.5),
        "authorization": int(float(info.get("authorization_handoff_observed", 0.0)) > 0.5),
        "refresh": int(float(info.get("postbranch_refresh_observed", 0.0)) > 0.5),
        "timeout": int(float(info.get("timeout", 0.0)) > 0.5),
        "collision": int(float(info.get("collision", 0.0)) > 0.5),
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
    rows = [
        run_episode(seed, profile, branch, offset)
        for branch in BRANCH_STEPS for offset in FUTURE_OFFSETS
        for profile in FUTURE_PROFILES for seed in SEEDS
    ]
    candidates = []
    for branch in BRANCH_STEPS:
        for offset in FUTURE_OFFSETS:
            cell = [row for row in rows if row["branch_step"] == branch and row["future_offset"] == offset]
            by_profile = {
                profile: float(np.mean([row["success"] for row in cell if row["profile"] == profile]))
                for profile in FUTURE_PROFILES
            }
            candidates.append({
                "branch_step": branch, "future_offset": offset,
                "min_profile_success": min(by_profile.values()),
                "mean_success": float(np.mean([row["success"] for row in cell])),
                "mean_authorization": float(np.mean([row["authorization"] for row in cell])),
                "mean_refresh": float(np.mean([row["refresh"] for row in cell])),
                "mean_collision": float(np.mean([row["collision"] for row in cell])),
                **{f"success_{profile}": by_profile[profile] for profile in FUTURE_PROFILES},
            })
    # Rank physical feasibility first, then preserve a later branch when it
    # is equally feasible to retain genuine two-stage decision time.
    selected = max(candidates, key=lambda row: (row["min_profile_success"], row["mean_success"], row["branch_step"], -row["future_offset"]))
    args.out_dir.mkdir(parents=True)
    with (args.out_dir / "v6_geometry_rows.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    with (args.out_dir / "v6_geometry_candidates.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(candidates[0])); writer.writeheader(); writer.writerows(candidates)
    report = {
        "protocol": PROTOCOL, "artifact_class": "DEVELOPMENT_ONLY_ZERO_TRAINING_PHYSICAL_CALIBRATION",
        "training_started": False, "selection_rule": "maximize min profile success, then mean success, then later branch, then smaller offset",
        "selected": selected, "all_candidates": candidates,
    }
    (args.out_dir / "v6_geometry_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
