"""Frozen final-1M R1 evaluation; never trains or promotes checkpoints."""
from __future__ import annotations
import argparse, csv, json, multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]; sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
import run_drtp_sg_development_evaluation as base  # noqa
ARMS=("utr_sg","drtp_sg","conservative_drtp_sg"); SEEDS=(3001,3002,3003,3004,3005)
TAPE=ROOT/'configs/drtp_stable_r1_development_tape.json'
def avg(rows,key): return sum(float(x[key]) for x in rows)/len(rows)
def main():
 p=argparse.ArgumentParser();p.add_argument('--output-root',type=Path,required=True);p.add_argument('--workers',type=int,default=8);p.add_argument('--execute',action='store_true');a=p.parse_args()
 if not a.execute or not 1<=a.workers<=8: raise SystemExit('R1 requires --execute and 1..8 workers')
 tape=json.loads(TAPE.read_text()); target=a.output_root/'evaluations'/'final_1m'
 if target.exists(): raise FileExistsError(target)
 target.mkdir(parents=True); tasks=[]; manifests=[]
 for arm in ARMS:
  for seed in SEEDS:
   run=a.output_root/'runs'/arm/f'seed{seed}'; m=json.loads((run/'run_manifest.json').read_text())
   if m.get('status')!='completed' or m.get('protocol')!='DRTP-STABLE-R1-DEVELOPMENT-V1' or m.get('updates')!=3907 or m.get('environment_steps')!=1000192 or m.get('tape_hash')!=tape['tape_hash']: raise RuntimeError(f'invalid source {run}')
   for c in tape['conditions']: tasks.append((arm,seed,str(run/'actor_critic_latest.pt'),'1m',tape['episode_ids'],[c],tape['tape_hash']))
   manifests.append(m)
 total=len(tasks)*100; rows=[]; done=0; print(f'R1 evaluation: workers={a.workers}, cells={len(tasks)}, episodes={total}',flush=True)
 with ProcessPoolExecutor(max_workers=a.workers,mp_context=mp.get_context('spawn')) as pool:
  futures=[pool.submit(base.evaluate_cell,t) for t in tasks]
  for f in as_completed(futures): rows.extend(f.result());done+=100;print(f'R1 evaluation progress {done}/{total} ({100*done/total:.2f}%)',flush=True)
 order={c['name']:i for i,c in enumerate(tape['conditions'])}; rows.sort(key=lambda r:(r['method'],int(r['train_seed']),order[r['topology_condition']],int(r['development_episode_id'])))
 with (target/'raw_episode_metrics.csv').open('w',newline='',encoding='utf8') as h: w=csv.DictWriter(h,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 summary=[]
 for arm in ARMS:
  for seed in SEEDS:
   for c in tape['conditions']:
    z=[r for r in rows if r['method']==arm and int(r['train_seed'])==seed and r['topology_condition']==c['name']]
    summary.append({'method':arm,'train_seed':seed,'condition':c['name'],'J':avg(z,'J'),'collision':avg(z,'collision'),'timeout':avg(z,'timeout'),'constraint_violation':avg(z,'constraint_violation')})
 with (target/'per_seed_condition_summary.csv').open('w',newline='',encoding='utf8') as h: w=csv.DictWriter(h,fieldnames=list(summary[0]));w.writeheader();w.writerows(summary)
 payload={'protocol':'DRTP-STABLE-R1-EVALUATION-V1','status':'completed','raw_rows':len(rows),'cells':len(tasks),'episodes_per_condition':100,'workers':a.workers,'tape_hash':tape['tape_hash'],'source_runs':manifests,'automatic_follow_on_started':False}
 (target/'evaluation_manifest.json').write_text(json.dumps(payload,indent=2,default=str)+'\n');print(json.dumps(payload,indent=2,default=str))
if __name__=='__main__': main()
