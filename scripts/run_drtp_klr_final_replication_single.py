"""One frozen P3 KLR final-replication training trajectory (cloud only)."""
from __future__ import annotations
import argparse, hashlib, json, subprocess, sys, time
from dataclasses import replace
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path[:0]=[str(ROOT),str(ROOT/"scripts")]
from algorithms.ri_gmappo.simple_ri_gmappo import train_ri_gmappo
import run_drtp_sg_strict_10m_single as strict
FREEZE=ROOT/"configs"/"drtp_klr_final_replication_freeze.json"; TAPE=ROOT/"configs"/"drtp_klr_final_replication_tape.json"
ARMS={"utr_sg":("utr","none",None),"drtp_sg":("drtp","none",None),"drtp_klr_sg":("drtp","post_step_actor_rollback",.02)}
SEEDS=tuple(range(3701,3711)); UPDATES=1953; MILESTONES={976:"250k",1953:"500k"}
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def head():
 try:return subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()
 except Exception:return "UNAVAILABLE"
def config(arm,seed,out):
 if arm not in ARMS or seed not in SEEDS: raise ValueError("frozen P3 arm/seed violation")
 sampler,guard,kl=ARMS[arm]; t=strict.training_config("utr_sg",strict.SEEDS[0],out)
 return replace(t,seed=seed,updates=UPDATES,save_interval=976,milestone_updates=MILESTONES,out_dir=str(out),drtp_sampler_mode=sampler,drtp_sampler_seed=seed,drtp_sampler_total_updates=UPDATES,policy_update_guard_mode=guard,target_kl=kl,runtime_state_checkpointing=True,runtime_state_save_interval=976,evaluation_enabled=False)
def main():
 p=argparse.ArgumentParser();p.add_argument("--arm",choices=ARMS,required=True);p.add_argument("--seed",type=int,choices=SEEDS,required=True);p.add_argument("--output-root",type=Path,required=True);p.add_argument("--execute",action="store_true");a=p.parse_args()
 if not a.execute: raise SystemExit("--execute required")
 freeze=json.loads(FREEZE.read_text()); tape=json.loads(TAPE.read_text())
 if freeze["authorization"]["training_authorized"] is not True: raise RuntimeError("P3 authorization flag not enabled in delivery freeze")
 out=a.output_root/"runs"/a.arm/f"seed{a.seed}"; 
 if out.exists(): raise FileExistsError(f"refusing rerun/overwrite: {out}")
 out.mkdir(parents=True); cfg=config(a.arm,a.seed,out); cohort="A" if a.seed<=3705 else "B"
 m={"protocol":"DRTP-KLR-FINAL-REPLICATION-P3-V1","status":"running","delivery_commit":head(),"arm":a.arm,"seed":a.seed,"cohort":cohort,"updates":UPDATES,"environment_steps":499968,"milestones":MILESTONES,"sampler":cfg.drtp_sampler_mode,"policy_update_guard_mode":cfg.policy_update_guard_mode,"target_kl":cfg.target_kl,"tape_sha256":sha(TAPE),"tape_hash":tape["tape_hash"],"freeze_sha256":sha(FREEZE),"early_stopping":False,"checkpoint_promotion":False,"seed_replacement":False,"performance_rerun":False,"automatic_continuation":False,"started_at":time.time()}
 (out/"run_manifest.json").write_text(json.dumps(m,indent=2)+"\n")
 try:
  train_ri_gmappo(cfg); required=[out/"actor_critic_milestone_250k.pt",out/"actor_critic_milestone_500k.pt",out/"actor_critic_runtime_state_milestone_500k.pt",out/"train_log.csv",out/"drtp_topology_sampler_log.csv"]
  if not all(x.exists() for x in required): raise RuntimeError("missing required frozen trajectory artifact")
  m["status"]="completed";m["completed_at"]=time.time()
 except BaseException as e:
  m["status"]="failed";m["error"]=repr(e);(out/"run_manifest.json").write_text(json.dumps(m,indent=2)+"\n");raise
 (out/"run_manifest.json").write_text(json.dumps(m,indent=2)+"\n")
if __name__=="__main__":main()
