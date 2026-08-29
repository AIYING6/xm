"""Cloud-only, zero-training milestone evaluation for immutable R1 checkpoints."""
from __future__ import annotations
import argparse,csv,json,multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor,as_completed
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
import run_drtp_sg_development_evaluation as base  # noqa
ARMS=('utr_sg','drtp_sg','conservative_drtp_sg');SEEDS=(3001,3002,3003,3004,3005);MILESTONES={976:'250k',1953:'500k',2930:'750k',3907:'1m'};TAPE=ROOT/'configs/drtp_stable_r1_development_tape.json'
def avg(rows,k):return sum(float(r[k]) for r in rows)/len(rows)
def main():
 p=argparse.ArgumentParser();p.add_argument('--r1-root',type=Path,required=True);p.add_argument('--output-root',type=Path,required=True);p.add_argument('--workers',type=int,default=15);p.add_argument('--execute',action='store_true');a=p.parse_args()
 if not a.execute or a.workers<1:raise SystemExit('--execute and positive workers required')
 tape=json.loads(TAPE.read_text());target=a.output_root/'evaluations'/'milestones'
 if target.exists():raise FileExistsError(target)
 target.mkdir(parents=True);tasks=[];sources=[]
 for arm in ARMS:
  for seed in SEEDS:
   run=a.r1_root/'runs'/arm/f'seed{seed}';m=json.loads((run/'run_manifest.json').read_text())
   if m.get('status')!='completed' or m.get('updates')!=3907 or m.get('tape_hash')!=tape['tape_hash']:raise RuntimeError(f'invalid frozen R1 source {run}')
   for update,label in MILESTONES.items():
    ckpt=run/f'actor_critic_milestone_{label}.pt'
    if not ckpt.exists():raise FileNotFoundError(ckpt)
    for condition in tape['conditions']:tasks.append((arm,seed,str(ckpt),label,tape['episode_ids'],[condition],tape['tape_hash']))
   sources.append({'arm':arm,'seed':seed,'manifest':m,'run_dir':str(run)})
 total=len(tasks)*100;done=0;rows=[];workers=min(a.workers,len(tasks));print(f'R1 forensic milestone evaluation: workers={workers}, cells={len(tasks)}, episodes={total}',flush=True)
 with ProcessPoolExecutor(max_workers=workers,mp_context=mp.get_context('spawn')) as pool:
  futures=[pool.submit(base.evaluate_cell,t) for t in tasks]
  for x in as_completed(futures):rows.extend(x.result());done+=100;print(f'R1 forensic evaluation progress {done}/{total} ({100*done/total:.2f}%)',flush=True)
 order={c['name']:i for i,c in enumerate(tape['conditions'])};rows.sort(key=lambda r:(r['method'],int(r['train_seed']),r['evaluation_budget'],order[r['topology_condition']],int(r['development_episode_id'])))
 with (target/'raw_episode_metrics.csv').open('w',newline='',encoding='utf8') as h:w=csv.DictWriter(h,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 summary=[]
 for arm in ARMS:
  for seed in SEEDS:
   for label in MILESTONES.values():
    for c in tape['conditions']:
     z=[r for r in rows if r['method']==arm and int(r['train_seed'])==seed and r['evaluation_budget']==label and r['topology_condition']==c['name']]
     summary.append({'method':arm,'train_seed':seed,'milestone':label,'condition':c['name'],'J':avg(z,'J'),'collision':avg(z,'collision'),'timeout':avg(z,'timeout'),'constraint_violation':avg(z,'constraint_violation')})
 with (target/'per_seed_condition_summary.csv').open('w',newline='',encoding='utf8') as h:w=csv.DictWriter(h,fieldnames=list(summary[0]));w.writeheader();w.writerows(summary)
 payload={'protocol':'DRTP-STABLE-R1-FORENSIC-STAGE2-V1','status':'completed','training_started':False,'checkpoint_promotion':False,'selection_forbidden':True,'raw_rows':len(rows),'cells':len(tasks),'episodes_per_cell':100,'workers':workers,'tape_hash':tape['tape_hash'],'source_runs':sources,'automatic_follow_on_started':False}
 (target/'evaluation_manifest.json').write_text(json.dumps(payload,indent=2,default=str)+'\n');print(json.dumps(payload,indent=2,default=str))
if __name__=='__main__':main()
