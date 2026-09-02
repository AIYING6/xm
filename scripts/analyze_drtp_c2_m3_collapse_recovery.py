"""Read completed M3 archive only; no environment, model, or training call."""
from __future__ import annotations
import argparse, csv, io, json, math, tarfile
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
FREEZE=ROOT/'configs/drtp_c2_m3_collapse_recovery_freeze.json'
UPDATES={'125k':488,'250k':976,'375k':1464,'500k':1953}
GROUP_FIELDS=('td_residual_abs_q90','raw_advantage_std','clipped_surrogate_mean','actor_loss_mean','entropy_bonus_mean','actor_gradient_norm')

def avg(x): return sum(x)/len(x) if x else math.nan
def sgn(x): return 'positive' if x>0 else 'negative' if x<0 else 'zero'
def arm_seed(name):
    if '/runs/' not in name or '/seed' not in name: return None
    a,tail=name.split('/runs/',1)[1].split('/seed',1); seed,file=tail.split('/',1)
    return a,int(seed),file
def bounds(a,b):
    lo,hi=UPDATES[a]+1,UPDATES[b]
    return lo,(lo+hi)//2
def write_csv(path,records):
    with path.open('w',newline='',encoding='utf-8') as h:
        w=csv.DictWriter(h,fieldnames=list(records[0])); w.writeheader(); w.writerows(records)

def main():
    p=argparse.ArgumentParser(); p.add_argument('--archive',type=Path,required=True); p.add_argument('--output-dir',type=Path,required=True); p.add_argument('--execute',action='store_true'); a=p.parse_args()
    if not a.execute: raise SystemExit('--execute required')
    if a.output_dir.exists(): raise FileExistsError(a.output_dir)
    f=json.loads(FREEZE.read_text(encoding='utf-8')); windows=f['fixed_transition_windows']; by_seed=defaultdict(list)
    for w in windows: by_seed[w['seed']].append(w)
    groups=defaultdict(lambda:defaultdict(list)); conflicts=defaultdict(list); role=defaultdict(lambda:defaultdict(list)); perf=[]
    with tarfile.open(a.archive,'r:gz') as z:
        for member in z:
            if not member.isfile(): continue
            name=member.name
            if name.endswith('evaluations/m3_fixed_milestones/per_seed_condition_summary.csv'):
                perf=list(csv.DictReader(io.TextIOWrapper(z.extractfile(member),encoding='utf-8'))); continue
            parsed=arm_seed(name)
            if not parsed: continue
            arm,seed,file=parsed
            if seed not in by_seed: continue
            src=z.extractfile(member)
            if src is None: continue
            if file=='group_credit_telemetry.csv':
                for r in csv.DictReader(io.TextIOWrapper(src,encoding='utf-8')):
                    if r['status']!='OK': continue
                    for w in by_seed[seed]:
                        lo,hi=bounds(w['from'],w['to'])
                        if lo<=int(r['update'])<=hi:
                            for k in GROUP_FIELDS:
                                if r[k]: groups[(arm,seed,w['from'],w['to'])][k].append(float(r[k]))
            elif file=='group_credit_gradient_conflicts.csv':
                for r in csv.DictReader(io.TextIOWrapper(src,encoding='utf-8')):
                    if r['status']!='OK': continue
                    for w in by_seed[seed]:
                        lo,hi=bounds(w['from'],w['to'])
                        if lo<=int(r['update'])<=hi: conflicts[(arm,seed,w['from'],w['to'])].append(float(r['actor_gradient_conflict'].lower()=='true'))
            elif file=='failure_telemetry/failure_event_window.jsonl':
                for raw in io.TextIOWrapper(src,encoding='utf-8'):
                    r=json.loads(raw)
                    for w in by_seed[seed]:
                        lo,hi=bounds(w['from'],w['to'])
                        if lo<=int(r['update'])<=hi:
                            q=role[(arm,seed,w['from'],w['to'])]
                            q['policy_entropy'].append(float(r['policy_entropy']))
                            q['support_chain'].append(float(r['task_support_state']['chain_support']))
                            q['cache_age'].append(float(r['cache_freshness']['mean_age']))
    if not perf: raise RuntimeError('missing fixed milestone summary')
    def score(arm,seed,label):
        z=[r for r in perf if r['arm']==arm and int(r['seed'])==seed and r['checkpoint_label']==label]
        d={r['condition']:r for r in z}; failures=[float(r['J']) for k,r in d.items() if k!='nominal']
        return avg(failures)
    ledger=[]; matrix=[]
    metrics=GROUP_FIELDS+('actor_conflict_rate','policy_entropy','support_chain','cache_age')
    for w in windows:
        seed,start,end=w['seed'],w['from'],w['to']; lo,hi=bounds(start,end); row=dict(w,precursor_start=lo,precursor_end=hi)
        base0,base1=score('utr_sg',seed,start),score('utr_sg',seed,end)
        cand0,cand1=score('group_weighted_utr_sg',seed,start),score('group_weighted_utr_sg',seed,end)
        row.update(start_delta=cand0-base0,end_delta=cand1-base1,transition_delta=(cand1-base1)-(cand0-base0))
        for arm in ('utr_sg','group_weighted_utr_sg'):
            k=(arm,seed,start,end)
            for m in GROUP_FIELDS: row[arm+'_'+m]=avg(groups[k][m])
            row[arm+'_actor_conflict_rate']=avg(conflicts[k])
            for m in ('policy_entropy','support_chain','cache_age'): row[arm+'_'+m]=avg(role[k][m])
        for m in metrics:
            delta=row['group_weighted_utr_sg_'+m]-row['utr_sg_'+m]; row['weighted_minus_utr_'+m]=delta
            matrix.append({'seed':seed,'cohort':w['cohort'],'kind':w['kind'],'from':start,'to':end,'metric':m,'precursor_window':str(lo)+'-'+str(hi),'signal_weighted_minus_utr':delta,'outcome_transition_delta':row['transition_delta'],'signal_direction':sgn(delta),'outcome_direction':sgn(row['transition_delta']),'precedence_observed':True,'cross_cohort_repeated':False})
        ledger.append(row)
    a.output_dir.mkdir(parents=True); write_csv(a.output_dir/'M3_TRANSITION_LEDGER.csv',ledger); write_csv(a.output_dir/'M3_TEMPORAL_PRECEDENCE_MATRIX.csv',matrix)
    collapse=[x for x in ledger if x['kind']=='collapse']; recovery=[x for x in ledger if x['kind']=='recovery']
    def brief(items): return '\n'.join('- seed {}: {:+.2f} → {:+.2f}; transition {:+.2f}'.format(x['seed'],x['start_delta'],x['end_delta'],x['transition_delta']) for x in items)+'\n'
    (a.output_dir/'M3_COLLAPSE_WINDOWS.md').write_text('# Fixed collapse windows\n\n'+brief(collapse),encoding='utf-8')
    (a.output_dir/'M3_RECOVERY_WINDOWS.md').write_text('# Fixed recovery windows\n\n'+brief(recovery),encoding='utf-8')
    for file,title,ms in [('M3_GRADIENT_CONFLICT_TEMPORAL_ANALYSIS.md','Gradient/conflict',('actor_gradient_norm','actor_conflict_rate')),('M3_ADVANTAGE_CREDIT_TEMPORAL_ANALYSIS.md','Advantage/credit',('td_residual_abs_q90','raw_advantage_std','clipped_surrogate_mean','actor_loss_mean')),('M3_ROLE_BEHAVIOR_TEMPORAL_ANALYSIS.md','Role behavior',('policy_entropy','support_chain','cache_age'))]:
        lines=['# '+title+' temporal analysis','', 'All values are weighted-minus-UTR over the frozen precursor window.']
        for m in ms: lines.append('- {}: collapse [{}]; recovery [{}].'.format(m,', '.join('{}={:+.4f}'.format(x['seed'],x['weighted_minus_utr_'+m]) for x in collapse),', '.join('{}={:+.4f}'.format(x['seed'],x['weighted_minus_utr_'+m]) for x in recovery)))
        (a.output_dir/file).write_text('\n'.join(lines)+'\n',encoding='utf-8')
    reversals=0
    for w in windows:
        values=[score('group_weighted_utr_sg',w['seed'],x)-score('utr_sg',w['seed'],x) for x in UPDATES]
        reversals+=int(any(x*y<0 for x,y in zip(values,values[1:])))
    horizon='HORIZON_INSUFFICIENT' if reversals==len(windows) else 'HORIZON_SUFFICIENT'
    decision={'protocol':f['protocol'],'mechanism_verdict':'M3_NO_ACTIONABLE_MECHANISM','horizon_verdict':horizon,'fixed_collapse_windows':len(collapse),'fixed_recovery_windows':len(recovery),'cross_cohort_same_transition_class_available':False,'reversal_count':reversals,'total_fixed_windows':len(windows),'mechanism_declared':False,'algorithm_modification_authorized':False,'automatic_extension_authorized':False}
    (a.output_dir/'M3_FINAL_MECHANISM_VERDICT.json').write_text(json.dumps(decision,indent=2)+'\n',encoding='utf-8')
    (a.output_dir/'M3_FINAL_MECHANISM_VERDICT.md').write_text('# M3 final mechanism verdict\n\n`M3_NO_ACTIONABLE_MECHANISM`\n\nCollapse is frozen in Cohort B and recovery in Cohort A; this cannot establish the required cross-cohort repeated precursor. No intervention is authorized.\n',encoding='utf-8')
    (a.output_dir/'M3_HORIZON_SUFFICIENCY.md').write_text('# M3 horizon sufficiency\n\n`'+horizon+'`\n\n{}/{} pre-specified transitions reverse sign across the fixed milestones. Any 500k→1M continuation needs a new frozen contract and explicit authorization.\n'.format(reversals,len(windows)),encoding='utf-8')
    (a.output_dir/'M3_COLLAPSE_RECOVERY_CONTRACT.md').write_text((ROOT/'docs/drtp_c2_m3_collapse_recovery_20260902/M3_COLLAPSE_RECOVERY_CONTRACT.md').read_text(encoding='utf-8'),encoding='utf-8')
    print(json.dumps(decision,indent=2))
if __name__=='__main__': main()
