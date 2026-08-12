"""Independent classification audit for Phase2IA9 trace-only replay."""
from __future__ import annotations
import argparse,csv,json
from collections import Counter,defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results'/'development'/'phase2ia9_path_replay'
def read(p):
 with p.open(newline='',encoding='utf8') as f:return list(csv.DictReader(f))
def write(p,rows):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('w',newline='',encoding='utf8') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def classify(r):
 direct=float(r['attacker_direct_target_information_t'])>.5;cache=float(r['attacker_fresh_cache_information_t'])>.5;relay_required=float(r['attacker_support_path_relay1_required_t'])>.5;relay_any=float(r['attacker_cache_path_includes_relay1_t'])>.5
 if direct:return 'DIRECT_BYPASS'
 if relay_required:return 'RELAY1_REQUIRED_CACHE'
 if cache and not relay_any:return 'CACHE_BYPASS_NO_RELAY1'
 if cache:return 'MIXED_OR_INDETERMINATE'
 return 'NO_ATTACKER_INFORMATION'
def main():
 p=argparse.ArgumentParser();p.add_argument('--out-dir',type=Path,default=OUT);a=p.parse_args();raw=read(a.out_dir/'raw_episode_metrics.csv');byid={r['development_episode_id']:r for r in raw}
 if len(raw)!=600 or len(byid)!=600:raise RuntimeError('Expected 600 raw rows')
 out=[];bad=[];files=sorted((a.out_dir/'raw_timestep_chain').glob('*.csv'))
 for f in files:
  groups=defaultdict(list)
  for r in read(f):groups[r['development_episode_id']].append(r)
  for eid,rows in groups.items():
   rows=sorted(rows,key=lambda x:int(x['timestep']));src=byid[eid];trig=next((r for r in rows if int(r['timestep'])==int(float(src['support_trigger_step']))),None);active=[r for r in rows if float(r['node_failure_active'])>.5]
   if trig is None:bad.append({'development_episode_id':eid,'issue':'missing_trigger'});continue
   if active and int(active[0]['timestep'])!=int(float(src['t_failure'])):bad.append({'development_episode_id':eid,'issue':'failure_start_mismatch'})
   for phase,r in [('trigger',trig)]+[('failure_active',x) for x in active]:out.append({'development_episode_id':eid,'controller':src['controller'],'seed':src['seed'],'phase':phase,'timestep':r['timestep'],'classification':classify(r),'chain_support_t':r['chain_support_t'],'direct':r['attacker_direct_target_information_t'],'cache':r['attacker_fresh_cache_information_t'],'cache_paths':r['attacker_cache_paths_t'],'relay1_required':r['attacker_support_path_relay1_required_t']})
 if len({r['development_episode_id'] for r in out})!=600:raise RuntimeError('Trace episode coverage failure')
 counts=Counter((r['controller'],r['phase'],r['classification']) for r in out);summary=[]
 for (c,phase,cl),n in sorted(counts.items()):summary.append({'controller':c,'phase':phase,'classification':cl,'n_rows':n})
 status={'raw_rows':len(raw),'trace_files':len(files),'trace_episode_coverage':len({r['development_episode_id'] for r in out}),'mismatch_count':len(bad),'status':'PASS' if not bad and len(files)==6 else 'FAIL'}
 write(a.out_dir/'summaries'/'path_classification_rows.csv',out);write(a.out_dir/'summaries'/'path_classification_summary.csv',summary)
 if bad:write(a.out_dir/'summaries'/'path_audit_mismatches.csv',bad)
 (a.out_dir/'summaries'/'PATH_AUDIT.json').write_text(json.dumps(status,indent=2)+'\n');print(json.dumps(status,indent=2));print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
