"""Evaluate all 30 final checkpoints, retaining cohort labels for separate gates."""
from __future__ import annotations
import argparse,csv,json,math,multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor,as_completed
from pathlib import Path
import run_egtr_p3_evaluation as base
ARMS=("utr_sg","drtp_sg","egtr_sg");SEEDS=(71011,71012,71013,71014,71015,71021,71022,71023,71024,71025);PROTOCOL="EGTR-DOUBLE-COHORT-SIMULTANEOUS-10M-EVALUATION-V1"
def cell(task):
 base.PROTOCOL=PROTOCOL
 return base.evaluate_cell(task)
def write(path,rows):
 path.parent.mkdir(parents=True,exist_ok=True)
 with path.open("w",newline="",encoding="utf-8") as h:w=csv.DictWriter(h,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def mean(rows,key):
 x=[float(r[key]) for r in rows if key in r and math.isfinite(float(r[key]))];return sum(x)/len(x) if x else math.nan
def main():
 p=argparse.ArgumentParser();p.add_argument("--trained-root",type=Path,required=True);p.add_argument("--output-root",type=Path,required=True);p.add_argument("--workers",type=int,default=10);p.add_argument("--execute",action="store_true");a=p.parse_args()
 if not a.execute:raise SystemExit("--execute required")
 if a.output_root.exists():raise FileExistsError(a.output_root)
 tape=json.loads((a.trained_root/"tape"/"tape_manifest.json").read_text())
 if tape.get("protocol")!="EGTR-DOUBLE-COHORT-SIMULTANEOUS-DEVELOPMENT-TAPE-V1" or tape.get("episode_ids")!=list(range(720000,720100)):raise RuntimeError("invalid tape")
 tasks=[];source=[]
 for arm in ARMS:
  for seed in SEEDS:
   d=a.trained_root/"runs"/arm/f"seed{seed}";m=json.loads((d/"run_manifest.json").read_text());ck=d/"actor_critic_latest.pt"
   if not(m.get("status")=="completed" and m.get("updates")==39063 and m.get("environment_steps")==10000128 and m.get("from_scratch") is True and m.get("checkpoint_promotion") is False and m.get("cohort") in {"A","B"} and ck.exists()):raise RuntimeError(f"bad {arm}/{seed}")
   tasks.append((arm,seed,str(ck),tape["episode_ids"],tape["conditions"],tape["tape_hash"]));source.append(m)
 total=len(tasks)*7*100;done=0;raw=[];print(f"EGTR dual-cohort evaluation: cells={len(tasks)}, episodes={total}, workers={min(a.workers,len(tasks))}",flush=True)
 with ProcessPoolExecutor(max_workers=min(a.workers,len(tasks)),mp_context=mp.get_context("spawn")) as pool:
  for f in as_completed([pool.submit(cell,t) for t in tasks]):
   rows=f.result();raw.extend(rows);done+=len(rows);print(f"EGTR dual-cohort evaluation progress {done}/{total} ({100*done/total:.2f}%)",flush=True)
 order={x["name"]:i for i,x in enumerate(tape["conditions"])};raw.sort(key=lambda r:(r["method"],int(r["train_seed"]),order[r["topology_condition"]],int(r["development_episode_id"])));write(a.output_root/"raw_episode_metrics.csv",raw);summary=[]
 for arm in ARMS:
  for seed in SEEDS:
   for c in order:
    x=[r for r in raw if r["method"]==arm and int(r["train_seed"])==seed and r["topology_condition"]==c];summary.append({"method":arm,"train_seed":seed,"cohort":"A" if seed<71020 else "B","condition":c,"episodes":len(x),"J":mean(x,"J"),"collision":mean(x,"collision"),"timeout":mean(x,"timeout")})
 write(a.output_root/"per_seed_condition_summary.csv",summary);(a.output_root/"evaluation_manifest.json").write_text(json.dumps({"protocol":PROTOCOL,"status":"completed","raw_rows":len(raw),"cells":len(tasks),"episodes_per_condition":100,"conditions":7,"tape_hash":tape["tape_hash"],"source_runs":source,"cohorts_separate":True,"pooled_n10_confirmatory_forbidden":True},indent=2)+"\n")
if __name__=="__main__":main()
