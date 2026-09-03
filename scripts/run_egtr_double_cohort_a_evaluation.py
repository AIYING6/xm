"""Final-checkpoint evaluation for the authorized EGTR Cohort A only."""
from __future__ import annotations
import argparse,csv,hashlib,json,math,multiprocessing as mp,sys
from concurrent.futures import ProcessPoolExecutor,as_completed
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/"scripts")]
import run_phase_rsg1_development_smoke as evaluator
from envs.uav_intercept_3d_env import UAVIntercept3DConfig,UAVIntercept3DEnv
ARMS=("utr_sg","drtp_sg","egtr_sg");SEEDS=(71011,71012,71013,71014,71015); TAPE_PROTOCOL="EGTR-DOUBLE-COHORT-A-DEVELOPMENT-TAPE-V1"; PROTOCOL="EGTR-DOUBLE-COHORT-A-10M-EVALUATION-V1"
def digest(p):
 h=hashlib.sha256()
 with Path(p).open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest()
def env(seed,spec):
 onset,duration=(0,0) if spec is None else spec
 return UAVIntercept3DEnv(UAVIntercept3DConfig(seed=seed,target_policy="straight",strict_target_sensing=True,agent_target_info_bottleneck=True,relay_dependent_task=True,business_grounded_geometry=True,communication_range_scale=1.,communication_dropout_prob=0.,message_delay_steps=0,radar_dropout_prob=0.,max_steps=260,min_success_step=260,failed_blue_agent=-1 if spec is None else 1,node_failure_start_step=onset,node_failure_duration_steps=duration))
def cell(task):
 arm,seed,checkpoint,ids,conditions,tape_hash=task; import torch;torch.set_num_threads(1);agent=evaluator.build_agent({"graph_encoder":"single","hidden_dim":115},Path(checkpoint),seed); rows=[]
 for condition in conditions:
  name=str(condition["name"]);spec=None if name=="nominal" else (int(condition["start_step"]),int(condition["duration_steps"])); original=evaluator.frozen_env;evaluator.frozen_env=lambda episode_seed,failure_on,_spec=spec:env(episode_seed,_spec)
  try:
   for episode_id in ids:
    row,_=evaluator.evaluate_episode(agent,arm,seed,episode_id,"nominal" if spec is None else "relay_failure");row.update({"protocol":PROTOCOL,"topology_condition":name,"scheduled_failure_onset":"" if spec is None else spec[0],"scheduled_failure_duration":"" if spec is None else spec[1],"checkpoint_sha256":digest(checkpoint),"tape_hash":tape_hash});rows.append(row)
  finally:evaluator.frozen_env=original
 return rows
def write(path,rows):
 path.parent.mkdir(parents=True,exist_ok=True)
 with path.open("w",newline="",encoding="utf-8") as h:
  w=csv.DictWriter(h,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def mean(rows,key):
 v=[float(r[key]) for r in rows if key in r and math.isfinite(float(r[key]))];return sum(v)/len(v) if v else math.nan
def main():
 p=argparse.ArgumentParser();p.add_argument("--trained-root",type=Path,required=True);p.add_argument("--output-root",type=Path,required=True);p.add_argument("--workers",type=int,default=6);p.add_argument("--execute",action="store_true");a=p.parse_args()
 if not a.execute:raise SystemExit("--execute required")
 if a.output_root.exists():raise FileExistsError(a.output_root)
 tape=json.loads((a.trained_root/"tape"/"tape_manifest.json").read_text())
 if tape.get("protocol")!=TAPE_PROTOCOL or tape.get("episode_ids")!=list(range(720000,720100)):raise RuntimeError("invalid Cohort-A tape")
 tasks=[];manifests=[]
 for arm in ARMS:
  for seed in SEEDS:
   d=a.trained_root/"runs"/arm/f"seed{seed}";m=json.loads((d/"run_manifest.json").read_text())
   if not(m.get("status")=="completed" and m.get("updates")==39063 and m.get("environment_steps")==10000128 and m.get("from_scratch") is True and m.get("checkpoint_promotion") is False):raise RuntimeError(f"invalid run {arm}/{seed}")
   checkpoint=d/"actor_critic_latest.pt"
   if not checkpoint.exists() or m.get("checkpoint_sha256")!=digest(checkpoint):raise RuntimeError(f"bad checkpoint {checkpoint}")
   tasks.append((arm,seed,str(checkpoint),tape["episode_ids"],tape["conditions"],tape["tape_hash"]));manifests.append(m)
 total=len(tasks)*len(tape["conditions"])*len(tape["episode_ids"]);print(f"EGTR Cohort A evaluation: cells={len(tasks)}, episodes={total}, workers={min(a.workers,len(tasks))}",flush=True); raw=[];done=0
 with ProcessPoolExecutor(max_workers=min(a.workers,len(tasks)),mp_context=mp.get_context("spawn")) as pool:
  futures=[pool.submit(cell,t) for t in tasks]
  for future in as_completed(futures):
   rows=future.result();raw.extend(rows);done+=len(rows);print(f"EGTR Cohort A evaluation progress {done}/{total} ({100*done/total:.2f}%)",flush=True)
 order={x["name"]:i for i,x in enumerate(tape["conditions"])};raw.sort(key=lambda x:(x["method"],int(x["train_seed"]),order[x["topology_condition"]],int(x["development_episode_id"])));write(a.output_root/"raw_episode_metrics.csv",raw)
 summary=[]
 for arm in ARMS:
  for seed in SEEDS:
   for c in order:
    rows=[r for r in raw if r["method"]==arm and int(r["train_seed"])==seed and r["topology_condition"]==c];summary.append({"method":arm,"train_seed":seed,"condition":c,"episodes":len(rows),"J":mean(rows,"J"),"collision":mean(rows,"collision"),"timeout":mean(rows,"timeout"),"constraint_violation":mean(rows,"constraint_violation")})
 write(a.output_root/"per_seed_condition_summary.csv",summary);m={"protocol":PROTOCOL,"status":"completed","raw_rows":len(raw),"cells":len(tasks),"episodes_per_condition":100,"conditions":len(tape["conditions"]),"tape_hash":tape["tape_hash"],"source_runs":manifests,"cohort":"A","cohort_b_started":False};(a.output_root/"evaluation_manifest.json").write_text(json.dumps(m,indent=2)+"\n")
if __name__=="__main__":main()
