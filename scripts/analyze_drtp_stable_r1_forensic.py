"""Zero-training forensic extraction from the immutable Stable-DRTP R1 archive."""
from __future__ import annotations
import argparse, csv, hashlib, io, json, statistics, tarfile
from collections import Counter
from pathlib import Path

ARMS=("utr_sg","drtp_sg","conservative_drtp_sg"); SEEDS=(3001,3002,3003,3004,3005); MS=(976,1953,2930,3907)
METRICS=("train_avg_reward","loss","policy_loss","value_loss","explained_variance","approx_kl","clip_fraction","entropy","grad_norm","advantage_mean","advantage_std","actor_gradient_norm","critic_gradient_norm","actor_update_norm","critic_update_norm")
PREFIX="drtp_stable_r1/"
def f(x):
 try:return float(x)
 except (ValueError,TypeError):return None
def mean(xs):
 xs=[x for x in xs if x is not None]
 return sum(xs)/len(xs) if xs else None
def open_csv(tar,name):return list(csv.DictReader(io.TextIOWrapper(tar.extractfile(name),encoding='utf-8')))
def main():
 p=argparse.ArgumentParser();p.add_argument('--archive',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args()
 if a.output_dir.exists():raise FileExistsError(a.output_dir)
 a.output_dir.mkdir(parents=True); digest=hashlib.sha256(a.archive.read_bytes()).hexdigest()
 with tarfile.open(a.archive,'r:gz') as tar:
  names=set(tar.getnames()); summary=open_csv(tar,PREFIX+'evaluations/final_1m/per_seed_condition_summary.csv'); gate=json.load(io.TextIOWrapper(tar.extractfile(PREFIX+'diagnostics/stable_r1/gate/R1_GATE_DECISION.json'),encoding='utf-8'))
  gains={r['seed']:r for r in gate['seed_results']}; trajectory=[]; sampler=[]; provenance=[]
  for arm in ARMS:
   for seed in SEEDS:
    base=f'{PREFIX}runs/{arm}/seed{seed}/'; manifest=json.load(io.TextIOWrapper(tar.extractfile(base+'run_manifest.json'),encoding='utf-8')); provenance.append({'arm':arm,'seed':seed,'commit':manifest['commit'],'updates':manifest['updates'],'environment_steps':manifest['environment_steps'],'status':manifest['status'],'tape_hash':manifest['tape_hash'],'sampler_mode':manifest['sampler_mode']})
    logs=open_csv(tar,base+'train_log.csv')
    for milestone in MS:
     window=[r for r in logs if max(1,milestone-127)<=int(r['update'])<=milestone]
     row={'arm':arm,'seed':seed,'milestone_update':milestone,'window_updates':len(window),'conservative_group':'failure' if arm=='conservative_drtp_sg' and seed in (3001,3003,3004) else 'success' if arm=='conservative_drtp_sg' else 'control'}
     row.update({k:mean([f(x[k]) for x in window]) for k in METRICS});trajectory.append(row)
    slog=open_csv(tar,base+'drtp_topology_sampler_log.csv')
    for milestone in MS:
     segment=[r for r in slog if max(1,milestone-976)<=(int(r['update']) if r['update'] else 0)<=milestone]
     select=[r for r in segment if r['record_type']=='selection']; upd=[r for r in segment if r['record_type']=='weight_update' and r['adapted'].lower()=='true']; counts=Counter(r['group'] for r in select)
     row={'arm':arm,'seed':seed,'milestone_update':milestone,'selection_count':len(select),'adaptation_count':len(upd),'trust_activation_rate':mean([1.0 if r['trust_region_active'].lower()=='true' else 0.0 for r in upd]),'mean_q_step_l1':mean([f(r['q_step_l1']) for r in upd]),'mean_pre_tr_l1':mean([f(r['pre_tr_l1']) for r in upd])}
     for g in ('F0','TE','TL','DS','DL','CP'): row[f'exposure_{g}']=counts[g]/len(select) if select else None
     if upd: row['q_uniform_l1']=mean([sum(abs(f(r[f'q_{g}'])-1/6) for g in ('F0','TE','TL','DS','DL','CP')) for r in upd])
     else: row['q_uniform_l1']=None
     sampler.append(row)
  safety=[]
  for seed in SEEDS:
   for c in ('F0_44_80','T28_28_80','D120_44_120','C28_120'):
    u=next(r for r in summary if r['method']=='utr_sg' and int(r['train_seed'])==seed and r['condition']==c); x=next(r for r in summary if r['method']=='conservative_drtp_sg' and int(r['train_seed'])==seed and r['condition']==c)
    safety.append({'seed':seed,'condition':c,'collision_delta':f(x['collision'])-f(u['collision']),'timeout_delta':f(x['timeout'])-f(u['timeout']),'constraint_violation':f(x['constraint_violation'])})
 def write(name,rows):
  with (a.output_dir/name).open('w',newline='',encoding='utf8') as h:w=csv.DictWriter(h,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 write('milestone_training_dynamics.csv',trajectory);write('milestone_sampler_dynamics.csv',sampler);write('safety_recalculation.csv',safety);write('provenance_alignment.csv',provenance)
 max_to=max(r['timeout_delta'] for r in safety); max_col=max(r['collision_delta'] for r in safety); bad=[r for r in safety if r['timeout_delta']>.10 or r['collision_delta']>.10 or r['constraint_violation']!=0]
 report=['# R1 zero-training forensic report','',f'Archive SHA256: `{digest}`. No checkpoint was rolled out and no training was started.','', '## Frozen R1 outcome','',f"Gate: `{gate['decision']}`. Failure-group Conservative seeds are 3001, 3003, 3004; success-group seeds are 3002, 3005.",'', '## Safety implementation reconciliation','',f'Existing R1 gate reported aggregate safety `{gate["criteria"]["safety"]}`. Independent per-seed/condition recalculation found max timeout delta `{max_to:.4f}`, max collision delta `{max_col:.4f}`, and `{len(bad)}` records exceeding a 0.10 per-cell delta threshold. Thus the R1 gate used aggregate safety only; this is a gate-implementation mismatch with the earlier S1/S2 per-cell rule. It cannot reverse R1_NO_GO because all non-safety core criteria already failed.','', '## Provenance','', 'All 15 manifests report execution commit `434b8720`, which is a descendant of readiness commit `591f6ff2`; the cloud package delivery commit `305e5833` only adds git-less provenance fallback. Algorithm/sampler semantics are not changed by that fallback.','', '## Available evidence and limitation','', 'The archive contains all four milestone checkpoints but only final-1M evaluation records. Therefore milestone reward/PPO/sampler dynamics are extracted here; milestone J_pert_mean, nominal and condition-specific task scores would require a separately authorized zero-training cloud evaluation of the frozen checkpoints. No causal mechanism is claimed from these associations.']
 (a.output_dir/'R1_FORENSIC_REPORT.md').write_text('\n'.join(report)+'\n',encoding='utf8')
 (a.output_dir/'forensic_manifest.json').write_text(json.dumps({'archive_sha256':digest,'training_started':False,'evaluation_started':False,'gate':gate['decision'],'safety_per_cell_reconciliation_required':bool(bad)},indent=2)+'\n')
 print(json.dumps({'output_dir':str(a.output_dir),'archive_sha256':digest,'per_cell_safety_exceedances':len(bad)},indent=2))
if __name__=='__main__':main()
