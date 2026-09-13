"""Scenario-distribution calibration for the three pre-registered v2 boundaries."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.calibrate_multi_threat_dual_capability_phase_map import POLICIES, run

CELLS = (
    {"branch_step": 10, "red_initial_lateral": 9500.0, "asset_lateral": 15000.0},
    {"branch_step": 12, "red_initial_lateral": 8500.0, "asset_lateral": 13500.0},
    {"branch_step": 12, "red_initial_lateral": 8500.0, "asset_lateral": 15000.0},
)
JITTER = {"red_center_y_jitter": 1000.0, "approach_speed_jitter": 12.0, "branch_step_jitter": 2}


def main() -> None:
    p=argparse.ArgumentParser(); p.add_argument("--output-root",type=Path,required=True); p.add_argument("--seed-start",type=int,default=99401); p.add_argument("--seeds",type=int,default=6); p.add_argument("--execute",action="store_true")
    a=p.parse_args()
    if not a.execute: raise SystemExit("pass --execute")
    if a.seeds != 6: raise SystemExit("scenario-v4 is frozen to 6 independent scenarios")
    if a.output_root.exists(): raise FileExistsError(f"refusing to overwrite {a.output_root}")
    a.output_root.mkdir(parents=True)
    rows=[]
    for cell_id, cell in enumerate(CELLS):
        params={**cell,**JITTER}
        for offset in range(a.seeds):
            for policy in POLICIES:
                rows.append({"cell":cell_id,**run(a.seed_start+offset,params,policy)})
    with (a.output_root/"SCENARIO_V4_ROWS.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    summary=[]
    for cell_id, cell in enumerate(CELLS):
        subset=[r for r in rows if r["cell"]==cell_id]
        rate={policy:sum(r["defense_success"] for r in subset if r["policy"]==policy)/6 for policy in POLICIES}
        candidate=2/6 <= rate["parallel_suppress_intercept"] <= 5/6 and rate["parallel_suppress_intercept"] >= rate["kinetic_first"]+2/6
        summary.append({"cell":cell_id,**cell,**JITTER,**{f"success_{p}":rate[p] for p in POLICIES},"candidate":candidate})
    report={"protocol":"MULTI-THREAT-DUAL-CAPABILITY-SCENARIO-V4","diagnostic_only":True,"training_started":False,"candidate_cells":[x for x in summary if x["candidate"]],"interpretation":"A candidate is a physical task-distribution candidate only; an independent G1 and plain-MAPPO G2 remain mandatory."}
    (a.output_root/"SCENARIO_V4_SUMMARY.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    (a.output_root/"SCENARIO_V4_REPORT.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps(report,indent=2))
if __name__=="__main__": main()
