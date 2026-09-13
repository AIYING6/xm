"""Zero-training learnability audit for the target-lock multi-threat task."""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from envs.multi_threat_target_lock_defense_env import (
    MultiThreatTargetLockDefenseConfig,
    MultiThreatTargetLockDefenseEnv,
)

POLICIES = ("kinetic_first", "parallel_suppress_intercept", "cofocused_error")
CELLS = (
    {"branch_step": 10, "red_initial_lateral": 9500.0, "asset_lateral": 15000.0},
    {"branch_step": 12, "red_initial_lateral": 8500.0, "asset_lateral": 13500.0},
    {"branch_step": 12, "red_initial_lateral": 8500.0, "asset_lateral": 15000.0},
)
JITTER = {"red_center_y_jitter": 1000.0, "approach_speed_jitter": 12.0, "branch_step_jitter": 2}


def _action(env: MultiThreatTargetLockDefenseEnv, agent: int, goal: np.ndarray) -> int:
    delta = goal - env.base.blue_pos[agent]
    desired = math.atan2(float(delta[1]), float(delta[0]))
    error = math.atan2(math.sin(desired - float(env.base.blue_heading[agent])), math.cos(desired - float(env.base.blue_heading[agent])))
    turn = int(np.sign(error)) if abs(error) > 0.035 else 0
    climb = int(np.sign(float(delta[2]))) if abs(float(delta[2])) > 250.0 else 0
    return int((turn + 1) * 9 + (climb + 1) * 3 + 2)


def _actions_for(env: MultiThreatTargetLockDefenseEnv, policy: str) -> np.ndarray:
    alive = [threat for threat in range(2) if not env.blue_destroyed[threat]]
    primary = alive[0] if alive else 0
    secondary = alive[1] if len(alive) > 1 else primary
    if policy == "kinetic_first":
        goals = (env.red_pos[primary],) * 3
    elif policy == "parallel_suppress_intercept":
        relay_goal = 0.5 * (env.base.blue_pos[env.scout] + env.base.blue_pos[env.attacker])
        goals = (env.red_pos[secondary], relay_goal, env.red_pos[primary])
    elif policy == "cofocused_error":
        goals = (env.red_pos[primary],) * 3
    else:
        raise ValueError(policy)
    return np.asarray([_action(env, agent, np.asarray(goal, dtype=np.float32)) for agent, goal in enumerate(goals)], dtype=np.int64)


def _run(seed: int, cell: int, policy: str) -> dict[str, object]:
    env = MultiThreatTargetLockDefenseEnv(MultiThreatTargetLockDefenseConfig(seed=seed, **CELLS[cell], **JITTER))
    env.reset()
    total_return = 0.0
    info: dict[str, float] = {}
    for _ in range(env.config.horizon):
        _, _, _, reward, done, info = env.step(_actions_for(env, policy))
        total_return += float(np.mean(reward))
        if bool(done[0, 0]):
            break
    return {
        "seed": seed, "cell": cell, "policy": policy, "return": total_return,
        "steps": env.base.step_count, "defense_success": int(info.get("defense_success", 0.0) > 0.5),
        "asset_breach": int(info.get("asset_breach", 0.0) > 0.5),
        "timeout": int(info.get("timeout", 0.0) > 0.5),
        "neutralized_threats": int(info.get("neutralized_threats", 0.0)),
        "max_target_lock": max(env.red_target_lock_hold),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--seed-start", type=int, default=99601)
    parser.add_argument("--seeds", type=int, default=12)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("pass --execute")
    if args.seeds != 12:
        raise SystemExit("G1 is frozen to 12 scenarios per cell")
    if args.output_root.exists():
        raise FileExistsError(f"refusing to overwrite {args.output_root}")
    args.output_root.mkdir(parents=True)
    rows = [_run(args.seed_start + offset, cell, policy) for cell in range(len(CELLS)) for offset in range(args.seeds) for policy in POLICIES]
    with (args.output_root / "MULTI_THREAT_TARGET_LOCK_G1_ROWS.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    wins = {policy: sum(int(row["defense_success"]) for row in rows if row["policy"] == policy) for policy in POLICIES}
    total = len(CELLS) * args.seeds
    parallel_margin = wins["parallel_suppress_intercept"] - wins["kinetic_first"]
    nondegenerate = 0 < wins["parallel_suppress_intercept"] < total and 0 < wins["kinetic_first"] < total
    verdict = "MULTI_THREAT_TARGET_LOCK_G1_LEARNABILITY_CANDIDATE" if nondegenerate and parallel_margin >= 3 else "MULTI_THREAT_TARGET_LOCK_G1_SIGNAL_NOT_ESTABLISHED"
    report = {
        "protocol": "MULTI-THREAT-TARGET-LOCK-DEFENSE-G1-V1", "verdict": verdict,
        "diagnostic_only": True, "training_started": False, "scenarios_per_policy": total,
        "defense_success_by_controller": wins, "parallel_minus_kinetic_success": parallel_margin,
        "interpretation": "The audit asks whether coordinated lock interruption and kinetic interception create a non-saturated, controller-sensitive task distribution. It is not a learned-policy result.",
    }
    (args.output_root / "MULTI_THREAT_TARGET_LOCK_G1_REPORT.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
