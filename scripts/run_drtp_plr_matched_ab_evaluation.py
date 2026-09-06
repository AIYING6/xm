from __future__ import annotations
import argparse,csv,hashlib,json,multiprocessing as mp,sys
from concurrent.futures import ProcessPoolExecutor,as_completed
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
from scripts.drtp_plr_matched_ab_contracts import SEEDS,STEPS,UPDATES,tape
from scripts.run_drtp_stabilization_confirmatory_evaluation import cell
PROTOCOL='DRTP-PLR-EXTERNAL-MATCHED-AB-ENDPOINT-EVALUATION-V2'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def write(p,rows):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def main():
 p=argparse.ArgumentParser();p.add_argument('--cohort',choices=('A','B'),required=True);p.add_argument('--trained-root',type=Path,required=True);p.add_argument('--output-root',type=Path,required=True);p.add_argument('--workers',type=int,default=10);p.add_argument('--execute',action='store_true');a=p.parse_args()
 if not a.execute:raise SystemExit('explicit --execute is required')
 if a.output_root.exists():raise FileExistsError(f'refusing to overwrite {a.output_root}')
 t=json.loads((a.trained_root/'cohorts'/a.cohort/'tape'/'tape_manifest.json').read_text(encoding='utf-8'))
 if t!=tape(a.cohort):raise RuntimeError('invalid tape')
 tasks=[];manifests=[]
 for seed in SEEDS[a.cohort]:
  run=a.trained_root/'cohorts'/a.cohort/'runs'/'plr_style_sg'/f'seed{seed}';ck=run/'actor_critic_latest.pt';m=json.loads((run/'run_manifest.json').read_text(encoding='utf-8'));expect={'status':'completed','updates':UPDATES,'environment_steps':STEPS,'from_scratch':True,'resume':False,'early_stopping':False,'checkpoint_promotion':False,'fixed_endpoint_tape_hash':t['tape_hash']}
  if any(m.get(k)!=v for k,v in expect.items()) or m.get('checkpoint_sha256')!=sha(ck):raise RuntimeError(f'invalid PLR run {seed}')
  tasks.append(('plr_style_sg',seed,str(ck),t['episode_ids'],t['conditions'],t['tape_hash'],PROTOCOL));manifests.append(m)
 total=len(tasks)*len(t['conditions'])*len(t['episode_ids']);raw=[];done=0;print(f'PLR matched {a.cohort} evaluation: cells={len(tasks)}, episodes={total}, workers={min(a.workers,len(tasks))}',flush=True)
 with ProcessPoolExecutor(max_workers=min(a.workers,len(tasks)),mp_context=mp.get_context('spawn')) as pool:
  fs=[pool.submit(cell,x) for x in tasks]
  for f in as_completed(fs):
   rows=f.result();raw.extend(rows);done+=len(rows);print(f'PLR matched {a.cohort} evaluation progress {done}/{total} ({100*done/total:.2f}%)',flush=True)
 order={x['name']:i for i,x in enumerate(t['conditions'])};raw.sort(key=lambda x:(int(x['train_seed']),order[x['topology_condition']],int(x['development_episode_id'])));write(a.output_root/'raw_episode_metrics.csv',raw)
 summary=[]
 for seed in SEEDS[a.cohort]:
  for c in order:
   rows=[x for x in raw if int(x['train_seed'])==seed and x['topology_condition']==c];summary.append({'method':'plr_style_sg','train_seed':seed,'condition':c,'episodes':len(rows),'J':sum(float(x['J']) for x in rows)/len(rows),'success':sum(float(x['success_at_horizon']) for x in rows)/len(rows),'collision':sum(float(x['collision']) for x in rows)/len(rows),'timeout':sum(float(x['timeout']) for x in rows)/len(rows),'constraint_violation':sum(float(x['constraint_violation']) for x in rows)/len(rows),'control_effort':sum(float(x['control_effort']) for x in rows)/len(rows)})
 write(a.output_root/'per_seed_condition_summary.csv',summary);(a.output_root/'evaluation_manifest.json').write_text(json.dumps({'protocol':PROTOCOL,'status':'completed','cohort':a.cohort,'tape_hash':t['tape_hash'],'raw_episode_rows':len(raw),'source_run_manifests':manifests,'training_started':False,'automatic_algorithm_revision':False},indent=2,default=str)+'\n',encoding='utf-8');print(json.dumps({'status':'completed','cohort':a.cohort,'raw_episode_rows':len(raw)},indent=2),flush=True)
if __name__=='__main__':main()
