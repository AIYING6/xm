"""Evaluate only the frozen final-0.5M P3 checkpoints on the P3 development tape."""
from __future__ import annotations
import argparse,csv,json,multiprocessing as mp,sys
from concurrent.futures import ProcessPoolExecutor,as_completed
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/"scripts")]
import run_drtp_sg_development_evaluation as base
ARMS=("utr_sg","drtp_sg","drtp_klr_sg");SEEDS=tuple(range(3701,3711));TAPE=ROOT/"configs"/"drtp_klr_final_replication_tape.json"
def avg(rows,k):return sum(float(r[k]) for r in rows)/len(rows)
def main():
 p=argparse.ArgumentParser();p.add_argument("--output-root",type=Path,required=True);p.add_argument("--workers",type=int,default=9);p.add_argument("--execute",action="store_true");a=p.parse_args()
 if not a.execute or a.workers!=9:raise SystemExit("frozen P3 requires --execute --workers 9")
 tape=json.loads(TAPE.read_text());out=a.output_root/"evaluations"/"final_05m"
 if out.exists():raise FileExistsError(f"refusing evaluation rerun: {out}")
 out.mkdir(parents=True);tasks=[];manifests=[]
 for arm in ARMS:
  for seed in SEEDS:
   run=a.output_root/"runs"/arm/f"seed{seed}";m=json.loads((run/"run_manifest.json").read_text())
   if m.get("status")!="completed" or m.get("updates")!=1953 or m.get("environment_steps")!=499968 or m.get("tape_hash")!=tape["tape_hash"]:raise RuntimeError(f"invalid source run: {run}")
   for c in tape["conditions"]:tasks.append((arm,seed,str(run/"actor_critic_latest.pt"),"500k",tape["episode_ids"],[c],tape["tape_hash"]))
   manifests.append(m)
 total=len(tasks)*100;done=0;rows=[];print(f"KLR final P3 evaluation: workers=9, cells={len(tasks)}, episodes={total}",flush=True)
 with ProcessPoolExecutor(max_workers=9,mp_context=mp.get_context("spawn")) as ex:
  fs=[ex.submit(base.evaluate_cell,t) for t in tasks]
  for f in as_completed(fs):
   q=f.result();rows+=q;done+=len(q);print(f"KLR final P3 evaluation progress {done}/{total} ({100*done/total:.2f}%)",flush=True)
 if len(rows)!=total:raise RuntimeError("incomplete raw rows")
 rows.sort(key=lambda r:(r["method"],int(r["train_seed"]),r["topology_condition"],int(r["development_episode_id"])))
 with (out/"raw_episode_metrics.csv").open("w",newline="",encoding="utf-8") as h:w=csv.DictWriter(h,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 s=[]
 for arm in ARMS:
  for seed in SEEDS:
   for c in tape["conditions"]:
    q=[r for r in rows if r["method"]==arm and int(r["train_seed"])==seed and r["topology_condition"]==c["name"]]
    if len(q)!=100:raise RuntimeError("incomplete cell")
    s.append({"method":arm,"train_seed":seed,"condition":c["name"],**{k:avg(q,k) for k in ("J","collision","timeout","constraint_violation","failure_exposed")}})
 with (out/"per_seed_condition_summary.csv").open("w",newline="",encoding="utf-8") as h:w=csv.DictWriter(h,fieldnames=list(s[0]));w.writeheader();w.writerows(s)
 (out/"evaluation_manifest.json").write_text(json.dumps({"protocol":"DRTP-KLR-FINAL-P3-EVAL-V1","status":"completed","raw_rows":len(rows),"cells":len(tasks),"workers":9,"tape_hash":tape["tape_hash"],"source_runs":manifests,"checkpoint_promotion":False,"automatic_follow_on_started":False},indent=2)+"\n")
if __name__=="__main__":main()
