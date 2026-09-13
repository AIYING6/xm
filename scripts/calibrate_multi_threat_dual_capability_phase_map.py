"""Pre-registered zero-training phase map for dual-capability task calibration."""
from __future__ import annotations

import argparse
import csv
import itertools
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from envs.multi_threat_dual_capability_defense_env import MultiThreatDualCapabilityDefenseConfig, MultiThreatDualCapabilityDefenseEnv
from scripts.audit_multi_threat_dual_capability_g1 import actions_for

AXES = {"branch_step": (12, 20, 28), "red_initial_lateral": (2400.0, 5500.0, 8500.0), "asset_lateral": (7500.0, 10500.0, 13500.0)}
POLICIES = ("kinetic_first", "parallel_suppress_intercept", "cofocused_error")


def run(seed: int, parameters: dict[str, float | int], policy: str) -> dict[str, object]:
    env = MultiThreatDualCapabilityDefenseEnv(MultiThreatDualCapabilityDefenseConfig(seed=seed, **parameters))
    env.reset(); info: dict[str, float] = {}
    for _ in range(env.config.horizon):
        _, _, _, _, done, info = env.step(actions_for(env, policy))
        if bool(done[0, 0]): break
    return {**parameters, "seed": seed, "policy": policy, "defense_success": int(info.get("defense_success", 0.0) > 0.5), "asset_breach": int(info.get("asset_breach", 0.0) > 0.5), "neutralized_threats": int(info.get("neutralized_threats", 0.0)), "steps": env.base.step_count}


def main() -> None:
    p = argparse.ArgumentParser(); p.add_argument("--output-root", type=Path, required=True); p.add_argument("--seeds", type=int, default=6); p.add_argument("--seed-start", type=int, default=99201); p.add_argument("--execute", action="store_true")
    a = p.parse_args()
    if not a.execute: raise SystemExit("pass --execute")
    if a.output_root.exists(): raise FileExistsError(f"refusing to overwrite {a.output_root}")
    a.output_root.mkdir(parents=True)
    keys, values = tuple(AXES), tuple(AXES.values())
    cells = [dict(zip(keys, combo)) for combo in itertools.product(*values)]
    rows = [run(a.seed_start + offset, cell, policy) for cell in cells for offset in range(a.seeds) for policy in POLICIES]
    with (a.output_root / "CALIBRATION_PHASE_MAP_ROWS.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    summaries = []
    for index, cell in enumerate(cells):
        subset = [r for r in rows if all(r[k] == v for k, v in cell.items())]
        rates = {policy: sum(r["defense_success"] for r in subset if r["policy"] == policy) / a.seeds for policy in POLICIES}
        # Strictly predeclared screen: task must not saturate, and the intended
        # parallel physical allocation must exceed plain kinetic pursuit by at
        # least two of six matched initialisations.
        selected = 0.15 <= rates["parallel_suppress_intercept"] <= 0.85 and rates["parallel_suppress_intercept"] >= rates["kinetic_first"] + 2.0 / a.seeds
        summaries.append({"cell": index, **cell, **{f"success_{p}": rates[p] for p in POLICIES}, "candidate": selected})
    with (a.output_root / "CALIBRATION_PHASE_MAP_SUMMARY.json").open("w", encoding="utf-8") as f: json.dump(summaries, f, indent=2)
    report = {"protocol": "MULTI-THREAT-DUAL-CAPABILITY-CALIBRATION-V2", "diagnostic_only": True, "training_started": False, "cell_count": len(cells), "candidate_cells": [s for s in summaries if s["candidate"]], "interpretation": "This v2 map varies the two physical lateral separations that govern whether one kinetic UAV can serially service both threats. A candidate still requires independent G1 and plain-MAPPO G2 before method design."}
    (a.output_root / "CALIBRATION_PHASE_MAP_REPORT.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))

if __name__ == "__main__": main()
