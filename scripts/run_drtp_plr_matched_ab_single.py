"""One new PLR-only trajectory matched to an existing frozen A/B seed."""
from __future__ import annotations
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
import torch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from algorithms.ri_gmappo.simple_ri_gmappo import RIGMAPPOConfig,train_ri_gmappo
from scripts.drtp_plr_matched_ab_contracts import FREEZE,MILESTONES,NUM_ENVS,ROLLOUT,SEEDS,STEPS,UPDATES,tape
PROTOCOL='DRTP-PLR-EXTERNAL-MATCHED-AB-10M-V2'
def sha(p):
 h=hashlib.sha256();
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def cfg(seed,out):
 return RIGMAPPOConfig(env_name='3d_intercept',seed=seed,num_envs=NUM_ENVS,rollout_steps=ROLLOUT,updates=UPDATES,hidden_dim=115,role_dim=8,intent_dim=8,graph_encoder='single',role_gate_mode='none',target_policy='straight',strict_target_sensing=True,agent_target_info_bottleneck=True,relay_dependent_task=True,business_grounded_geometry=True,communication_range_scale=1.,communication_dropout_prob=0.,message_delay_steps=0,radar_dropout_prob=0.,min_success_step=260,failed_blue_agent=-1,node_failure_start_step=0,node_failure_duration_steps=0,evaluation_enabled=False,target_kl=None,save_interval=UPDATES,save_snapshots=False,milestone_updates=MILESTONES,out_dir=str(out),device='cuda' if torch.cuda.is_available() else 'cpu',topology_curriculum_schedule='none',topology_curriculum_logging=False,fixed_f0_probability=None,drtp_sampler_mode='plr',drtp_sampler_seed=seed,drtp_sampler_logging=True,runtime_state_checkpointing=True,runtime_state_save_interval=UPDATES)
def main():
 p=argparse.ArgumentParser();p.add_argument('--cohort',choices=('A','B'),required=True);p.add_argument('--seed',type=int,required=True);p.add_argument('--output-root',type=Path,required=True);p.add_argument('--execute',action='store_true');a=p.parse_args()
 if not a.execute:raise SystemExit('explicit --execute is required')
 if a.seed not in SEEDS[a.cohort]:raise ValueError('seed outside frozen A/B PLR cohort')
 t=json.loads((a.output_root/'cohorts'/a.cohort/'tape'/'tape_manifest.json').read_text(encoding='utf-8'))
 if t!=tape(a.cohort):raise RuntimeError('invalid frozen cohort tape')
 run=a.output_root/'cohorts'/a.cohort/'runs'/'plr_style_sg'/f'seed{a.seed}'
 if run.exists():raise FileExistsError(f'refusing to overwrite {run}')
 run.mkdir(parents=True);c=cfg(a.seed,run);m={'protocol':PROTOCOL,'cohort':a.cohort,'status':'running','arm':'plr_style_sg','seed':a.seed,'sampler_mode':'plr','updates':UPDATES,'environment_steps':STEPS,'from_scratch':True,'resume':False,'early_stopping':False,'checkpoint_promotion':False,'evaluation_during_training':False,'fixed_endpoint_tape_hash':t['tape_hash'],'tape_not_read_by_training':True,'freeze_sha256':sha(FREEZE),'config':c.__dict__};(run/'run_manifest.json').write_text(json.dumps(m,indent=2,default=str)+'\n',encoding='utf-8');train_ri_gmappo(c)
 needed=[run/'actor_critic_latest.pt',run/'actor_critic_runtime_state_latest.pt',run/'plr_topology_sampler_manifest.json',run/'plr_topology_sampler_log.csv']+[run/f'actor_critic_{x}_{n}.pt' for n in MILESTONES.values() for x in ('milestone','runtime_state_milestone')]
 if bad:=[str(x) for x in needed if not x.is_file()]:raise FileNotFoundError(', '.join(bad))
 m.update({'status':'completed','checkpoint_sha256':sha(run/'actor_critic_latest.pt'),'runtime_state_sha256':sha(run/'actor_critic_runtime_state_latest.pt')});(run/'run_manifest.json').write_text(json.dumps(m,indent=2,default=str)+'\n',encoding='utf-8');print(json.dumps({'status':'completed','cohort':a.cohort,'seed':a.seed},indent=2),flush=True)
if __name__=='__main__':main()
