"""Run exactly one frozen Cohort-A 10M UTR/DRTP/EGTR trajectory."""
from __future__ import annotations
import argparse, hashlib, json, subprocess, sys
from pathlib import Path
import torch
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from algorithms.ri_gmappo.simple_ri_gmappo import RIGMAPPOConfig, train_ri_gmappo
PROTOCOL="EGTR-DOUBLE-COHORT-A-10M-TRAINING-V1"; SEEDS=(71011,71012,71013,71014,71015); ARMS={"utr_sg":"utr","drtp_sg":"drtp","egtr_sg":"egtr"}; UPDATES=39063; NUM_ENVS=4; ROLLOUT=64; STEPS=UPDATES*NUM_ENVS*ROLLOUT; MILESTONES={3907:"1m",11719:"3m",39063:"10m"}; TAPE_PROTOCOL="EGTR-DOUBLE-COHORT-A-DEVELOPMENT-TAPE-V1"
def digest(p:Path):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest()
def commit():
 try:return subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()
 except Exception:return "package-provenance-only"
def tape(root):
 x=json.loads((root/"tape"/"tape_manifest.json").read_text())
 if x.get("protocol")!=TAPE_PROTOCOL or x.get("episode_ids")!=list(range(720000,720100)) or x.get("development_only") is not True or x.get("training_access")!="forbidden":raise RuntimeError("invalid frozen Cohort-A tape")
 return x
def config(arm,seed,out):
 return RIGMAPPOConfig(env_name="3d_intercept",seed=seed,num_envs=NUM_ENVS,rollout_steps=ROLLOUT,updates=UPDATES,hidden_dim=115,role_dim=8,intent_dim=8,graph_encoder="single",role_gate_mode="none",target_policy="straight",strict_target_sensing=True,agent_target_info_bottleneck=True,relay_dependent_task=True,business_grounded_geometry=True,communication_range_scale=1.0,communication_dropout_prob=0.0,message_delay_steps=0,radar_dropout_prob=0.0,min_success_step=260,failed_blue_agent=-1,node_failure_start_step=0,node_failure_duration_steps=0,evaluation_enabled=False,target_kl=None,save_interval=UPDATES,save_snapshots=False,milestone_updates=MILESTONES,out_dir=str(out),device="cuda" if torch.cuda.is_available() else "cpu",topology_curriculum_schedule="none",topology_curriculum_logging=False,fixed_f0_probability=None,drtp_sampler_mode=ARMS[arm],drtp_sampler_seed=seed,drtp_sampler_logging=True,runtime_state_checkpointing=True,runtime_state_save_interval=UPDATES)
def run(arm,seed,root):
 if arm not in ARMS or seed not in SEEDS:raise ValueError("unfrozen cell")
 t=tape(root); out=root/"runs"/arm/f"seed{seed}"
 if out.exists():raise FileExistsError(f"refusing overwrite {out}")
 out.mkdir(parents=True); cfg=config(arm,seed,out); man={"protocol":PROTOCOL,"status":"running","arm":arm,"sampler_mode":ARMS[arm],"seed":seed,"updates":UPDATES,"environment_steps":STEPS,"from_scratch":True,"resume":False,"early_stopping":False,"checkpoint_promotion":False,"seed_replacement":False,"final_checkpoint_only_for_decision":True,"milestones_for_diagnosis_only":True,"parameter_count":116728,"tape_hash":t["tape_hash"],"tape_not_read_by_training":True,"source_commit":commit(),"config":cfg.__dict__}
 (out/"run_manifest.json").write_text(json.dumps(man,indent=2,default=str)+"\n"); train_ri_gmappo(cfg)
 ckpt=out/"actor_critic_latest.pt"; runtime=out/"actor_critic_runtime_state_latest.pt"; sampler=out/"drtp_topology_sampler_manifest.json"
 for p in (ckpt,runtime,sampler,out/"drtp_topology_sampler_log.csv"):
  if not p.exists():raise FileNotFoundError(p)
 for label in MILESTONES.values():
  for prefix in ("actor_critic_milestone_","actor_critic_runtime_state_milestone_"):
   if not (out/f"{prefix}{label}.pt").exists():raise FileNotFoundError(f"missing {prefix}{label}")
 man.update({"status":"completed","checkpoint_sha256":digest(ckpt),"runtime_state_sha256":digest(runtime),"sampler_manifest_sha256":digest(sampler)})
 (out/"run_manifest.json").write_text(json.dumps(man,indent=2,default=str)+"\n");print(json.dumps({"status":"completed","arm":arm,"seed":seed},indent=2))
def main():
 p=argparse.ArgumentParser();p.add_argument("--arm",choices=ARMS,required=True);p.add_argument("--seed",type=int,choices=SEEDS,required=True);p.add_argument("--output-root",type=Path,required=True);p.add_argument("--execute",action="store_true");a=p.parse_args()
 if not a.execute:raise SystemExit("--execute required")
 run(a.arm,a.seed,a.output_root)
if __name__=="__main__":main()
