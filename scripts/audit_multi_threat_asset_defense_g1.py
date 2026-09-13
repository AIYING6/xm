"""G1 zero-training audit for the 3v2 multi-threat asset-defense task."""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from envs.multi_threat_asset_defense_env import MultiThreatAssetDefenseConfig, MultiThreatAssetDefenseEnv


POLICIES = ("lower_first", "upper_first", "sequential_nearest")
CONTEXTS = {
    "C0_symmetric": {},
    "C1_lower_approach": {"red_center_y": -3_000.0},
    "C2_upper_mirror": {"red_center_y": 3_000.0, "mirror_y": True},
    "C3_wide_assets": {"asset_lateral": 9_000.0},
}


def waypoint_action(env: MultiThreatAssetDefenseEnv, agent: int, goal: np.ndarray) -> int:
    delta = goal - env.base.blue_pos[agent]
    desired = math.atan2(float(delta[1]), float(delta[0]))
    error = math.atan2(math.sin(desired - float(env.base.blue_heading[agent])), math.cos(desired - float(env.base.blue_heading[agent])))
    turn = int(np.sign(error)) if abs(error) > 0.035 else 0
    climb = int(np.sign(float(delta[2]))) if abs(float(delta[2])) > 250.0 else 0
    return int((turn + 1) * 9 + (climb + 1) * 3 + 2)


def choose_threat(env: MultiThreatAssetDefenseEnv, policy: str) -> int:
    alive = [idx for idx in range(2) if not env.blue_destroyed[idx]]
    if not alive:
        return 0
    if policy == "lower_first":
        return min(alive, key=lambda idx: float(env.red_pos[idx, 1]))
    if policy == "upper_first":
        return max(alive, key=lambda idx: float(env.red_pos[idx, 1]))
    attacker = 2
    return min(alive, key=lambda idx: float(np.linalg.norm(env.red_pos[idx] - env.base.blue_pos[attacker])))


def run_one(seed: int, context: str, policy: str) -> dict[str, object]:
    env = MultiThreatAssetDefenseEnv(MultiThreatAssetDefenseConfig(seed=seed, **CONTEXTS[context]))
    env.reset()
    total_return = 0.0
    info: dict[str, float] = {}
    for _ in range(env.config.horizon):
        threat = choose_threat(env, policy)
        target = env.red_pos[threat]
        actions = np.asarray([waypoint_action(env, agent, target) for agent in range(env.num_agents)], dtype=np.int64)
        _, _, _, rewards, dones, info = env.step(actions)
        total_return += float(np.mean(rewards))
        if bool(dones[0, 0]):
            break
    return {"seed": seed, "context": context, "policy": policy, "return": total_return, "steps": env.base.step_count, "defense_success": int(info.get("defense_success", 0.0) > 0.5), "asset_breach": int(info.get("asset_breach", 0.0) > 0.5), "timeout": int(info.get("timeout", 0.0) > 0.5), "neutralized_threats": int(info.get("neutralized_threats", 0.0))}


def main() -> None:
    p = argparse.ArgumentParser(); p.add_argument("--output-root", type=Path, required=True); p.add_argument("--seeds", type=int, default=12); p.add_argument("--seed-start", type=int, default=98101); p.add_argument("--execute", action="store_true")
    a = p.parse_args()
    if not a.execute: raise SystemExit("pass --execute")
    if a.output_root.exists(): raise FileExistsError(f"refusing to overwrite {a.output_root}")
    a.output_root.mkdir(parents=True)
    rows = [run_one(a.seed_start + i, ctx, policy) for i in range(a.seeds) for ctx in CONTEXTS for policy in POLICIES]
    with (a.output_root / "MULTI_THREAT_DEFENSE_G1_ROWS.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    # Terminal mission outcome outranks shaped return.
    rank = lambda row: (int(row["defense_success"]), -int(row["asset_breach"]), int(row["neutralized_threats"]), float(row["return"]))
    winners: dict[tuple[int, str], list[str]] = {}
    for seed in range(a.seed_start, a.seed_start + a.seeds):
        for ctx in CONTEXTS:
            cell = [row for row in rows if row["seed"] == seed and row["context"] == ctx]
            best = max(rank(row) for row in cell)
            winners[(seed, ctx)] = [str(row["policy"]) for row in cell if rank(row) == best]
    unique = {policy: sum(winners[key] == [policy] for key in winners) for policy in POLICIES}
    successes, breaches = sum(int(row["defense_success"]) for row in rows), sum(int(row["asset_breach"]) for row in rows)
    verdict = "MULTI_THREAT_DEFENSE_G1_NONDEGENERATE_SIGNAL" if sum(x > 0 for x in unique.values()) >= 2 and max(unique.values()) < len(winners) and 0 < successes < len(rows) and 0 < breaches < len(rows) else "MULTI_THREAT_DEFENSE_G1_SIGNAL_NOT_ESTABLISHED"
    report = {"protocol": "MULTI-THREAT-ASSET-DEFENSE-G1-V1", "verdict": verdict, "diagnostic_only": True, "training_started": False, "contexts": list(CONTEXTS), "unique_terminal_objective_win_counts": unique, "defense_success_rows": successes, "asset_breach_rows": breaches, "interpretation": "This assesses only physical task identifiability and the single-attacker-capacity feasibility assumption; it is not a learned-policy result."}
    (a.output_root / "MULTI_THREAT_DEFENSE_G1_REPORT.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__": main()
