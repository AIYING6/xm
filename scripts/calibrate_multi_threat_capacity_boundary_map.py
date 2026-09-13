"""One bounded threshold calibration between the established 10 and 12 km regimes."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.audit_multi_threat_capacity_candidate_g1 import POLICIES
from envs.multi_threat_capacity_defense_env import MultiThreatCapacityDefenseConfig, MultiThreatCapacityDefenseEnv
from scripts.audit_multi_threat_capacity_defense_g1 import actions_for

GRID=tuple({"red_start_x":x,"suppression_range":r} for x in (13500.0,14000.0) for r in (10500.0,11000.0,11500.0))


def main() -> None:
    p=argparse.ArgumentParser(); p.add_argument("--output-root",type=Path,required=True); p.add_argument("--seed-start",type=int,default=99951); p.add_argument("--seeds",type=int,default=12); p.add_argument("--execute",action="store_true")
    a=p.parse_args()
    if not a.execute: raise SystemExit("pass --execute")
    if a.seeds != 12: raise SystemExit("boundary map is frozen to twelve scenarios per cell")
    if a.output_root.exists(): raise FileExistsError(f"refusing to overwrite {a.output_root}")
    a.output_root.mkdir(parents=True)
    rows=[]
    for cell, parameters in enumerate(GRID):
        for offset in range(a.seeds):
            for policy in POLICIES:
                env=MultiThreatCapacityDefenseEnv(MultiThreatCapacityDefenseConfig(seed=a.seed_start+offset, branch_step=12, red_initial_lateral=8500.0, asset_lateral=15000.0, red_center_y_jitter=750.0, approach_speed_jitter=8.0, branch_step_jitter=1, **parameters))
                env.reset(); total=0.0; info={}
                for _ in range(env.config.horizon):
                    _,_,_,reward,done,info=env.step(actions_for(env,policy)); total+=float(reward.mean())
                    if bool(done[0,0]): break
                rows.append({"cell":cell,**parameters,"seed":a.seed_start+offset,"policy":policy,"defense_success":int(info.get("defense_success",0.0)>0.5),"asset_breach":int(info.get("asset_breach",0.0)>0.5),"return":total})
    with (a.output_root/"MULTI_THREAT_CAPACITY_BOUNDARY_ROWS.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    summary=[]
    for cell, parameters in enumerate(GRID):
        subset=[row for row in rows if row["cell"]==cell]
        wins={policy:sum(int(row["defense_success"]) for row in subset if row["policy"]==policy) for policy in POLICIES}
        parallel=wins["parallel_suppress_intercept"]; candidate=4<=parallel<=10 and parallel-wins["kinetic_first"]>=4
        summary.append({"cell":cell,**parameters,**{f"success_{k}":v for k,v in wins.items()},"candidate":candidate})
    report={"protocol":"MULTI-THREAT-CAPACITY-DEFENSE-BOUNDARY-MAP-V1","diagnostic_only":True,"training_started":False,"candidate_cells":[x for x in summary if x["candidate"]]}
    (a.output_root/"MULTI_THREAT_CAPACITY_BOUNDARY_SUMMARY.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    (a.output_root/"MULTI_THREAT_CAPACITY_BOUNDARY_REPORT.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps(report,indent=2))


if __name__=="__main__": main()
