"""One-time no-training repair for the P3 artifact-name validation defect."""
from __future__ import annotations
import argparse,hashlib,json,shutil
from pathlib import Path
ARMS=("utr_sg","drtp_sg","drtp_klr_sg");SEEDS=tuple(range(3701,3711))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument("--output-root",type=Path,required=True);p.add_argument("--execute",action="store_true");a=p.parse_args()
 if not a.execute:raise SystemExit("--execute required")
 audit=a.output_root/"diagnostics"/"technical_repair";audit.mkdir(parents=True,exist_ok=False); rows=[]
 for arm in ARMS:
  for seed in SEEDS:
   run=a.output_root/"runs"/arm/f"seed{seed}";m=run/"run_manifest.json";old=json.loads(m.read_text());required=[run/"actor_critic_milestone_250k.pt",run/"actor_critic_milestone_500k.pt",run/"actor_critic_runtime_state_milestone_500k.pt",run/"train_log.csv",run/"drtp_topology_sampler_log.csv"]
   lines=sum(1 for _ in (run/"train_log.csv").open(encoding="utf-8"));last=(run/"train_log.csv").read_text(encoding="utf-8").splitlines()[-1].split(",")[0]
   if not all(x.exists() for x in required) or lines!=1954 or last!="1953":raise RuntimeError(f"invalid artifact set: {run}")
   if old.get("status")!="failed" or old.get("error")!="RuntimeError('missing required frozen trajectory artifact')":raise RuntimeError(f"unexpected manifest state: {run}")
   backup=run/"run_manifest.pre_artifact_name_repair.json";shutil.copy2(m,backup);old["status"]="completed";old["technical_repair"]={"reason":"runner incorrectly expected actor_critic_latest.pt and milestone_976.pt; trainer writes milestone_500k.pt and milestone_250k.pt","zero_training":True,"checkpoint_selection":"fixed_500k_final_only","rerun":False,"original_manifest_sha256":sha(backup)};old.pop("error",None);m.write_text(json.dumps(old,indent=2)+"\n")
   rows.append({"arm":arm,"seed":seed,"manifest":str(m),"backup_sha256":sha(backup)})
 (audit/"P3_ARTIFACT_NAME_REPAIR.json").write_text(json.dumps({"status":"PASS","zero_training":True,"trajectories":rows,"training_rerun":False,"checkpoint_promotion":False},indent=2)+"\n");print("P3 manifest repair PASS: 30/30")
if __name__=="__main__":main()
