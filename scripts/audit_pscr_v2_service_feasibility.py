"""Physical reachability check for PSCR-v2 service chains.

This is not a learning method or a paper result.  It applies a transparent
role-respecting navigation controller to establish whether the current
geometry permits a primary and, after arrival, a future service chain.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from envs.pscr_adversarial_service_env import PSCRConfig, PredictiveServiceChainReconfigurationEnv
from envs.uav_intercept_3d_env import ACTION3D_TABLE


def heading_error(target: np.ndarray, position: np.ndarray, heading: float) -> float:
    desired = math.atan2(float(target[1] - position[1]), float(target[0] - position[0]))
    return (desired - heading + math.pi) % (2.0 * math.pi) - math.pi


def navigation_action(env: PredictiveServiceChainReconfigurationEnv, agent: int, target: np.ndarray) -> int:
    error = heading_error(target, env.base.blue_pos[agent], float(env.base.blue_heading[agent]))
    turn = 1.0 if error > 0.04 else (-1.0 if error < -0.04 else 0.0)
    altitude = float(target[2] - env.base.blue_pos[agent, 2])
    climb = 1.0 if altitude > 250.0 else (-1.0 if altitude < -250.0 else 0.0)
    matches = np.flatnonzero(np.all(np.isclose(ACTION3D_TABLE, np.asarray((turn, climb, 1.0), dtype=np.float32)), axis=1))
    return int(matches[0])


def rollout(seed: int, profile: str, policy: str) -> dict[str, float | int | str]:
    env = PredictiveServiceChainReconfigurationEnv(PSCRConfig(seed=seed, adversary_profile=profile))
    env.reset()
    total = 0.0
    while not env.done:
        target = env.primary_position
        if policy == "switch_at_arrival" and env.future_active and not env.future_completed and not env.future_expired:
            target = env.future_position
        actions = np.asarray([navigation_action(env, agent, target) for agent in range(env.num_agents)], dtype=np.int64)
        _, _, _, rewards, _, _ = env.step(actions)
        total += float(rewards.mean())
    return {"seed": seed, "profile": profile, "policy": policy, "return": total, **env.terminal_summary()}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--episodes", type=int, default=24)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("refusing without --execute")
    if args.output.exists():
        raise FileExistsError(args.output)
    rows = [
        rollout(99000 + index, profile, policy)
        for profile in ("bounded_mixture", "urgent_opposite", "routine_aligned")
        for policy in ("primary_first", "switch_at_arrival")
        for index in range(args.episodes)
    ]
    summary = {}
    for profile in ("bounded_mixture", "urgent_opposite", "routine_aligned"):
        for policy in ("primary_first", "switch_at_arrival"):
            subset = [row for row in rows if row["profile"] == profile and row["policy"] == policy]
            prefix = f"{profile}_{policy}"
            for field in ("primary_completed", "future_completed", "weighted_service_value", "return"):
                summary[f"{prefix}_{field}"] = float(np.mean([float(row[field]) for row in subset]))
    payload = {
        "protocol": "PSCR-V2-SERVICE-FEASIBILITY-V1",
        "diagnostic_only": True,
        "rows": rows,
        "summary": summary,
        "interpretation": "A transparent navigation policy tests physical/service-chain reachability only; it does not establish learnability or a method result.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"summary": summary}, indent=2))


if __name__ == "__main__":
    main()
