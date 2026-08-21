"""Seed-level final D1 comparison; training seed is the only inference unit."""
from __future__ import annotations
import argparse,csv,json
from pathlib import Path
import sys,numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.aggregate_t1_telemetry_native_reference import cell_summary  # noqa
from scripts.run_t1_telemetry_native_single import SEEDS  # noqa
from scripts.telemetry_native_t0 import read_jsonl  # noqa
METRICS=('J_nominal','J_F0','J_OOD_mean','J_OOD_worst','collision','timeout','constraint_violation')
def cell(root,arm,seed): return cell_summary(read_jsonl(root/'evaluations'/'final_1m'/arm/f'seed{seed}'/'episode_aggregates.jsonl'))
def avg(x): return {k:float(np.mean([v[k] for v in x.values()])) for k in METRICS}
def main():
 p=argparse.ArgumentParser();p.add_argument('--tc-root',type=Path,required=True);p.add_argument('--t1-root',type=Path,required=True);p.add_argument('--artifacts-root',type=Path,required=True);p.add_argument('--docs-root',type=Path,default=ROOT/'docs');p.add_argument('--execute',action='store_true');a=p.parse_args()
 if not a.execute: raise SystemExit('explicit --execute required')
 if a.artifacts_root.exists(): raise FileExistsError(f'refusing overwrite: {a.artifacts_root}')
 tc={s:cell(a.tc_root,'tc_sam_utr',s) for s in SEEDS}; utr={s:cell(a.t1_root,'utr_sg',s) for s in SEEDS}; paired={s:{k:tc[s][k]-utr[s][k] for k in METRICS} for s in SEEDS}; pt,pu=avg(tc),avg(utr)
 favorable=[s for s in SEEDS if all(paired[s][k]>0 for k in ('J_F0','J_OOD_mean','J_OOD_worst')) and paired[s]['timeout']<=0]
 catastrophic=[s for s in SEEDS if paired[s]['J_F0']<-.5*abs(utr[s]['J_F0']) or paired[s]['J_OOD_worst']<-.5*abs(utr[s]['J_OOD_worst'])]
 delta={k:pt[k]-pu[k] for k in METRICS}
 if len(favorable)>=4 and not catastrophic and all(delta[k]>0 for k in ('J_F0','J_OOD_mean','J_OOD_worst')) and delta['timeout']<=0 and delta['collision']<=0 and delta['constraint_violation']<=0: decision='A — TC_SAM_DEV_PASS'
 elif not catastrophic and any(delta[k]>0 for k in ('J_F0','J_OOD_mean','J_OOD_worst')): decision='B — TC_SAM_DEV_MIXED'
 else: decision='C — TC_SAM_DEV_FAIL'
 result={'protocol':'TC-SAM-D1-AGGREGATE-V1','final_decision':decision,'training_seed_unit':'seed','tc_sam_per_seed':tc,'utr_per_seed':utr,'paired_difference':paired,'tc_sam_pooled':pt,'utr_pooled':pu,'profile':{'favorable_seeds':favorable,'catastrophic_seeds':catastrophic,'pooled_difference':delta}}
 a.artifacts_root.mkdir(parents=True);(a.artifacts_root/'results.json').write_text(json.dumps(result,indent=2)+'\n')
 with (a.artifacts_root/'paired.csv').open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=('seed',*METRICS));w.writeheader();w.writerows({'seed':s,**paired[s]} for s in SEEDS)
 table='\n'.join(f"| {s} | {tc[s]['J_nominal']:.3f} | {tc[s]['J_F0']:.3f} | {tc[s]['J_OOD_mean']:.3f} | {tc[s]['J_OOD_worst']:.3f} | {tc[s]['timeout']:.3f} |" for s in SEEDS)
 a.docs_root.joinpath('TC_SAM_D1_FIVE_SEED_RESULTS.md').write_text('# TC-SAM-D1 Five-Seed Results\n\n| Seed | J nominal | J F0 | J OOD mean | J OOD worst | Timeout |\n|---|---:|---:|---:|---:|---:|\n'+table+'\n')
 a.docs_root.joinpath('TC_SAM_D1_PAIRED_UTR_COMPARISON.md').write_text('# TC-SAM-D1 Paired UTR Comparison\n\n```json\n'+json.dumps(result['profile'],indent=2)+'\n```\n')
 a.docs_root.joinpath('TC_SAM_D1_OOD_SAFETY_ANALYSIS.md').write_text('# TC-SAM-D1 OOD and Safety\n\n```json\n'+json.dumps({'tc_sam':pt,'utr':pu,'difference':delta},indent=2)+'\n```\n')
 a.docs_root.joinpath('TC_SAM_D1_SHARPNESS_MECHANISM_ANALYSIS.md').write_text('# TC-SAM-D1 Sharpness Mechanism Analysis\n\nThe frozen offline sharpness probe is run only after final checkpoints are available; its results must be interpreted as mechanism evidence, not a decision gate.\n')
 a.docs_root.joinpath('TC_SAM_D1_COMPUTE_ANALYSIS.md').write_text('# TC-SAM-D1 Compute Analysis\n\nEnvironment steps are matched to T1. TC-SAM adds one actor loss forward/backward per PPO actor minibatch and has no inference-time overhead.\n')
 a.docs_root.joinpath('TC_SAM_D1_FINAL_DECISION.md').write_text('# TC-SAM-D1 Final Decision\n\n**Decision:** `'+decision+'`\n\n```json\n'+json.dumps(result['profile'],indent=2)+'\n```\n')
 print(json.dumps({'final_decision':decision,'artifacts':str(a.artifacts_root)},indent=2))
if __name__=='__main__': main()
