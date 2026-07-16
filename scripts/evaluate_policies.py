from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from baselines import greedy_intercept_policy
from envs import UAVPursuitConfig, UAVPursuitEnv


def random_policy(env: UAVPursuitEnv) -> np.ndarray:
    return env.rng.integers(0, env.action_dim, size=env.config.num_pursuers, dtype=np.int64)


def run_episode(policy_name: str, seed: int, target_policy: str, target_speed: float) -> dict:
    env = UAVPursuitEnv(UAVPursuitConfig(seed=seed, target_policy=target_policy, target_speed=target_speed))
    env.reset()
    info = {}
    while True:
        if policy_name == "rule":
            actions = greedy_intercept_policy(env)
        elif policy_name == "random":
            actions = random_policy(env)
        else:
            raise ValueError(f"Unknown policy: {policy_name}")
        _, _, _, _, dones, info = env.step(actions)
        if np.all(dones):
            break
    return info


def evaluate(policy_name: str, episodes: int, target_policy: str, target_speed: float) -> dict:
    records = [run_episode(policy_name, seed, target_policy, target_speed) for seed in range(episodes)]
    return {
        "policy": policy_name,
        "target_policy": target_policy,
        "target_speed": target_speed,
        "episodes": episodes,
        "success_rate": float(np.mean([r["success"] for r in records])),
        "collision_rate": float(np.mean([r["collision"] for r in records])),
        "timeout_rate": float(np.mean([r["timeout"] for r in records])),
        "avg_steps": float(np.mean([r["step"] for r in records])),
        "avg_mean_distance": float(np.mean([r["mean_distance"] for r in records])),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--episodes", type=int, default=50)
    parser.add_argument("--target-policy", type=str, default="mixed")
    parser.add_argument("--target-speed", type=float, default=0.75)
    args = parser.parse_args()

    for policy_name in ["random", "rule"]:
        print(evaluate(policy_name, args.episodes, args.target_policy, args.target_speed))


if __name__ == "__main__":
    main()
