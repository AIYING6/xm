"""Dependency-light cloud integrity preflight for the authorized CV pilot."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; FREEZE=ROOT/"configs/cv_drtp_pilot_freeze.json"; TAPE=ROOT/"configs/cv_drtp_pilot_tape.json"
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True);a=p.parse_args()
 if a.output.exists(): raise FileExistsError(a.output)
 f=json.loads(FREEZE.read_text()); t=json.loads(TAPE.read_text()); seeds=f["cohorts"]["A"]+f["cohorts"]["B"]
 checks={"explicit_authorization":f["authorization"]["training_authorized"] is True,"exact_30_trajectories":len(seeds)*len(f["arms"])==30,"fresh_seed_order":seeds==list(range(4301,4311)),"budget":f["training"]["environment_steps"]==499968 and f["training"]["updates"]==1953,"cv_only_change":f["arms"]["cv_drtp_sg"]=={"sampler":"drtp","counterfactual_critic_enabled":True},"tape_shape":len(t["episode_ids"])==100 and len(t["conditions"])==5}
 payload={"status":"CV_DRTP_CLOUD_PREFLIGHT_PASS" if all(checks.values()) else "CV_DRTP_CLOUD_PREFLIGHT_FAIL","checks":checks,"hashes":{"freeze":sha(FREEZE),"tape":sha(TAPE)},"pytest_required":False};a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(payload,indent=2)+"\n");print(json.dumps(payload,indent=2));raise SystemExit(0 if all(checks.values()) else 1)
if __name__=="__main__":main()
