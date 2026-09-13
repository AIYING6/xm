"""Read-only legal-observation feasibility audit for the mature 3DOF task.

This development diagnostic distinguishes a controller that can see only an
agent's emitted observation from a physical-state oracle.  It intentionally
does not create checkpoints, start learning, or make a method claim.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from envs.uav_intercept_3d_env import ACTION3D_TABLE, UAVIntercept3DConfig, UAVIntercept3DEnv, angle_diff

SEEDS = (3101, 3102, 3103)
EPISODES = 40
OUT = ROOT / "results" / "development" / "intercept_3d_legal_baseline"


def nearest_actions(turn: np.ndarray, climb: np.ndarray) -> np.ndarray:
    commands = np.zeros((3, 3), dtype=np.float32)
    commands[:, 0] = np.clip(turn, -1.0, 1.0)
    commands[:, 1] = np.clip(climb, -1.0, 1.0)
    commands[:, 2] = 1.0
    return np.argmin(((ACTION3D_TABLE[None, :, :] - commands[:, None, :]) ** 2).sum(axis=-1), axis=1)


def legal_actions(obs: np.ndarray) -> np.ndarray:
    """Track the target using only documented local observation entries."""
    turn, climb = np.zeros(3), np.zeros(3)
    max_turn = (0.035, 0.030, 0.052)
    max_climb = (0.26, 0.22, 0.31)
    for agent in range(3):
        rel_x, rel_y, rel_z = map(float, obs[agent, 8:11])
        if abs(rel_x) + abs(rel_y) + abs(rel_z) < 1e-8:
            continue
        heading = math.atan2(float(obs[agent, 4]), float(obs[agent, 5]))
        desired_heading = math.atan2(rel_y, rel_x)
        turn[agent] = angle_diff(desired_heading, heading) / max_turn[agent]
        gamma = math.atan2(float(obs[agent, 6]), float(obs[agent, 7]))
        desired_gamma = math.atan2(rel_z, math.hypot(rel_x, rel_y) + 1e-6)
        climb[agent] = (desired_gamma - gamma) / max_climb[agent]
    return nearest_actions(turn, climb)


def run_episode(seed: int, episode: int) -> dict[str, object]:
    env = UAVIntercept3DEnv(
        UAVIntercept3DConfig(
            seed=seed * 10_000 + episode,
            target_policy="straight",
            strict_target_sensing=False,
            agent_target_info_bottleneck=False,
            relay_dependent_task=False,
            communication_dropout_prob=0.10,
            radar_dropout_prob=0.05,
            message_delay_steps=2,
            max_steps=260,
        )
    )
    obs, _, _ = env.reset()
    reward_sum = 0.0
    while True:
        obs, _, _, rewards, dones, info = env.step(legal_actions(obs))
        reward_sum += float(np.mean(rewards))
        if bool(np.all(dones)):
            return {
                "seed": seed,
                "episode": episode,
                "success": int(info["success"]),
                "timeout": int(info["timeout"]),
                "collision": int(info["collision"]),
                "constraint_violation": int(info["constraint_violation"]),
                "steps": int(info["step"]),
                "tracking_rate": float(info["tracking_rate"]),
                "attack_window_rate": float(info["attack_window_rate"]),
                "reward_sum": reward_sum,
            }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=OUT)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("This read-only development audit requires --execute.")
    raw = args.out_dir / "raw_episode_metrics.csv"
    if raw.exists():
        raise FileExistsError(f"Refusing to overwrite {raw}")

    rows = [run_episode(seed, episode) for seed in SEEDS for episode in range(EPISODES)]
    args.out_dir.mkdir(parents=True, exist_ok=True)
    with raw.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    by_seed = []
    for seed in SEEDS:
        cell = [row for row in rows if row["seed"] == seed]
        by_seed.append({
            "seed": seed,
            "episodes": len(cell),
            "success_rate": float(np.mean([row["success"] for row in cell])),
            "timeout_rate": float(np.mean([row["timeout"] for row in cell])),
            "mean_reward": float(np.mean([row["reward_sum"] for row in cell])),
        })
    with (args.out_dir / "seed_summary.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(by_seed[0]))
        writer.writeheader()
        writer.writerows(by_seed)
    payload = {
        "protocol": "INTERCEPT-3D-LEGAL-BASELINE-G0-V1",
        "artifact_class": "DEVELOPMENT_ONLY_LEGAL_CONTROLLER_FEASIBILITY",
        "seeds": list(SEEDS),
        "episodes_per_seed": EPISODES,
        "controller_information": "local emitted observation only; no environment state",
        "training_started": False,
        "canonical_data_used": False,
        "success_rate": float(np.mean([row["success"] for row in rows])),
        "verdict": "PASS" if all(row["success_rate"] >= 0.50 for row in by_seed) else "INFEASIBLE",
    }
    (args.out_dir / "manifest.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
