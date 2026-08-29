"""Frozen R1 gate; aggregates completed 1M records only."""
from __future__ import annotations
import argparse,csv,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; ARMS=('utr_sg','drtp_sg','conservative_drtp_sg');SEEDS=(3001,3002,3003,3004,3005);CONDS=('nominal','F0_44_80','T28_28_80','D120_44_120','C28_120');FAIL=CONDS[1:]
def read(p):
 with p.open(newline='',encoding='utf8') as h:return list(csv.DictReader(h))
def mean(x):return sum(x)/len(x)
def disp(x):return {'range':max(x)-min(x),'sample_sd':statistics.stdev(x),'iqr':statistics.quantiles(x,n=4)[2]-statistics.quantiles(x,n=4)[0],'mad':statistics.median(abs(v-statistics.median(x)) for v in x)}
def main():
 p=argparse.ArgumentParser();p.add_argument('--output-root',type=Path,required=True);p.add_argument('--technical-audit',type=Path,required=True);p.add_argument('--execute',action='store_true');a=p.parse_args()
 if not a.execute:raise SystemExit('--execute required')
 audit=json.loads(a.technical_audit.read_text());
 if audit.get('status')!='PASS':raise RuntimeError('R1_TECHNICAL_NOT_READY')
 tape=json.loads((ROOT/'configs/drtp_stable_r1_development_tape.json').read_text()); freeze=json.loads((ROOT/'configs/drtp_stabilization_s0_freeze.json').read_text()); ev=a.output_root/'evaluations'/'final_1m';mani=json.loads((ev/'evaluation_manifest.json').read_text()); raw,summary=read(ev/'raw_episode_metrics.csv'),read(ev/'per_seed_condition_summary.csv')
 if mani.get('status')!='completed' or len(raw)!=7500 or mani.get('tape_hash')!=tape['tape_hash']:raise RuntimeError('R1 invalid evaluation')
 def m(arm,seed):
  z={r['condition']:r for r in summary if r['method']==arm and int(r['train_seed'])==seed}; n=lambda c,k:float(z[c][k]); return {'j':mean([n(c,'J') for c in FAIL]),'f0':n('F0_44_80','J'),'worst':min(n(c,'J') for c in FAIL),'collision':mean([n(c,'collision') for c in FAIL]),'timeout':mean([n(c,'timeout') for c in FAIL]),'cv':max(n(c,'constraint_violation') for c in FAIL)}
 cells={a0:{s:m(a0,s) for s in SEEDS} for a0 in ARMS}; cat=lambda x,u:((x['f0']/u['f0']<.7 and x['worst']/u['worst']<.85)or(x['worst']/u['worst']<.7 and x['f0']/u['f0']<.85)or(x['timeout']-u['timeout']>.2 and(x['f0']/u['f0']<.85 or x['worst']/u['worst']<.85)))
 rows=[]
 for s in SEEDS:
  u,o,c=cells['utr_sg'][s],cells['drtp_sg'][s],cells['conservative_drtp_sg'][s];rows.append({'seed':s,'G_original':o['j']-u['j'],'G_conservative':c['j']-u['j'],'conservative_minus_original':c['j']-o['j'],'original_catastrophic':cat(o,u),'conservative_catastrophic':cat(c,u),'conservative_collision_minus_utr':c['collision']-u['collision'],'conservative_timeout_minus_utr':c['timeout']-u['timeout']})
 eps=float(freeze['epsilon_J']);g0=[r['G_original'] for r in rows];gc=[r['G_conservative'] for r in rows];d0,dc=disp(g0),disp(gc);upper=[r for r in rows if r['G_original']>eps]
 criteria={'advantage_retention':mean([cells['conservative_drtp_sg'][s]['j'] for s in SEEDS])>=mean([cells['drtp_sg'][s]['j'] for s in SEEDS])-eps,'downside_protection':min(gc)-min(g0)>eps and sum(r['conservative_catastrophic'] for r in rows)<sum(r['original_catastrophic'] for r in rows),'seed_reliability':dc['range']<d0['range'] and dc['sample_sd']<d0['sample_sd'],'upper_tail_retention':bool(upper) and all(r['conservative_minus_original']>=-eps for r in upper),'direction_consistency':sum(g>=0 for g in gc)>=4,'safety':mean([r['conservative_collision_minus_utr'] for r in rows])<=.05 and mean([r['conservative_timeout_minus_utr'] for r in rows])<=.05 and all(cells['conservative_drtp_sg'][s]['cv']==0 for s in SEEDS)}
 decision='R1_STABLE_SIGNAL_GO' if all(criteria.values()) else 'R1_NO_GO'; out=a.output_root/'diagnostics'/'stable_r1'/'gate';out.mkdir(parents=True)
 with (out/'r1_seed_level_results.csv').open('w',newline='',encoding='utf8') as h:w=csv.DictWriter(h,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 result={'decision':decision,'criteria':criteria,'epsilon_J':eps,'downside_margin':eps,'original_dispersion':d0,'conservative_dispersion':dc,'seed_results':rows,'automatic_continuation_started':False}
 (out/'R1_GATE_DECISION.json').write_text(json.dumps(result,indent=2)+'\n');(out/'R1_GATE_REPORT.md').write_text('# Stable-DRTP R1 gate\n\n**Decision:** `'+decision+'`.\n\n```json\n'+json.dumps(result,indent=2)+'\n```\n');print(json.dumps({'decision':decision,'report':str(out/'R1_GATE_REPORT.md')},indent=2))
if __name__=='__main__':main()
