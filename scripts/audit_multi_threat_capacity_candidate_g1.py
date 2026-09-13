"""Independent G1 replication for the selected capacity-defense region."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from envs.multi_threat_capacity_defense_env import MultiThreatCapacityDefenseConfig, MultiThreatCapacityDefenseEnv
from scripts.audit_multi_threat_capacity_defense_g1 import POLICIES, actions_for

PARAMETERS = {"red_start_x": 14000.0, "suppression_range": 12000.0, "branch_step": 12, "red_initial_lateral": 8500.0, "asset_lateral": 15000.0, "red_center_y_jitter": 750.0, "approach_speed_jitter": 8.0, "branch_step_jitter": 1}


def run(seed: int, policy: str) -> dict[str, object]:
    env = MultiThreatCapacityDefenseEnv(MultiThreatCapacityDefenseConfig(seed=seed, **PARAMETERS))
    env.reset(); total = 0.0; info: dict[str, float] = {}
    for _ in range(env.config.horizon):
        _, _, _, reward, done, info = env.step(actions_for(env, policy))
        total += float(reward.mean())
        if bool(done[0, 0]): break
    return {"seed":seed, "policy":policy, "return":total, "steps":env.base.step_count, "defense_success":int(info.get("defense_success", 0.0)>0.5), "asset_breach":int(info.get("asset_breach", 0.0)>0.5), "neutralized_threats":int(info.get("neutralized_threats", 0.0))}


def main() -> None:
    p=argparse.ArgumentParser(); p.add_argument("--output-root",type=Path,required=True); p.add_argument("--seed-start",type=int,default=99901); p.add_argument("--seeds",type=int,default=12); p.add_argument("--execute",action="store_true")
    a=p.parse_args()
    if not a.execute: raise SystemExit("pass --execute")
    if a.seeds != 12: raise SystemExit("candidate G1 is frozen to twelve scenarios")
    if a.output_root.exists(): raise FileExistsError(f"refusing to overwrite {a.output_root}")
    a.output_root.mkdir(parents=True)
    rows=[run(a.seed_start+offset, policy) for offset in range(a.seeds) for policy in POLICIES]
    with (a.output_root/"MULTI_THREAT_CAPACITY_CANDIDATE_G1_ROWS.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    success={policy:sum(int(row["defense_success"]) for row in rows if row["policy"]==policy) for policy in POLICIES}
    parallel=success["parallel_suppress_intercept"]; margin=parallel-success["kinetic_first"]
    verdict="MULTI_THREAT_CAPACITY_G1_REPLICATION_PASS" if 4 <= parallel <= 10 and margin >= 4 else "MULTI_THREAT_CAPACITY_G1_REPLICATION_FAIL"
    report={"protocol":"MULTI-THREAT-CAPACITY-DEFENSE-CANDIDATE-G1-V1", "verdict":verdict, "diagnostic_only":True, "training_started":False, "parameters":PARAMETERS, "defense_success_by_controller":success, "parallel_minus_kinetic_success":margin, "interpretation":"An independent transparent-controller replication validates the selected physical region before any learner is run."}
    (a.output_root/"MULTI_THREAT_CAPACITY_CANDIDATE_G1_REPORT.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps(report,indent=2))


if __name__=="__main__": main()
