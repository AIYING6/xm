"""No-rollout integrity preflight; P3 launcher runs this before any cloud training."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; FREEZE=ROOT/"configs"/"drtp_klr_final_replication_freeze.json";TAPE=ROOT/"configs"/"drtp_klr_final_replication_tape.json";AUDIT=ROOT/"docs"/"drtp_klr_final_replication_20260831"/"KLR_FINAL_P0_TECHNICAL_AUDIT.json";SEEDS=ROOT/"docs"/"drtp_klr_final_replication_20260831"/"KLR_FINAL_P0_SEED_PROVENANCE.json"
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True);a=p.parse_args()
 if a.output.exists():raise FileExistsError(a.output)
 f=json.loads(FREEZE.read_text());t=json.loads(TAPE.read_text());u=json.loads(AUDIT.read_text());s=json.loads(SEEDS.read_text()); x=dict(t);h=x.pop("tape_hash")
 canonical=hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":")).encode()).hexdigest()
 checks={"p0_audit_pass":u["status"]=="KLR_FINAL_REPLICATION_READY_FOR_AUTHORIZATION","seeds_clean":s["status"]=="CLEAN","authorization_explicit":f["authorization"]["training_authorized"] is True,"tape_hash":h==canonical,"30_trajectories":(len(f["cohorts"]["A"])+len(f["cohorts"]["B"]))*len(f["arms"])==30,"budget":f["training"]["environment_steps"]==499968,"klr_exact":f["arms"]["drtp_klr_sg"]=={"sampler":"drtp","policy_update_guard_mode":"post_step_actor_rollback","target_kl":.02}}
 d={"status":"P3_PREFLIGHT_PASS" if all(checks.values()) else "P3_PREFLIGHT_FAIL","checks":checks,"hashes":{"freeze":sha(FREEZE),"tape":sha(TAPE),"audit":sha(AUDIT),"seeds":sha(SEEDS)},"zero_training_preflight":True}
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(d,indent=2)+"\n");print(json.dumps(d,indent=2));raise SystemExit(0 if all(checks.values()) else 1)
if __name__=="__main__":main()
