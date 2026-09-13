"""Bounded feasibility calibration for capacity-limited multi-threat defense.

This is not a method search.  It maps only geometry and sensor-range values
already present in the physical contract, before a single learner is run.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.audit_multi_threat_capacity_defense_g1 import POLICIES, actions_for
from envs.multi_threat_capacity_defense_env import MultiThreatCapacityDefenseConfig, MultiThreatCapacityDefenseEnv

GRID = tuple(
    {"red_start_x": red_start_x, "suppression_range": suppression_range}
    for red_start_x in (11_000.0, 14_000.0, 17_000.0, 20_000.0)
    for suppression_range in (8_000.0, 10_000.0, 12_000.0)
)
JITTER = {"red_center_y_jitter": 750.0, "approach_speed_jitter": 8.0, "branch_step_jitter": 1}
BASE = {"branch_step": 12, "red_initial_lateral": 8500.0, "asset_lateral": 15000.0}


def run(seed: int, parameters: dict[str, float], policy: str) -> dict[str, object]:
    env = MultiThreatCapacityDefenseEnv(MultiThreatCapacityDefenseConfig(seed=seed, **BASE, **JITTER, **parameters))
    env.reset(); total = 0.0; info: dict[str, float] = {}
    for _ in range(env.config.horizon):
        _, _, _, reward, done, info = env.step(actions_for(env, policy))
        total += float(reward.mean())
        if bool(done[0, 0]): break
    return {"seed": seed, "policy": policy, "return": total, "steps": env.base.step_count, "defense_success": int(info.get("defense_success", 0.0) > 0.5), "asset_breach": int(info.get("asset_breach", 0.0) > 0.5), "neutralized_threats": int(info.get("neutralized_threats", 0.0))}


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--output-root", type=Path, required=True); parser.add_argument("--seed-start", type=int, default=99801); parser.add_argument("--seeds", type=int, default=6); parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute: raise SystemExit("pass --execute")
    if args.seeds != 6: raise SystemExit("calibration is frozen to six scenarios per cell")
    if args.output_root.exists(): raise FileExistsError(f"refusing to overwrite {args.output_root}")
    args.output_root.mkdir(parents=True)
    rows=[]
    for cell, parameters in enumerate(GRID):
        for offset in range(args.seeds):
            for policy in POLICIES:
                rows.append({"cell": cell, **parameters, **run(args.seed_start + offset, parameters, policy)})
    with (args.output_root / "MULTI_THREAT_CAPACITY_PHASE_MAP_ROWS.csv").open("w", newline="", encoding="utf-8") as handle:
        writer=csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    summary=[]
    for cell, parameters in enumerate(GRID):
        subset=[row for row in rows if row["cell"] == cell]
        rates={policy: sum(int(row["defense_success"]) for row in subset if row["policy"] == policy) / args.seeds for policy in POLICIES}
        candidate = 2/6 <= rates["parallel_suppress_intercept"] <= 5/6 and rates["parallel_suppress_intercept"] >= rates["kinetic_first"] + 2/6
        summary.append({"cell":cell, **parameters, **{f"success_{p}": rates[p] for p in POLICIES}, "candidate":candidate})
    report={"protocol":"MULTI-THREAT-CAPACITY-PHASE-MAP-V1", "diagnostic_only":True, "training_started":False, "base":BASE, "jitter":JITTER, "candidate_cells":[item for item in summary if item["candidate"]], "selection_rule":"Parallel allocation must succeed in 2-5 of six scenarios and exceed kinetic-first by at least two successes. This selects a feasible, non-saturated task region only; G1 replication and plain-MAPPO learning remain required."}
    (args.output_root / "MULTI_THREAT_CAPACITY_PHASE_MAP_SUMMARY.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (args.output_root / "MULTI_THREAT_CAPACITY_PHASE_MAP_REPORT.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__": main()
