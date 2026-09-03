"""Create the frozen, training-inaccessible Cohort-A development tape."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

PROTOCOL = "EGTR-DOUBLE-COHORT-A-DEVELOPMENT-TAPE-V1"
EPISODE_IDS = list(range(720000, 720100))
CONDITIONS = {"nominal": None, "F0": (44,80), "TE": (28,80), "TL": (52,80), "DS": (44,40), "DL": (44,100), "CP": (28,120)}

def main():
    p=argparse.ArgumentParser(); p.add_argument("--output-root",type=Path,required=True); a=p.parse_args()
    payload={"protocol":PROTOCOL,"episode_ids":EPISODE_IDS,"conditions":[{"name":n,"failed_blue_agent":-1 if spec is None else 1,"start_step":0 if spec is None else spec[0],"duration_steps":0 if spec is None else spec[1]} for n,spec in CONDITIONS.items()],"episodes_per_condition":100,"same_base_ids_across_conditions":True,"canonical":False,"development_only":True,"training_access":"forbidden","held_out":False,"future_cohort_b_not_generated":True}
    encoded=json.dumps(payload,sort_keys=True,separators=(",", ":")).encode(); payload["tape_hash"]=hashlib.sha256(encoded).hexdigest()
    a.output_root.mkdir(parents=True,exist_ok=True); path=a.output_root/"tape_manifest.json"
    if path.exists() and json.loads(path.read_text()).get("tape_hash")!=payload["tape_hash"]: raise RuntimeError("existing tape differs")
    path.write_text(json.dumps(payload,indent=2)+"\n"); print(json.dumps(payload,indent=2))
if __name__=="__main__":main()
