"""Map legal-controller performance across frozen 3DOF difficulty bands.

The purpose is to select a non-saturated, physically feasible substrate before
any new learning method is introduced.  It is not a training or paper result.
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

from audit_intercept_3d_legal_baseline import legal_actions
from envs.uav_intercept_3d_env import UAVIntercept3DConfig, UAVIntercept3DEnv

SEEDS = (3201, 3202, 3203)
EPISODES = 40
CONDITIONS = {
    "nominal": dict(target_policy="straight", communication_dropout_prob=0.10, radar_dropout_prob=0.05, message_delay_steps=2),
    "moderate": dict(target_policy="weaving_mild", communication_dropout_prob=0.25, radar_dropout_prob=0.15, message_delay_steps=4),
    "stress": dict(target_policy="break_turn", communication_dropout_prob=0.35, radar_dropout_prob=0.20, message_delay_steps=5),
}
OUT = ROOT / "results" / "development" / "intercept_3d_difficulty_calibration"


def run_one(condition: str, seed: int, episode: int) -> dict[str, object]:
    cfg = UAVIntercept3DConfig(
        seed=400_000 + 10_000 * list(CONDITIONS).index(condition) + 100 * (seed - SEEDS[0]) + episode,
        strict_target_sensing=False,
        agent_target_info_bottleneck=False,
        relay_dependent_task=False,
        max_steps=260,
        **CONDITIONS[condition],
    )
    env = UAVIntercept3DEnv(cfg)
    obs, _, _ = env.reset()
    while True:
        obs, _, _, _, dones, info = env.step(legal_actions(obs))
        if bool(np.all(dones)):
            return {
                "condition": condition,
                "seed": seed,
                "episode": episode,
                "success": int(info["success"]),
                "timeout": int(info["timeout"]),
                "collision": int(info["collision"]),
                "constraint_violation": int(info["constraint_violation"]),
                "steps": int(info["step"]),
                "tracking_rate": float(info["tracking_rate"]),
                "attack_window_rate": float(info["attack_window_rate"]),
            }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=OUT)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("This development calibration requires --execute.")
    if (args.out_dir / "raw_episode_metrics.csv").exists():
        raise FileExistsError(f"Refusing to overwrite {args.out_dir}")
    rows = [run_one(condition, seed, episode) for condition in CONDITIONS for seed in SEEDS for episode in range(EPISODES)]
    args.out_dir.mkdir(parents=True, exist_ok=True)
    with (args.out_dir / "raw_episode_metrics.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    summary = []
    for condition in CONDITIONS:
        cell = [row for row in rows if row["condition"] == condition]
        summary.append({
            "condition": condition,
            "episodes": len(cell),
            "success_rate": float(np.mean([row["success"] for row in cell])),
            "timeout_rate": float(np.mean([row["timeout"] for row in cell])),
            "collision_rate": float(np.mean([row["collision"] for row in cell])),
            "mean_tracking_rate": float(np.mean([row["tracking_rate"] for row in cell])),
        })
    with (args.out_dir / "condition_summary.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary[0])); writer.writeheader(); writer.writerows(summary)
    usable = [row["condition"] for row in summary if 0.15 <= row["success_rate"] <= 0.85]
    manifest = {
        "protocol": "INTERCEPT-3D-DIFFICULTY-CALIBRATION-G0-V1",
        "artifact_class": "DEVELOPMENT_ONLY_LEGAL_CONTROLLER_CALIBRATION",
        "legal_information_only": True,
        "training_started": False,
        "canonical_data_used": False,
        "usable_non_saturated_conditions": usable,
        "verdict": "PASS" if usable else "NO_NON_SATURATED_BAND",
    }
    (args.out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
