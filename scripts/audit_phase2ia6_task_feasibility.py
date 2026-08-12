"""Independent Gate F reconstruction for Phase2IA6 task-feasibility probes."""
from __future__ import annotations
import argparse,csv,json
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results'/'development'/'phase2ia6_task_feasibility'
CONTROLLERS=('structural_oracle','legal_observation'); SEEDS=(601,602,603)
def read(p):
    with p.open(newline='',encoding='utf8') as f:return list(csv.DictReader(f))
def write(p,rows):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('w',newline='',encoding='utf8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def main():
 p=argparse.ArgumentParser();p.add_argument('--out-dir',type=Path,default=OUT);a=p.parse_args()
 raw=read(a.out_dir/'raw_episode_metrics.csv'); byid={r['development_episode_id']:r for r in raw}
 if len(raw)!=600 or len(byid)!=600:raise RuntimeError('Expected 600 unique raw episodes')
 rows=[]; mismatches=[]; traces=sorted((a.out_dir/'raw_timestep_chain').glob('*.csv'))
 for trace in traces:
  grouped=defaultdict(list)
  for r in read(trace):grouped[r['development_episode_id']].append(r)
  for eid,items in grouped.items():
   items=sorted(items,key=lambda x:int(x['timestep'])); src=byid[eid]; hold=0; first=-1
   for item in items:
    hold=hold+1 if float(item['chain_closed'])>.5 else 0
    if first<0 and hold>=4 and int(item['timestep'])<=220:first=int(item['timestep'])
   reconstructed=float(first>=0)
   if reconstructed != (float(src['feasible_before_cap'])>.5) or first != int(float(src['first_four_step_chain'])): mismatches.append({'development_episode_id':eid,'controller':src['controller'],'raw_feasible':src['feasible_before_cap'],'trace_first':first})
   rows.append({'development_episode_id':eid,'controller':src['controller'],'seed':src['seed'],'trace_first_four_step_chain':first,'feasible_before_cap':reconstructed})
 if len(rows)!=len(raw):raise RuntimeError('Trace coverage mismatch')
 summary=[];gate={'protocol':'PHASE2IA6-TF-V1','raw_rows':len(raw),'trace_rows':len(rows),'trace_files':len(traces),'mismatch_count':len(mismatches),'controllers':{}}
 for c in CONTROLLERS:
  r=[x for x in rows if x['controller']==c]; counts={str(s):sum(x['feasible_before_cap'] for x in r if x['seed']==str(s)) for s in SEEDS}
  cond={'at_least_40_total':sum(counts.values())>=40,'at_least_two_seeds':sum(x>0 for x in counts.values())>=2,'two_seeds_at_least_10':sum(x>=10 for x in counts.values())>=2,'trace_consistency':not mismatches}
  gate['controllers'][c]={'pass':all(cond.values()),'counts':counts,'total':sum(counts.values()),'conditions':cond}
  summary.append({'controller':c,'episodes':len(r),'seed601':counts['601'],'seed602':counts['602'],'seed603':counts['603'],'total':sum(counts.values()),'gate_F_pass':all(cond.values())})
 gate['structural_pass']=gate['controllers']['structural_oracle']['pass'];gate['legal_pass']=gate['controllers']['legal_observation']['pass'];gate['overall_pass']=gate['structural_pass'] and gate['legal_pass']
 write(a.out_dir/'summaries'/'gate_f_trace_reconstruction.csv',rows);write(a.out_dir/'summaries'/'gate_f_summary.csv',summary)
 if mismatches:write(a.out_dir/'summaries'/'gate_f_mismatches.csv',mismatches)
 (a.out_dir/'summaries'/'GATE_F.json').write_text(json.dumps(gate,indent=2)+'\n',encoding='utf8');print(json.dumps(gate,indent=2))
if __name__=='__main__':main()
