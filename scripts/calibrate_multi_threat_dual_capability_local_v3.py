"""Pre-registered local phase-map refinement around the v2 boundary."""
from __future__ import annotations

import argparse
import csv
import itertools
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.calibrate_multi_threat_dual_capability_phase_map import POLICIES, run

AXES = {"branch_step": (10, 12, 14), "red_initial_lateral": (7500.0, 8500.0, 9500.0), "asset_lateral": (12000.0, 13500.0, 15000.0)}


def main() -> None:
    p = argparse.ArgumentParser(); p.add_argument("--output-root", type=Path, required=True); p.add_argument("--seed-start", type=int, default=99301); p.add_argument("--seeds", type=int, default=6); p.add_argument("--execute", action="store_true")
    a = p.parse_args()
    if not a.execute: raise SystemExit("pass --execute")
    if a.seeds != 6:
        raise SystemExit("local-v3 is frozen to exactly 6 calibration initialisations")
    if a.output_root.exists(): raise FileExistsError(f"refusing to overwrite {a.output_root}")
    a.output_root.mkdir(parents=True)
    keys, values = tuple(AXES), tuple(AXES.values()); cells = [dict(zip(keys, combo)) for combo in itertools.product(*values)]
    rows = [run(a.seed_start+i, cell, policy) for cell in cells for i in range(a.seeds) for policy in POLICIES]
    with (a.output_root / "LOCAL_V3_ROWS.csv").open("w", newline="", encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    summary=[]
    for cell_id, cell in enumerate(cells):
        subset=[r for r in rows if all(r[k] == v for k,v in cell.items())]
        rates={p:sum(r["defense_success"] for r in subset if r["policy"]==p)/a.seeds for p in POLICIES}
        candidate=2/6 <= rates["parallel_suppress_intercept"] <= 5/6 and rates["parallel_suppress_intercept"] >= rates["kinetic_first"] + 2/6
        summary.append({"cell":cell_id, **cell, **{f"success_{p}":rates[p] for p in POLICIES}, "candidate":candidate})
    (a.output_root / "LOCAL_V3_SUMMARY.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    report={"protocol":"MULTI-THREAT-DUAL-CAPABILITY-CALIBRATION-LOCAL-V3","diagnostic_only":True,"training_started":False,"cell_count":len(cells),"candidate_cells":[x for x in summary if x["candidate"]],"interpretation":"Selected cells are calibration candidates only and require a fresh independent G1 and plain-MAPPO G2."}
    (a.output_root / "LOCAL_V3_REPORT.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps(report,indent=2))

if __name__ == "__main__": main()
