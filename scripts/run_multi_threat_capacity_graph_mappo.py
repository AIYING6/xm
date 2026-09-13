"""Standard graph-MAPPO G3 learnability control for capacity defense."""
from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from pathlib import Path
from typing import Any

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from algorithms.redundant_topology_sg_mappo import SGMPPO
from envs.multi_threat_capacity_defense_env import MultiThreatCapacityDefenseConfig
from envs.multi_threat_capacity_shaped_defense_env import MultiThreatCapacityShapedDefenseEnv

PROTOCOL="MULTI-THREAT-CAPACITY-DEFENSE-G3-GRAPH-MAPPO-V1"
PARAMETERS={"red_start_x":14000.0,"suppression_range":12000.0,"branch_step":12,"red_initial_lateral":8500.0,"asset_lateral":15000.0,"red_center_y_jitter":1500.0,"approach_speed_jitter":16.0,"branch_step_jitter":3}


def seed_all(seed:int)->None: random.seed(seed);np.random.seed(seed);torch.manual_seed(seed);torch.cuda.manual_seed_all(seed) if torch.cuda.is_available() else None
def make(seed:int)->MultiThreatCapacityShapedDefenseEnv:return MultiThreatCapacityShapedDefenseEnv(MultiThreatCapacityDefenseConfig(seed=seed,**PARAMETERS))
class Cursor:
    def __init__(self,seed:int):self.rng=np.random.default_rng(seed)
    def next(self):return make(int(self.rng.integers(0,2**31-1)))
def stack(envs):
    return (np.stack([e._obs() for e in envs]),np.tile(np.arange(3,dtype=np.int64),(len(envs),1)),np.stack([e._graph()["active_adj"] for e in envs]).astype(np.float32),np.stack([e._graph()["action_masks"] for e in envs]).astype(np.float32),np.stack([e._share_obs()[0] for e in envs]))
def evaluate(agent,seed,episodes,device):
    rng=np.random.default_rng(seed);rows=[];agent.eval()
    with torch.no_grad():
        for ep in range(episodes):
            env=make(int(rng.integers(0,2**31-1)));env.reset();total=0.;info={}
            while not env.base.done:
                obs,roles,adj,masks,share=stack([env]);actions,_,_,_=agent.action_value(torch.as_tensor(obs,dtype=torch.float32,device=device),torch.as_tensor(roles,device=device),torch.as_tensor(adj,device=device),torch.as_tensor(masks,device=device),torch.as_tensor(share,dtype=torch.float32,device=device),deterministic=True);_,_,_,reward,_,info=env.step(actions.squeeze(0).cpu().numpy());total+=float(reward.mean())
            rows.append({"episode":ep,"return":total,"defense_success":float(info.get("defense_success",0.)),"asset_breach":float(info.get("asset_breach",0.)),"timeout":float(info.get("timeout",0.))})
    return rows,{k:float(np.mean([r[k] for r in rows])) for k in rows[0] if k!="episode"}
def train(seed,updates,parallel,rollout,out,device):
    seed_all(seed);cursor=Cursor(seed+37);envs=[cursor.next() for _ in range(parallel)];obs,roles,adj,masks,share=stack(envs);agent=SGMPPO(obs.shape[-1],share.shape[-1],masks.shape[-1]).to(device);opt=torch.optim.Adam(agent.parameters(),lr=3e-4);fields=("update","environment_steps","train_reward","policy_loss","value_loss","eval_return","eval_defense_success","eval_asset_breach")
    with (out/"train_log.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for update in range(1,updates+1):
            rec=[]
            for _ in range(rollout):
                obs,roles,adj,masks,share=stack(envs);t=lambda x,dtype=None:torch.as_tensor(x,dtype=dtype,device=device);o,r,a,m,s=t(obs,torch.float32),t(roles),t(adj),t(masks),t(share,torch.float32)
                with torch.no_grad():acts,lp,_,val=agent.action_value(o,r,a,m,s);vals=val[:,0]
                rew=[];done=[]
                for i,e in enumerate(envs):
                    _,_,_,reward,dones,_=e.step(acts[i].cpu().numpy());rew.append(float(reward.mean()));done.append(float(dones[0,0]));envs[i]=cursor.next() if dones[0,0] else e
                rec.append((obs,roles,adj,masks,share,acts.cpu().numpy(),lp.cpu().numpy(),vals.cpu().numpy(),np.asarray(rew,dtype=np.float32),np.asarray(done,dtype=np.float32)))
            *_,next_share=stack(envs)
            with torch.no_grad(): _,_,_,boot=agent.action_value(t(stack(envs)[0],torch.float32),t(stack(envs)[1]),t(stack(envs)[2]),t(stack(envs)[3]),t(next_share,torch.float32));boot=boot[:,0].cpu().numpy()
            adv=np.zeros((rollout,parallel),np.float32);ret=np.zeros_like(adv);gae=np.zeros(parallel,np.float32)
            for j in reversed(range(rollout)):
                val,rew,dn=rec[j][7],rec[j][8],rec[j][9];nxt=boot if j==rollout-1 else rec[j+1][7];delta=rew+.99*(1-dn)*nxt-val;gae=delta+.99*.95*(1-dn)*gae;adv[j]=gae;ret[j]=gae+val
            cat=lambda index,dtype: t(np.concatenate([x[index] for x in rec]),dtype)
            o,r,a,m,s,acts,oldlp=cat(0,torch.float32),cat(1,None),cat(2,None),cat(3,None),cat(4,torch.float32),cat(5,torch.int64),cat(6,torch.float32);advantages=t(adv.reshape(-1),torch.float32);advantages=(advantages-advantages.mean())/(advantages.std()+1e-8);targets=t(ret.reshape(-1),torch.float32)
            for _ in range(4):
                _,lp,entropy,val=agent.action_value(o,r,a,m,s,acts);ratio=torch.exp(lp.sum(-1)-oldlp.sum(-1));ploss=-torch.minimum(ratio*advantages,torch.clamp(ratio,.8,1.2)*advantages).mean();vloss=torch.nn.functional.mse_loss(val[:,0],targets);loss=ploss+.5*vloss-.01*entropy.mean();opt.zero_grad();loss.backward();torch.nn.utils.clip_grad_norm_(agent.parameters(),.5);opt.step()
            ev={}
            if update%64==0 or update==updates:_,ev=evaluate(agent,seed+update,24,device)
            w.writerow({"update":update,"environment_steps":update*parallel*rollout,"train_reward":float(np.mean([x[8].mean() for x in rec])),"policy_loss":float(ploss.detach()),"value_loss":float(vloss.detach()),"eval_return":ev.get("return",""),"eval_defense_success":ev.get("defense_success",""),"eval_asset_breach":ev.get("asset_breach","")});f.flush()
    torch.save({"protocol":PROTOCOL,"seed":seed,"state_dict":agent.state_dict(),"obs_dim":obs.shape[-1],"share_dim":share.shape[-1],"action_dim":masks.shape[-1]},out/"endpoint.pt")
def main():
    p=argparse.ArgumentParser();p.add_argument("--seed",type=int,required=True);p.add_argument("--output-root",type=Path,required=True);p.add_argument("--updates",type=int,default=512);p.add_argument("--parallel-envs",type=int,default=12);p.add_argument("--rollout-steps",type=int,default=24);p.add_argument("--device",default="cpu");p.add_argument("--execute",action="store_true");a=p.parse_args()
    if not a.execute:raise SystemExit("pass --execute")
    if a.output_root.exists():raise FileExistsError(f"refusing to overwrite {a.output_root}")
    a.output_root.mkdir(parents=True);train(a.seed,a.updates,a.parallel_envs,a.rollout_steps,a.output_root,torch.device(a.device))
if __name__=="__main__":main()
