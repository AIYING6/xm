"""Independent P1 trace/timing/adequacy audit for Phase2IA8."""
from __future__ import annotations
import argparse,csv,json
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results'/'development'/'phase2ia8_p1_mechanism_probe';CS=('structural_oracle','legal_observation');SEEDS=(701,702,703)
def read(p):
 with p.open(newline='',encoding='utf8') as f:return list(csv.DictReader(f))
def write(p,rows):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('w',newline='',encoding='utf8') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def ti(x):
 x=int(float(x));return None if x<0 else x
def main():
 p=argparse.ArgumentParser();p.add_argument('--out-dir',type=Path,default=OUT);a=p.parse_args();raw=read(a.out_dir/'raw_episode_metrics.csv');byid={r['development_episode_id']:r for r in raw}
 if len(raw)!=600 or len(byid)!=600:raise RuntimeError('Expected 600 unique raw rows')
 out=[];bad=[];traces=sorted((a.out_dir/'raw_timestep_chain').glob('*.csv'))
 for file in traces:
  groups=defaultdict(list)
  for r in read(file):groups[r['development_episode_id']].append(r)
  for eid,rows in groups.items():
   rows=sorted(rows,key=lambda r:int(r['timestep']));src=byid[eid];hold=0;trigger=None;active=[];loss=None;rec=None
   for r in rows:
    s=int(r['timestep']);support=float(r['chain_support_t'])>.5;hold=hold+1 if support else 0
    if trigger is None and hold>=2 and s<=220:trigger=s
    if float(r['node_failure_active'])>.5:active.append(s)
    if active and not support and loss is None:loss=s
    if loss is not None and support and rec is None:rec=s
   failure=active[0] if active else None;checks={
    'eligibility':(trigger is not None)==(float(src['support_eligible'])>.5),
    'failure_start':failure==ti(src['t_failure']),
    'trigger_to_failure':(failure==trigger+1) if trigger is not None else failure is None,
    'failure_duration':(len(active)<=80 and active==list(range(failure,failure+len(active)))) if failure is not None else True,
    'loss':loss==ti(src['t_loss']),'recovery':rec==ti(src['t_recovery']),'event':(rec is not None)==(float(src['event'])>.5)}
   if not all(checks.values()):bad.append({'development_episode_id':eid,'controller':src['controller'],'checks':json.dumps(checks)})
   out.append({'development_episode_id':eid,'controller':src['controller'],'seed':src['seed'],'support_trigger_step':'' if trigger is None else trigger,'t_failure':'' if failure is None else failure,'t_loss':'' if loss is None else loss,'t_recovery':'' if rec is None else rec,'event':float(rec is not None)})
 if len(out)!=len(raw):raise RuntimeError('Trace coverage mismatch')
 gate={'protocol':'PHASE2IA8-PSR-V1','raw_rows':len(raw),'trace_rows':len(out),'trace_files':len(traces),'mismatch_count':len(bad),'controllers':{}}
 summary=[]
 for c in CS:
  rows=[r for r in raw if r['controller']==c];counts={str(s):sum(float(r['support_eligible'])>.5 for r in rows if r['seed']==str(s)) for s in SEEDS};loss=sum(float(r['support_eligible'])>.5 and float(r['support_lost_after_failure'])>.5 for r in rows);cond={'raw_trace_complete':len(out)==len(raw) and len(traces)==6,'timing_endpoint_consistent':not bad,'at_least_40_eligible':sum(counts.values())>=40,'at_least_two_seeds':sum(v>0 for v in counts.values())>=2,'two_seeds_at_least_10':sum(v>=10 for v in counts.values())>=2,'at_least_one_eligible_loss':loss>=1};gate['controllers'][c]={'pass':all(cond.values()),'eligible_by_seed':counts,'eligible_total':sum(counts.values()),'eligible_loss_total':loss,'conditions':cond};summary.append({'controller':c,'episodes':len(rows),'seed701':counts['701'],'seed702':counts['702'],'seed703':counts['703'],'eligible_total':sum(counts.values()),'eligible_loss_total':loss,'P1_pass':all(cond.values())})
 gate['overall_pass']=all(v['pass'] for v in gate['controllers'].values());write(a.out_dir/'summaries'/'P1_trace_reconstruction.csv',out);write(a.out_dir/'summaries'/'P1_summary.csv',summary)
 if bad:write(a.out_dir/'summaries'/'P1_mismatches.csv',bad)
 (a.out_dir/'summaries'/'P1_GATE.json').write_text(json.dumps(gate,indent=2)+'\n',encoding='utf8');print(json.dumps(gate,indent=2))
if __name__=='__main__':main()
