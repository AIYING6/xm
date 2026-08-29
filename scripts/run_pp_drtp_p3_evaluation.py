"""Evaluate frozen PP-DRTP P3 final 0.5M checkpoints only."""
from __future__ import annotations
import argparse,csv,hashlib,json,multiprocessing as mp,sys
from concurrent.futures import ProcessPoolExecutor,as_completed
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
import run_drtp_sg_development_evaluation as base
ARMS=('utr_sg','drtp_sg','pp_drtp_sg');SEEDS=(3401,3402,3403);TAPE=ROOT/'configs'/'pp_drtp_p3_pilot_tape.json'
def main():
 p=argparse.ArgumentParser();p.add_argument('--output-root',type=Path,required=True);p.add_argument('--workers',type=int,default=9);p.add_argument('--execute',action='store_true');a=p.parse_args()
 if not a.execute or a.workers!=9:raise SystemExit('frozen workers=9 and --execute required')
 tape=json.loads(TAPE.read_text());th=hashlib.sha256(TAPE.read_bytes()).hexdigest();out=a.output_root/'evaluations'/'final_05m'
 if out.exists():raise FileExistsError('refusing evaluation rerun');
 out.mkdir(parents=True); tasks=[]
 for arm in ARMS:
  for seed in SEEDS:
   run=a.output_root/'runs'/arm/f'seed{seed}';m=json.loads((run/'run_manifest.json').read_text())
   if m.get('status')!='completed' or m.get('protocol')!='PP-DRTP-P3-PILOT-V1' or m.get('tape_hash')!=th:raise RuntimeError(f'invalid run {run}')
   for c in tape['conditions']:tasks.append((arm,seed,str(run/'actor_critic_latest.pt'),'500k',tape['episode_ids'],[c],th))
 rows=[];done=0;total=len(tasks)*100;print(f'PP P3 evaluation: workers=9, cells={len(tasks)}, episodes={total}',flush=True)
 with ProcessPoolExecutor(max_workers=9,mp_context=mp.get_context('spawn')) as pool:
  fs=[pool.submit(base.evaluate_cell,x) for x in tasks]
  for f in as_completed(fs): rows+=f.result();done+=100;print(f'PP P3 evaluation progress {done}/{total} ({100*done/total:.2f}%)',flush=True)
 rows.sort(key=lambda x:(x['method'],int(x['train_seed']),x['topology_condition'],int(x['development_episode_id'])))
 with (out/'raw_episode_metrics.csv').open('w',newline='',encoding='utf-8') as h:
  w=csv.DictWriter(h,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 summary=[]
 for arm in ARMS:
  for seed in SEEDS:
   for c in tape['conditions']:
    z=[r for r in rows if r['method']==arm and int(r['train_seed'])==seed and r['topology_condition']==c['name']]
    summary.append({'method':arm,'train_seed':seed,'condition':c['name'],**{k:sum(float(r[k]) for r in z)/100 for k in ('J','collision','timeout','constraint_violation')}})
 with (out/'condition_summary.csv').open('w',newline='',encoding='utf-8') as h:w=csv.DictWriter(h,fieldnames=list(summary[0]));w.writeheader();w.writerows(summary)
if __name__=='__main__':main()
