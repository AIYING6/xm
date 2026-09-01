"""Technical-only paired cloud benchmark for C2 diagnostic telemetry."""
from __future__ import annotations
import argparse, hashlib, json, sys, time
from dataclasses import replace
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]; sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
from algorithms.ri_gmappo.simple_ri_gmappo import train_ri_gmappo
import run_drtp_sg_strict_10m_single as strict
FREEZE=ROOT/'configs/drtp_c2_m2_telemetry_cost_preflight_freeze.json'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def size(p): return sum(x.stat().st_size for x in p.rglob('*') if x.is_file())
def make_cfg(arm,out,f):
 b=strict.training_config('utr_sg',strict.SEEDS[0],out)
 return replace(b,seed=int(f['seed']),updates=int(f['updates']),out_dir=str(out),evaluation_enabled=False,save_interval=64,save_snapshots=False,runtime_state_checkpointing=True,runtime_state_save_interval=64,milestone_updates={int(k):v for k,v in f['milestones'].items()},drtp_sampler_mode='none',fixed_stratified_topology_sampler=True,fixed_stratified_topology_sampler_seed=int(f['seed']),group_weighted_actor_enabled=False,group_credit_telemetry=arm=='telemetry_on',group_credit_telemetry_interval=int(f['group_credit_interval_updates']),failure_aware_telemetry=arm=='telemetry_on')
def main():
 p=argparse.ArgumentParser();p.add_argument('--output-root',type=Path,required=True);p.add_argument('--execute',action='store_true');a=p.parse_args();f=json.loads(FREEZE.read_text())
 if not a.execute or not f['authorization']['technical_training_authorized']: raise RuntimeError('frozen M2 authorization required')
 if a.output_root.exists(): raise FileExistsError(a.output_root)
 a.output_root.mkdir(parents=True); rows=[]
 for arm in f['arms']:
  out=a.output_root/'runs'/arm;out.mkdir(parents=True); t=time.perf_counter();train_ri_gmappo(make_cfg(arm,out,f)); elapsed=time.perf_counter()-t
  required=[out/'actor_critic_latest.pt',out/'train_log.csv',out/'actor_critic_runtime_state_milestone_32k.pt']
  if arm=='telemetry_on': required += [out/'group_credit_telemetry.csv',out/'group_credit_gradient_conflicts.csv',out/'failure_telemetry'/'telemetry_manifest.json']
  if not all(x.is_file() for x in required): raise RuntimeError(f'missing artifact: {arm}')
  rows.append({'arm':arm,'wall_seconds':elapsed,'directory_bytes':size(out),'final_model_sha256':sha(out/'actor_critic_latest.pt'),'train_log_sha256':sha(out/'train_log.csv'),'telemetry_bytes':size(out/'failure_telemetry') if (out/'failure_telemetry').exists() else 0})
 equal=all(rows[0][k]==rows[1][k] for k in f['required_equivalence']); payload={'protocol':f['protocol'],'verdict':'C2_M2_TELEMETRY_COST_PASS' if equal else 'C2_M2_TELEMETRY_COST_FAIL','runs':rows,'trajectory_equivalence':equal,'evaluation_started':False,'scientific_training_started':False,'next_step_authorized':False}
 d=a.output_root/'diagnostics';d.mkdir();(d/'C2_M2_COST_PREFLIGHT.json').write_text(json.dumps(payload,indent=2)+'\n');(d/'C2_M2_COST_PREFLIGHT.md').write_text(f'# C2-M2 telemetry cost preflight\n\n**Verdict:** `{payload["verdict"]}`.\n\nThis is a technical cost check only; no evaluation or scientific claim was produced.\n')
 print(json.dumps(payload,indent=2));
 if not equal: raise SystemExit(1)
if __name__=='__main__': main()
