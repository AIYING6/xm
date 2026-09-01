"""Frozen M3 telemetry-first diagnostic training; evaluation is intentionally absent."""
from __future__ import annotations
import argparse,json,sys,time
from dataclasses import replace
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
from algorithms.ri_gmappo.simple_ri_gmappo import train_ri_gmappo
import run_drtp_sg_strict_10m_single as strict
FREEZE=ROOT/'configs/drtp_c2_m3_diagnostic_freeze.json'; ARMS=('utr_sg','group_weighted_utr_sg')
def seeds(f): return tuple(x for c in ('A','B') for x in f['cohorts'][c])
def config(arm,seed,out,f):
 b=strict.training_config('utr_sg',strict.SEEDS[0],out); weighted=arm=='group_weighted_utr_sg'
 return replace(b,seed=seed,updates=f['budget']['updates'],out_dir=str(out),evaluation_enabled=False,save_interval=488,save_snapshots=False,runtime_state_checkpointing=True,runtime_state_save_interval=488,milestone_updates={int(k):v for k,v in f['budget']['milestones'].items()},drtp_sampler_mode='none',fixed_stratified_topology_sampler=True,fixed_stratified_topology_sampler_seed=seed,group_weighted_actor_enabled=weighted,group_weighted_actor_auto_lagged=weighted,group_weighted_actor_scores=None,group_weighted_actor_strength=0.25,group_weighted_actor_min=0.75,group_weighted_actor_max=1.25,group_credit_telemetry=True,group_credit_telemetry_interval=f['telemetry']['group_credit_interval_updates'],failure_aware_telemetry=True)
def main():
 p=argparse.ArgumentParser();p.add_argument('--arm',choices=ARMS);p.add_argument('--seed',type=int);p.add_argument('--output-root',type=Path,required=True);p.add_argument('--execute',action='store_true');a=p.parse_args();f=json.loads(FREEZE.read_text())
 if not a.execute or not f['authorization']['training_authorized']: raise RuntimeError('M3 authorization required')
 if a.seed not in seeds(f): raise ValueError('unfrozen seed')
 out=a.output_root/'runs'/a.arm/f'seed{a.seed}';out.mkdir(parents=True,exist_ok=False); manifest={'protocol':f['protocol'],'status':'running','arm':a.arm,'seed':a.seed,'evaluation_authorized':False,'started_at':time.time()};(out/'run_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 try:
  train_ri_gmappo(config(a.arm,a.seed,out,f)); required=[out/'train_log.csv',out/'group_credit_telemetry.csv',out/'group_credit_gradient_conflicts.csv',out/'failure_telemetry'/'telemetry_manifest.json',out/'actor_critic_runtime_state_milestone_500k.pt']
  if not all(x.is_file() for x in required): raise RuntimeError('missing M3 telemetry artifact')
  manifest.update(status='completed',completed_at=time.time())
 except BaseException as e: manifest.update(status='failed',error=repr(e),completed_at=time.time());raise
 finally: (out/'run_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
if __name__=='__main__':main()
