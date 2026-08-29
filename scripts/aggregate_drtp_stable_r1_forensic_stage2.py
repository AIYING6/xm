"""Align R1 milestone task outcomes with existing training/sampler logs; no gate or selection."""
from __future__ import annotations
import argparse,csv,json
from pathlib import Path
ARMS=('utr_sg','drtp_sg','conservative_drtp_sg');SEEDS=(3001,3002,3003,3004,3005);MS={976:'250k',1953:'500k',2930:'750k',3907:'1m'};CONDS=('nominal','F0_44_80','T28_28_80','D120_44_120','C28_120');FAIL=CONDS[1:]
def read(p):
 with p.open(newline='',encoding='utf8') as h:return list(csv.DictReader(h))
def mean(x):return sum(x)/len(x)
def f(x):
 try:return float(x)
 except:return None
def main():
 p=argparse.ArgumentParser();p.add_argument('--r1-root',type=Path,required=True);p.add_argument('--output-root',type=Path,required=True);p.add_argument('--execute',action='store_true');a=p.parse_args()
 if not a.execute:raise SystemExit('--execute required')
 ev=a.output_root/'evaluations'/'milestones';m=json.loads((ev/'evaluation_manifest.json').read_text());summary=read(ev/'per_seed_condition_summary.csv')
 if m.get('status')!='completed' or len(summary)!=300:raise RuntimeError('incomplete forensic evaluation')
 out=a.output_root/'report';out.mkdir(parents=True,exist_ok=False);rows=[]
 for arm in ARMS:
  for seed in SEEDS:
   train=read(a.r1_root/'runs'/arm/f'seed{seed}'/'train_log.csv');sam=read(a.r1_root/'runs'/arm/f'seed{seed}'/'drtp_topology_sampler_log.csv')
   for update,label in MS.items():
    z={r['condition']:r for r in summary if r['method']==arm and int(r['train_seed'])==seed and r['milestone']==label};tw=[r for r in train if update-127<=int(r['update'])<=update];sw=[r for r in sam if update-976 < (int(r['update']) if r['update'] else 0) <= update and r['record_type']=='weight_update' and r['adapted'].lower()=='true']
    row={'method':arm,'seed':seed,'milestone':label,'update':update,'J_nominal':float(z['nominal']['J']),'J_F0':float(z['F0_44_80']['J']),'J_T28':float(z['T28_28_80']['J']),'J_D120':float(z['D120_44_120']['J']),'J_C28_120':float(z['C28_120']['J']),'J_pert_mean':mean([float(z[c]['J']) for c in FAIL]),'J_pert_worst':min(float(z[c]['J']) for c in FAIL),'collision':mean([float(z[c]['collision']) for c in FAIL]),'timeout':mean([float(z[c]['timeout']) for c in FAIL])}
    for key in ('train_avg_reward','policy_loss','value_loss','explained_variance','approx_kl','clip_fraction','entropy','grad_norm','advantage_std','actor_gradient_norm','critic_gradient_norm'):
     vals=[f(r.get(key)) for r in tw];row[key]=mean([v for v in vals if v is not None]) if any(v is not None for v in vals) else None
    row['adaptation_count']=len(sw);row['trust_activation_rate']=mean([1.0 if r['trust_region_active'].lower()=='true' else 0.0 for r in sw]) if sw else None;row['q_uniform_l1']=mean([sum(abs(float(r[f'q_{g}'])-1/6) for g in ('F0','TE','TL','DS','DL','CP')) for r in sw]) if sw else None
    rows.append(row)
 with (out/'milestone_aligned_forensic.csv').open('w',newline='',encoding='utf8') as h:w=csv.DictWriter(h,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 report=['# R1 Stage-2 milestone forensic report','',f'Raw milestone evaluation records: `{m["raw_rows"]}`. This is forensic-only: no checkpoint selection, promotion, training, continuation or algorithm change occurred.','', 'The aligned CSV contains all task endpoints and training/sampler windows. Any apparent temporal association is descriptive and cannot establish a causal mechanism.']
 (out/'R1_STAGE2_FORENSIC_REPORT.md').write_text('\n'.join(report)+'\n');(out/'stage2_manifest.json').write_text(json.dumps({'status':'complete','training_started':False,'checkpoint_selection':False,'raw_records':m['raw_rows']},indent=2)+'\n');print(json.dumps({'report':str(out/'R1_STAGE2_FORENSIC_REPORT.md'),'rows':len(rows)},indent=2))
if __name__=='__main__':main()
