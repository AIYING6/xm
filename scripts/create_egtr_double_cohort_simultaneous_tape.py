"""Create the one frozen development-only tape for simultaneous A/B execution."""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
def main():
 p=argparse.ArgumentParser();p.add_argument("--output-root",type=Path,required=True);a=p.parse_args();ids=list(range(720000,720100));conds={"nominal":None,"F0":(44,80),"TE":(28,80),"TL":(52,80),"DS":(44,40),"DL":(44,100),"CP":(28,120)}
 d={"protocol":"EGTR-DOUBLE-COHORT-SIMULTANEOUS-DEVELOPMENT-TAPE-V1","episode_ids":ids,"conditions":[{"name":n,"failed_blue_agent":-1 if x is None else 1,"start_step":0 if x is None else x[0],"duration_steps":0 if x is None else x[1]} for n,x in conds.items()],"episodes_per_condition":100,"same_base_ids_across_conditions":True,"canonical":False,"development_only":True,"training_access":"forbidden","cohort_specific_tape_selection":False}
 d["tape_hash"]=hashlib.sha256(json.dumps(d,sort_keys=True,separators=(",", ":")).encode()).hexdigest();a.output_root.mkdir(parents=True,exist_ok=True);path=a.output_root/"tape_manifest.json"
 if path.exists() and json.loads(path.read_text()).get("tape_hash")!=d["tape_hash"]:raise RuntimeError("existing tape differs")
 path.write_text(json.dumps(d,indent=2)+"\n");print(json.dumps(d,indent=2))
if __name__=="__main__":main()
