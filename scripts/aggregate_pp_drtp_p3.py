from __future__ import annotations
import argparse,csv,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];ARMS=('utr_sg','drtp_sg','pp_drtp_sg');SEEDS=(3401,3402,3403);CONDS=('nominal','F0_44_80','T28_28_80','D120_44_120','C28_120');EPS=7.874919837916801
def main():
 p=argparse.ArgumentParser();p.add_argument('--output-root',type=Path,required=True);p.add_argument('--execute',action='store_true');a=p.parse_args();
 if not a.execute:raise SystemExit('--execute required')
 rows=list(csv.DictReader((a.output_root/'evaluations'/'final_05m'/'condition_summary.csv').open()));r={}
 for x in rows:r.setdefault((x['method'],int(x['train_seed'])),{})[x['condition']]=x
 def cell(m,s):
  x=r[m,s];j=lambda c:float(x[c]['J']);return {'nominal':j('nominal'),'f0':j('F0_44_80'),'mean':sum(j(c) for c in CONDS[1:])/4,'worst':min(j(c) for c in CONDS[1:]),'collision':sum(float(x[c]['collision']) for c in CONDS[1:])/4,'timeout':sum(float(x[c]['timeout']) for c in CONDS[1:])/4,'cv':max(float(x[c]['constraint_violation']) for c in CONDS[1:])}
 out=[]
 for s in SEEDS:
  u,d,q=cell('utr_sg',s),cell('drtp_sg',s),cell('pp_drtp_sg',s);out.append({'seed':s,'G_original':d['mean']-u['mean'],'G_pp':q['mean']-u['mean'],'pp_minus_original':q['mean']-d['mean'],'timeout_delta':q['timeout']-u['timeout'],'collision_delta':q['collision']-u['collision'],'constraint_violation':q['cv'],'upper':d['mean']-u['mean']>EPS})
 go=[x['G_original'] for x in out];gp=[x['G_pp'] for x in out];disp=lambda x:(max(x)-min(x),statistics.stdev(x),statistics.median(abs(v-statistics.median(x)) for v in x))
 criteria={'advantage_retention':sum(x['pp_minus_original'] for x in out)/3>=-EPS,'downside_protection':min(gp)-min(go)>EPS,'seed_reliability':all(a<b for a,b in zip(disp(gp),disp(go))),'upper_tail_retention':any(x['upper'] for x in out) and all((not x['upper']) or x['pp_minus_original']>=-EPS for x in out),'safety':all(x['timeout_delta']<=.1 and x['collision_delta']<=.1 and x['constraint_violation']==0 for x in out)}
 decision='PP_PILOT_EARLY_GO' if all(criteria.values()) else 'PP_PILOT_NO_GO';rd=a.output_root/'diagnostics'/'pp_p3_gate';rd.mkdir(parents=True,exist_ok=False)
 (rd/'PP_P3_GATE_DECISION.json').write_text(json.dumps({'decision':decision,'criteria':criteria,'seed_results':out,'original_dispersion':disp(go),'pp_dispersion':disp(gp),'automatic_continuation_started':False},indent=2)+'\n');(rd/'PP_P3_GATE_REPORT.md').write_text(f'# PP-DRTP P3 gate\n\n**Decision:** `{decision}`.\n\n```json\n'+json.dumps(criteria,indent=2)+'\n```\n')
if __name__=='__main__':main()
