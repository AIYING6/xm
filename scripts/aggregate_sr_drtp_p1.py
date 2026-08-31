"""Frozen, seed-level SR-DRTP P1 matched-shadow analysis."""
from __future__ import annotations
import argparse,csv,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; FREEZE=ROOT/'configs'/'sr_drtp_p1_shadow_preparation_freeze.json'
def mean(x): return sum(x)/len(x) if x else 0.0
def main():
 p=argparse.ArgumentParser();p.add_argument('--output-root',type=Path,required=True);p.add_argument('--execute',action='store_true');a=p.parse_args()
 if not a.execute: raise SystemExit('--execute required')
 f=json.loads(FREEZE.read_text()); out=a.output_root; gate=out/'diagnostics'/'sr_drtp_p1';
 if gate.exists(): raise FileExistsError(gate)
 rows=[]
 for cohort,seeds in f['cohorts'].items():
  for seed in seeds:
   d=out/'runs'/'drtp_sg'/f'seed{seed}'; signals={int(r['update']):r for r in csv.DictReader((d/'sr_drtp_p1_signal'/'pp_disagreement.csv').open())}
   for u,s in signals.items():
    m={b:json.loads((d/'matched_shadows'/f'u{u:04d}'/b/'shadow_manifest.json').read_text()) for b in 'ABC'}
    if any(v['status']!='completed' for v in m.values()): raise RuntimeError('incomplete shadow')
    for b in 'BC': rows.append({'seed':seed,'cohort':cohort,'update':u,'branch':b,'high_risk':s['high_risk']=='True','pp_disagreement':s['pp_online_disagreement']=='True','utility':float(m[b]['outcome_mean_training_reward'])-float(m['A']['outcome_mean_training_reward'])})
 gate.mkdir(parents=True); fields=list(rows[0]);
 with (gate/'SR_DRTP_P1_EVENT_LEDGER.csv').open('w',newline='') as h: w=csv.DictWriter(h,fieldnames=fields);w.writeheader();w.writerows(rows)
 margin=f['analysis_constants']['practical_utility_margin']; fp=f['analysis_constants']['max_low_risk_harm_rate']; summaries={}; viable=[]; contradictory=False
 for cohort in 'AB':
  report=[]
  for b in 'BC':
   r=[x for x in rows if x['cohort']==cohort and x['branch']==b]; hi=[x for x in r if x['high_risk']];lo=[x for x in r if not x['high_risk']]; harm=mean([x['utility']<=-margin for x in lo]) if lo else 0.0; delta=mean([x['utility'] for x in hi])-mean([x['utility'] for x in lo]); seed_hi=len(set(x['seed'] for x in hi)); ok=len(hi)>=f['analysis_constants']['minimum_high_risk_events_per_cohort'] and seed_hi>=f['analysis_constants']['minimum_high_risk_seeds_per_cohort'] and delta>=margin and harm<=fp
   report.append({'branch':b,'high_events':len(hi),'high_seeds':seed_hi,'high_mean_utility':mean([x['utility'] for x in hi]),'low_mean_utility':mean([x['utility'] for x in lo]),'conditional_delta':delta,'low_risk_harm_rate':harm,'pass':ok}); contradictory|=bool(lo and harm>fp)
  summaries[cohort]=report; (gate/f'SR_DRTP_P1_COHORT_{cohort}_SUMMARY.md').write_text('# SR-DRTP P1 Cohort '+cohort+'\n\n```json\n'+json.dumps(report,indent=2)+'\n```\n')
 for b in 'BC':
  if all(next(x for x in summaries[c] if x['branch']==b)['pass'] for c in 'AB'): viable.append(b)
 enough=all(any(x['high_events']>=f['analysis_constants']['minimum_high_risk_events_per_cohort'] for x in summaries[c]) for c in 'AB')
 verdict='P1_GATE_SIGNAL_PASS' if viable else ('P1_GATE_NO_GO' if contradictory or enough else 'P1_INCONCLUSIVE')
 analysis={'verdict':verdict,'viable_branches':viable,'cohorts':summaries,'pooled_event_analysis_descriptive_only':True,'automatic_continuation_authorized':False}
 (gate/'SR_DRTP_P1_GATE_ANALYSIS.md').write_text('# SR-DRTP P1 gate analysis\n\n```json\n'+json.dumps(analysis,indent=2)+'\n```\n')
 (gate/'SR_DRTP_P1_FINAL_VERDICT.md').write_text('# SR-DRTP P1 final verdict\n\n`'+verdict+'`\n')
 (gate/'SR_DRTP_P1_RESULTS.md').write_text('# SR-DRTP P1 results\n\n'+json.dumps({'events':len(rows),'verdict':verdict},indent=2)+'\n')
 print(json.dumps({'verdict':verdict,'gate':str(gate)},indent=2))
if __name__=='__main__':main()
