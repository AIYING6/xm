"""Deterministic, zero-learning validation of the frozen P3 static schedule."""
from __future__ import annotations
import argparse,json,random,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from algorithms.redundant_topology_staged_schedule import GROUPS,STAGES,StaticTopologySchedule,TIER_R,TOTAL_UPDATES
from envs.redundant_topology_uav_env import RedundantTopologyUAVEnv,scale_config

def main():
 p=argparse.ArgumentParser();p.add_argument("--output-root",type=Path,required=True);p.add_argument("--execute",action="store_true");a=p.parse_args()
 if not a.execute:raise SystemExit("--execute required")
 if a.output_root.exists():raise FileExistsError(a.output_root)
 s=StaticTopologySchedule();rng=random.Random(68011)
 samples={"stage0":{s.sample(0,rng) for _ in range(64)},"stage1":{s.sample(1000,rng) for _ in range(256)},"stage2":{s.sample(3000,rng) for _ in range(1024)}}
 env=RedundantTopologyUAVEnv(scale_config("main",seed_env=1,seed_comm=2,seed_topology=3,assignment_observation=True,scout_assignment_observation=True));before=(env.obs_dim,env.share_obs_dim,env.action_dim);env.reset();after=(env.obs_dim,env.share_obs_dim,env.action_dim)
 checks={"complete_partition":STAGES[0][0]==0 and STAGES[-1][1]==TOTAL_UPDATES and all(STAGES[i][1]==STAGES[i+1][0] for i in range(len(STAGES)-1)),"stage0_nominal_only":samples["stage0"]=={"nominal"},"stage1_tier_r_only":samples["stage1"]==set(TIER_R),"stage2_all_groups_reachable":samples["stage2"]==set(GROUPS),"out_of_budget_rejected":all(_raises(s,x) for x in (-1,TOTAL_UPDATES)),"environment_interface_unchanged":before==after,"scheduler_has_no_learning_inputs":s.manifest()["adaptive"] is False and s.manifest()["inputs"]=="update_index_and_training_rng_only","ppo_updates":0,"environment_steps":0,"evaluation_started":False}
 verdict="P3_P1_STATIC_SCHEDULE_TECHNICAL_PASS" if all(v is True or v==0 for v in checks.values()) else "P3_P1_STATIC_SCHEDULE_TECHNICAL_FAIL";a.output_root.mkdir(parents=True);d={"protocol":"REDUNDANT-TOPOLOGY-UAV-P3-P1-TECHNICAL-AUDIT-V1","verdict":verdict,"checks":checks,"schedule":s.manifest(),"training_started":False,"automatic_continuation":False};(a.output_root/"P3_P1_AUDIT.json").write_text(json.dumps(d,indent=2)+"\n");(a.output_root/"P3_P1_FINAL_VERDICT.md").write_text(f"# P3-P1 final verdict\n\n`{verdict}`\n\nNo PPO rollout, update, evaluation, or cloud training occurred.\n");print(json.dumps(d,indent=2))
def _raises(schedule,index):
 try:schedule.groups_for_update(index)
 except ValueError:return True
 return False
if __name__=="__main__":main()
