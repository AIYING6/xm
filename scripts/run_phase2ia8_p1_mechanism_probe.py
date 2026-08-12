"""Phase2IA8 P1 fixed-controller pre-completion support mechanism probe."""
from __future__ import annotations
import argparse,csv,json,sys
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from envs.uav_intercept_3d_env import UAVIntercept3DConfig,UAVIntercept3DEnv
from run_phase2ia6_task_feasibility import controller_actions

CONTROLLERS=('structural_oracle','legal_observation');SEEDS=(701,702,703)
OUT=ROOT/'results'/'development'/'phase2ia8_p1_mechanism_probe'
def eid(ci,si,ep):return 710000+10000*ci+1000*si+ep
def write(p,rows):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('w',newline='',encoding='utf8') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def run_one(controller,ci,seed,si,episode):
 env=UAVIntercept3DEnv(UAVIntercept3DConfig(seed=eid(ci,si,episode),target_policy='straight',communication_range_scale=1.0,communication_dropout_prob=.30,message_delay_steps=2,radar_dropout_prob=0.0,strict_target_sensing=True,agent_target_info_bottleneck=True,failed_blue_agent=-1,node_failure_duration_steps=0,max_steps=260,attack_hold_steps=4))
 obs,_,_=env.reset(); support_hold=0;trigger=None;failure=None;loss=None;recovery=None;trace=[]
 while True:
  actions=controller_actions(controller,env,obs);obs,_,_,_,dones,info=env.step(actions);step=int(info['step']);support=float(info['chain_support_t'])>.5
  support_hold=support_hold+1 if support else 0
  if trigger is None and support_hold>=2 and step<=220:
   trigger=step;failure=step+1;env.config.failed_blue_agent=1;env.config.node_failure_start_step=failure;env.config.node_failure_duration_steps=80
  active=float(info['node_failure_active'])>.5
  if active and not support and loss is None:loss=step
  if loss is not None and support and recovery is None:recovery=step
  trace.append({'development_episode_id':eid(ci,si,episode),'controller':controller,'seed':seed,'timestep':step,'chain_support_t':float(support),'support_hold':support_hold,'node_failure_active':float(active),'terminal':float(np.all(dones)),'chain_closed':info['chain_closed'],'success':info['success']})
  if np.all(dones):break
 return {'development_episode_id':eid(ci,si,episode),'controller':controller,'seed':seed,'episode':episode,'support_eligible':float(trigger is not None),'support_trigger_step':-1 if trigger is None else trigger,'t_failure':-1 if failure is None else failure,'support_lost_after_failure':float(loss is not None),'t_loss':-1 if loss is None else loss,'post_failure_support_recovered_after_loss':float(recovery is not None),'t_recovery':-1 if recovery is None else recovery,'delta_t_loss_to_recovery':-1 if recovery is None or loss is None else recovery-loss,'event':float(recovery is not None),'censor_time':step,'success':info['success'],'timeout':info['timeout'],'controller_information_class':'ORACLE_STRUCTURAL' if ci==0 else 'LEGAL_OBSERVATION_ONLY'},trace
def main():
 p=argparse.ArgumentParser();p.add_argument('--out-dir',type=Path,default=OUT);p.add_argument('--episodes',type=int,default=100);p.add_argument('--execute',action='store_true');a=p.parse_args()
 if not a.execute:raise SystemExit('NO-GO: P1 requires --execute after the committed launch record')
 if (a.out_dir/'raw_episode_metrics.csv').exists() or (a.out_dir/'raw_timestep_chain').exists():raise FileExistsError('Refusing to overwrite P1 results')
 rows=[]
 for ci,c in enumerate(CONTROLLERS):
  for si,s in enumerate(SEEDS):
   trace=[]
   for ep in range(a.episodes):r,t=run_one(c,ci,s,si,ep);rows.append(r);trace.extend(t)
   write(a.out_dir/'raw_timestep_chain'/f'{c}_seed{s}.csv',trace)
 write(a.out_dir/'raw_episode_metrics.csv',rows)
 (a.out_dir/'manifest.json').write_text(json.dumps({'artifact_class':'DEVELOPMENT_ONLY_P1','protocol':'PHASE2IA8-PSR-V1','episodes':len(rows),'canonical_data_used':False},indent=2)+'\n')
 print(json.dumps({'status':'COMPLETE','episodes':len(rows)},indent=2))
if __name__=='__main__':main()
