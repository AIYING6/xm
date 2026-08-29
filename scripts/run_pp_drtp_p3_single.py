"""Run one frozen PP-DRTP P3 0.5M pilot trajectory."""
from __future__ import annotations
import argparse, hashlib, json, subprocess, sys, time
from dataclasses import replace
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]; sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
from algorithms.ri_gmappo.simple_ri_gmappo import train_ri_gmappo
import run_drtp_sg_strict_10m_single as strict

PROTOCOL='PP-DRTP-P3-PILOT-V1'; SEEDS=(3401,3402,3403); UPDATES=1953
ARMS={'utr_sg':'utr','drtp_sg':'drtp','pp_drtp_sg':'pp_drtp'}
TAPE=ROOT/'configs'/'pp_drtp_p3_pilot_tape.json'; P2=ROOT/'docs'/'drtp_stable_v2_d8_20260830'/'PP_DRTP_P2_TECHNICAL_AUDIT.json'

def digest(p:Path)->str:
 h=hashlib.sha256(); h.update(p.read_bytes()); return h.hexdigest()
def config(arm,seed,out):
 base=strict.training_config('utr_sg',strict.SEEDS[0],out)
 return replace(base,seed=seed,updates=UPDATES,save_interval=UPDATES,milestone_updates={976:'250k',1953:'500k'},out_dir=str(out),drtp_sampler_mode=ARMS[arm],drtp_sampler_seed=seed,drtp_sampler_total_updates=UPDATES,drtp_sampler_logging=True,runtime_state_checkpointing=True,runtime_state_save_interval=UPDATES,evaluation_enabled=False,pp_drtp_probe_count=4,pp_drtp_probe_seed=seed)
def main():
 p=argparse.ArgumentParser();p.add_argument('--arm',choices=tuple(ARMS),required=True);p.add_argument('--seed',choices=SEEDS,type=int,required=True);p.add_argument('--output-root',type=Path,required=True);p.add_argument('--execute',action='store_true');a=p.parse_args()
 if not a.execute: raise SystemExit('--execute required')
 if json.loads(P2.read_text())['status']!='P2_TECHNICAL_PASS': raise RuntimeError('PP P2 audit not PASS')
 tape=json.loads(TAPE.read_text()); tape_hash=digest(TAPE); out=a.output_root/'runs'/a.arm/f'seed{a.seed}'
 if out.exists(): raise FileExistsError(f'refusing rerun/overwrite: {out}')
 out.mkdir(parents=True); cfg=config(a.arm,a.seed,out)
 manifest={'protocol':PROTOCOL,'status':'running','arm':a.arm,'seed':a.seed,'sampler_mode':cfg.drtp_sampler_mode,'updates':UPDATES,'environment_steps':UPDATES*4*64,'probe_count':4 if a.arm=='pp_drtp_sg' else 0,'checkpoint_selection':'common_final_500k_only','early_stopping':False,'rerun_authorized':False,'continuation_authorized':False,'tape_hash':tape_hash,'tape_sha256':tape_hash,'p2_audit_sha256':digest(P2),'config':cfg.__dict__,'started_at':time.time()}
 path=out/'run_manifest.json';path.write_text(json.dumps(manifest,indent=2,default=str)+'\n')
 try:
  train_ri_gmappo(cfg)
  required=['actor_critic_latest.pt','actor_critic_runtime_state_latest.pt','train_log.csv','drtp_topology_sampler_log.csv']
  if a.arm=='pp_drtp_sg': required.append('pp_drtp_probe_log.csv')
  required += ['actor_critic_milestone_250k.pt','actor_critic_milestone_500k.pt']
  missing=[x for x in required if not (out/x).exists()]
  if missing: raise RuntimeError('missing frozen artifacts: '+','.join(missing))
  manifest.update(status='completed',finished_at=time.time(),final_checkpoint_sha256=digest(out/'actor_critic_latest.pt'))
 except Exception as e:
  manifest.update(status='technical_invalid',finished_at=time.time(),error=repr(e));path.write_text(json.dumps(manifest,indent=2,default=str)+'\n');raise
 path.write_text(json.dumps(manifest,indent=2,default=str)+'\n')
if __name__=='__main__':main()
