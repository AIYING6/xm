"""G1 zero-training audit for dual-capability multi-threat defense."""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from envs.multi_threat_dual_capability_defense_env import MultiThreatDualCapabilityDefenseConfig, MultiThreatDualCapabilityDefenseEnv

POLICIES = ("kinetic_first", "parallel_suppress_intercept", "cofocused_error")
CONTEXTS = {
    "C0_symmetric": {},
    "C1_lower_shift": {"red_center_y": -2800.0},
    "C2_upper_mirror": {"red_center_y": 2800.0, "mirror_y": True},
    "C3_wide_assets": {"asset_lateral": 9000.0},
}


def action(env: MultiThreatDualCapabilityDefenseEnv, agent: int, goal: np.ndarray) -> int:
    delta = goal - env.base.blue_pos[agent]
    desired = math.atan2(float(delta[1]), float(delta[0]))
    err = math.atan2(math.sin(desired - float(env.base.blue_heading[agent])), math.cos(desired - float(env.base.blue_heading[agent])))
    turn = int(np.sign(err)) if abs(err) > 0.035 else 0
    climb = int(np.sign(float(delta[2]))) if abs(float(delta[2])) > 250.0 else 0
    return int((turn + 1) * 9 + (climb + 1) * 3 + 2)


def actions_for(env: MultiThreatDualCapabilityDefenseEnv, policy: str) -> np.ndarray:
    alive = [t for t in range(2) if not env.blue_destroyed[t]]
    primary = alive[0] if alive else 0
    secondary = alive[1] if len(alive) > 1 else primary
    if policy == "kinetic_first":
        goals = (env.red_pos[primary],) * 3
    elif policy == "parallel_suppress_intercept":
        # Scout establishes a focused physical disruption beam on the second
        # threat; relay holds the geometric midpoint needed for communication;
        # attacker forms an intercept window on the first threat.
        relay_goal = 0.5 * (env.base.blue_pos[env.scout] + env.base.blue_pos[env.attacker])
        goals = (env.red_pos[secondary], relay_goal, env.red_pos[primary])
    elif policy == "cofocused_error":
        goals = (env.red_pos[primary], env.red_pos[primary], env.red_pos[primary])
    else:
        raise ValueError(policy)
    return np.asarray([action(env, i, np.asarray(goal, dtype=np.float32)) for i, goal in enumerate(goals)], dtype=np.int64)


def run_one(seed: int, context: str, policy: str) -> dict[str, object]:
    env = MultiThreatDualCapabilityDefenseEnv(MultiThreatDualCapabilityDefenseConfig(seed=seed, **CONTEXTS[context]))
    env.reset(); total = 0.0; info: dict[str, float] = {}
    for _ in range(env.config.horizon):
        _, _, _, reward, done, info = env.step(actions_for(env, policy))
        total += float(np.mean(reward))
        if bool(done[0, 0]): break
    return {"seed": seed, "context": context, "policy": policy, "return": total, "steps": env.base.step_count, "defense_success": int(info.get("defense_success", 0.0) > 0.5), "asset_breach": int(info.get("asset_breach", 0.0) > 0.5), "timeout": int(info.get("timeout", 0.0) > 0.5), "neutralized_threats": int(info.get("neutralized_threats", 0.0))}


def main() -> None:
    p = argparse.ArgumentParser(); p.add_argument("--output-root", type=Path, required=True); p.add_argument("--seed-start", type=int, default=99101); p.add_argument("--seeds", type=int, default=12); p.add_argument("--execute", action="store_true")
    a = p.parse_args()
    if not a.execute: raise SystemExit("pass --execute")
    if a.output_root.exists(): raise FileExistsError(f"refusing to overwrite {a.output_root}")
    a.output_root.mkdir(parents=True)
    rows = [run_one(a.seed_start+i, ctx, policy) for i in range(a.seeds) for ctx in CONTEXTS for policy in POLICIES]
    with (a.output_root / "MULTI_THREAT_DUAL_CAPABILITY_G1_ROWS.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    rank = lambda r: (int(r["defense_success"]), -int(r["asset_breach"]), int(r["neutralized_threats"]), float(r["return"]))
    winners: dict[tuple[int, str], list[str]] = {}
    for seed in range(a.seed_start, a.seed_start+a.seeds):
        for ctx in CONTEXTS:
            cell = [r for r in rows if r["seed"] == seed and r["context"] == ctx]; best = max(rank(r) for r in cell)
            winners[(seed, ctx)] = [str(r["policy"]) for r in cell if rank(r) == best]
    unique = {policy: sum(winners[key] == [policy] for key in winners) for policy in POLICIES}
    success, breach = sum(int(r["defense_success"]) for r in rows), sum(int(r["asset_breach"]) for r in rows)
    verdict = "MULTI_THREAT_DUAL_CAPABILITY_G1_NONDEGENERATE_SIGNAL" if unique["parallel_suppress_intercept"] > 0 and sum(x > 0 for x in unique.values()) >= 2 and max(unique.values()) < len(winners) and 0 < success < len(rows) and 0 < breach < len(rows) else "MULTI_THREAT_DUAL_CAPABILITY_G1_SIGNAL_NOT_ESTABLISHED"
    report = {"protocol": "MULTI-THREAT-DUAL-CAPABILITY-G1-V1", "verdict": verdict, "diagnostic_only": True, "training_started": False, "contexts": list(CONTEXTS), "unique_terminal_objective_win_counts": unique, "defense_success_rows": success, "asset_breach_rows": breach, "interpretation": "Transparent controllers test whether constrained suppression and interception create physical task trade-offs; they are not learned-policy or paper performance results."}
    (a.output_root / "MULTI_THREAT_DUAL_CAPABILITY_G1_REPORT.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))

if __name__ == "__main__": main()
