"""Zero-training G1 audit for the capacity-limited defense task."""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from envs.multi_threat_capacity_defense_env import MultiThreatCapacityDefenseConfig, MultiThreatCapacityDefenseEnv

POLICIES = ("kinetic_first", "parallel_suppress_intercept", "cofocused_error")
CELLS = (
    {"branch_step": 10, "red_initial_lateral": 9500.0, "asset_lateral": 15000.0},
    {"branch_step": 12, "red_initial_lateral": 8500.0, "asset_lateral": 13500.0},
    {"branch_step": 12, "red_initial_lateral": 8500.0, "asset_lateral": 15000.0},
)
JITTER = {"red_center_y_jitter": 1000.0, "approach_speed_jitter": 12.0, "branch_step_jitter": 2}


def action(env: MultiThreatCapacityDefenseEnv, agent: int, goal: np.ndarray) -> int:
    delta = goal - env.base.blue_pos[agent]
    desired = math.atan2(float(delta[1]), float(delta[0]))
    err = math.atan2(math.sin(desired - float(env.base.blue_heading[agent])), math.cos(desired - float(env.base.blue_heading[agent])))
    turn = int(np.sign(err)) if abs(err) > 0.035 else 0
    climb = int(np.sign(float(delta[2]))) if abs(float(delta[2])) > 250.0 else 0
    return int((turn + 1) * 9 + (climb + 1) * 3 + 2)


def actions_for(env: MultiThreatCapacityDefenseEnv, policy: str) -> np.ndarray:
    alive = [t for t in range(2) if not env.blue_destroyed[t]]
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
    return np.asarray([action(env, i, np.asarray(goal, dtype=np.float32)) for i, goal in enumerate(goals)], dtype=np.int64)


def run_one(seed: int, cell: int, policy: str) -> dict[str, object]:
    env = MultiThreatCapacityDefenseEnv(MultiThreatCapacityDefenseConfig(seed=seed, **CELLS[cell], **JITTER))
    env.reset(); total = 0.0; info: dict[str, float] = {}
    for _ in range(env.config.horizon):
        _, _, _, reward, done, info = env.step(actions_for(env, policy))
        total += float(np.mean(reward))
        if bool(done[0, 0]):
            break
    return {"seed": seed, "cell": cell, "policy": policy, "return": total, "steps": env.base.step_count, "defense_success": int(info.get("defense_success", 0.0) > 0.5), "asset_breach": int(info.get("asset_breach", 0.0) > 0.5), "timeout": int(info.get("timeout", 0.0) > 0.5), "neutralized_threats": int(info.get("neutralized_threats", 0.0)), "kinetic_remaining": int(info.get("kinetic_engagements_remaining", 0.0))}


def main() -> None:
    p = argparse.ArgumentParser(); p.add_argument("--output-root", type=Path, required=True); p.add_argument("--seed-start", type=int, default=99701); p.add_argument("--seeds", type=int, default=12); p.add_argument("--execute", action="store_true")
    a = p.parse_args()
    if not a.execute: raise SystemExit("pass --execute")
    if a.seeds != 12: raise SystemExit("G1 is frozen to 12 scenarios per cell")
    if a.output_root.exists(): raise FileExistsError(f"refusing to overwrite {a.output_root}")
    a.output_root.mkdir(parents=True)
    rows = [run_one(a.seed_start + off, cell, policy) for cell in range(len(CELLS)) for off in range(a.seeds) for policy in POLICIES]
    with (a.output_root / "MULTI_THREAT_CAPACITY_G1_ROWS.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    success = {p: sum(int(r["defense_success"]) for r in rows if r["policy"] == p) for p in POLICIES}
    total = len(CELLS) * a.seeds
    margin = success["parallel_suppress_intercept"] - success["kinetic_first"]
    non_saturated = 0 < success["parallel_suppress_intercept"] < total
    verdict = "MULTI_THREAT_CAPACITY_G1_LEARNABILITY_CANDIDATE" if non_saturated and margin >= 3 else "MULTI_THREAT_CAPACITY_G1_SIGNAL_NOT_ESTABLISHED"
    report = {"protocol": "MULTI-THREAT-CAPACITY-DEFENSE-G1-V1", "verdict": verdict, "diagnostic_only": True, "training_started": False, "scenarios_per_policy": total, "defense_success_by_controller": success, "parallel_minus_kinetic_success": margin, "interpretation": "This audit tests whether a single kinetic engagement and a single continuous disruption channel make complementary allocation materially better than concentrated pursuit. It is not a learned-policy result."}
    (a.output_root / "MULTI_THREAT_CAPACITY_G1_REPORT.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__": main()
