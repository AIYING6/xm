"""Independent G1 audit for the selected non-saturated capacity-defense task."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from envs.multi_threat_capacity_defense_env import MultiThreatCapacityDefenseConfig, MultiThreatCapacityDefenseEnv
from scripts.audit_multi_threat_capacity_defense_g1 import POLICIES, actions_for

PARAMETERS={"red_start_x":14000.0,"suppression_range":12000.0,"branch_step":12,"red_initial_lateral":8500.0,"asset_lateral":15000.0,"red_center_y_jitter":1500.0,"approach_speed_jitter":16.0,"branch_step_jitter":3}


def run(seed:int,policy:str)->dict[str,object]:
    env=MultiThreatCapacityDefenseEnv(MultiThreatCapacityDefenseConfig(seed=seed,**PARAMETERS));env.reset();total=0.0;info={}
    for _ in range(env.config.horizon):
        _,_,_,reward,done,info=env.step(actions_for(env,policy));total+=float(reward.mean())
        if bool(done[0,0]):break
    return {"seed":seed,"policy":policy,"defense_success":int(info.get("defense_success",0.0)>0.5),"asset_breach":int(info.get("asset_breach",0.0)>0.5),"neutralized_threats":int(info.get("neutralized_threats",0.0)),"return":total}


def main()->None:
    p=argparse.ArgumentParser();p.add_argument("--output-root",type=Path,required=True);p.add_argument("--seed-start",type=int,default=101001);p.add_argument("--seeds",type=int,default=24);p.add_argument("--execute",action="store_true");a=p.parse_args()
    if not a.execute:raise SystemExit("pass --execute")
    if a.seeds!=24:raise SystemExit("formal candidate G1 is frozen to 24 independent scenarios")
    if a.output_root.exists():raise FileExistsError(f"refusing to overwrite {a.output_root}")
    a.output_root.mkdir(parents=True);rows=[run(a.seed_start+offset,policy) for offset in range(a.seeds) for policy in POLICIES]
    with (a.output_root/"MULTI_THREAT_CAPACITY_FORMAL_G1_ROWS.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    success={policy:sum(int(r["defense_success"]) for r in rows if r["policy"]==policy) for policy in POLICIES};parallel=success["parallel_suppress_intercept"];margin=parallel-success["kinetic_first"]
    verdict="MULTI_THREAT_CAPACITY_FORMAL_G1_PASS" if 8<=parallel<=20 and margin>=8 else "MULTI_THREAT_CAPACITY_FORMAL_G1_FAIL"
    report={"protocol":"MULTI-THREAT-CAPACITY-DEFENSE-FORMAL-CANDIDATE-G1-V1","verdict":verdict,"diagnostic_only":True,"training_started":False,"parameters":PARAMETERS,"defense_success_by_controller":success,"parallel_minus_kinetic_success":margin,"interpretation":"This independent controller audit verifies that the frozen scenario distribution is feasible, non-saturated, and decision-sensitive before learner training."}
    (a.output_root/"MULTI_THREAT_CAPACITY_FORMAL_G1_REPORT.json").write_text(json.dumps(report,indent=2),encoding="utf-8");print(json.dumps(report,indent=2))


if __name__=="__main__":main()
