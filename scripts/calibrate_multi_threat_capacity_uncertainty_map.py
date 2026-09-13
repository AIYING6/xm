"""Calibrate natural approach uncertainty at a fixed capacity-defense geometry."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from envs.multi_threat_capacity_defense_env import MultiThreatCapacityDefenseConfig, MultiThreatCapacityDefenseEnv
from scripts.audit_multi_threat_capacity_defense_g1 import POLICIES, actions_for

BASE={"red_start_x":14000.0,"suppression_range":12000.0,"branch_step":12,"red_initial_lateral":8500.0,"asset_lateral":15000.0}
DISTRIBUTIONS=(
    {"red_center_y_jitter":1000.0,"approach_speed_jitter":12.0,"branch_step_jitter":2},
    {"red_center_y_jitter":1250.0,"approach_speed_jitter":12.0,"branch_step_jitter":2},
    {"red_center_y_jitter":1500.0,"approach_speed_jitter":16.0,"branch_step_jitter":3},
)


def run(seed: int, distribution: dict[str, float], policy: str) -> dict[str, object]:
    env=MultiThreatCapacityDefenseEnv(MultiThreatCapacityDefenseConfig(seed=seed,**BASE,**distribution))
    env.reset(); total=0.0; info={}
    for _ in range(env.config.horizon):
        _,_,_,reward,done,info=env.step(actions_for(env,policy)); total+=float(reward.mean())
        if bool(done[0,0]): break
    return {"seed":seed,"policy":policy,"defense_success":int(info.get("defense_success",0.0)>0.5),"asset_breach":int(info.get("asset_breach",0.0)>0.5),"return":total}


def main() -> None:
    p=argparse.ArgumentParser();p.add_argument("--output-root",type=Path,required=True);p.add_argument("--seed-start",type=int,default=100001);p.add_argument("--seeds",type=int,default=12);p.add_argument("--execute",action="store_true")
    a=p.parse_args()
    if not a.execute:raise SystemExit("pass --execute")
    if a.seeds!=12:raise SystemExit("uncertainty map is frozen to twelve scenarios per distribution")
    if a.output_root.exists():raise FileExistsError(f"refusing to overwrite {a.output_root}")
    a.output_root.mkdir(parents=True);rows=[]
    for index,distribution in enumerate(DISTRIBUTIONS):
        for offset in range(a.seeds):
            for policy in POLICIES:rows.append({"distribution":index,**distribution,**run(a.seed_start+offset,distribution,policy)})
    with (a.output_root/"MULTI_THREAT_CAPACITY_UNCERTAINTY_ROWS.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    summary=[]
    for index,distribution in enumerate(DISTRIBUTIONS):
        subset=[x for x in rows if x["distribution"]==index]; success={p:sum(int(x["defense_success"]) for x in subset if x["policy"]==p) for p in POLICIES}; parallel=success["parallel_suppress_intercept"]
        summary.append({"distribution":index,**distribution,**{f"success_{p}":v for p,v in success.items()},"candidate":4<=parallel<=10 and parallel-success["kinetic_first"]>=4})
    report={"protocol":"MULTI-THREAT-CAPACITY-DEFENSE-UNCERTAINTY-MAP-V1","diagnostic_only":True,"training_started":False,"candidate_distributions":[x for x in summary if x["candidate"]]}
    (a.output_root/"MULTI_THREAT_CAPACITY_UNCERTAINTY_SUMMARY.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    (a.output_root/"MULTI_THREAT_CAPACITY_UNCERTAINTY_REPORT.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps(report,indent=2))


if __name__=="__main__":main()
