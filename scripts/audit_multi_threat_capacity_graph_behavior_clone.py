"""Can a legal graph actor reproduce successful complementary execution?"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from algorithms.redundant_topology_sg_mappo import SGMPPO
from envs.multi_threat_capacity_defense_env import MultiThreatCapacityDefenseConfig
from envs.multi_threat_capacity_shaped_defense_env import MultiThreatCapacityShapedDefenseEnv
from scripts.audit_multi_threat_capacity_defense_g1 import actions_for
from scripts.run_multi_threat_capacity_graph_mappo import PARAMETERS, stack


def make(seed: int) -> MultiThreatCapacityShapedDefenseEnv:
    return MultiThreatCapacityShapedDefenseEnv(MultiThreatCapacityDefenseConfig(seed=seed, **PARAMETERS))


def collect(seed: int, episodes: int):
    rng=np.random.default_rng(seed); records=[];success=0
    for _ in range(episodes):
        env=make(int(rng.integers(0,2**31-1)));env.reset();info={}
        while not env.base.done:
            obs,roles,adj,masks,share=stack([env]);action=actions_for(env,"parallel_suppress_intercept")
            records.append((obs[0],roles[0],adj[0],masks[0],share[0],action));_,_,_,_,_,info=env.step(action)
        success+=int(info.get("defense_success",0.0)>0.5)
    return tuple(np.stack([r[i] for r in records]) for i in range(6)),success


def evaluate(agent: SGMPPO, seed: int, episodes: int) -> float:
    rng=np.random.default_rng(seed);out=[];agent.eval()
    with torch.no_grad():
        for _ in range(episodes):
            env=make(int(rng.integers(0,2**31-1)));env.reset();info={}
            while not env.base.done:
                obs,roles,adj,masks,share=stack([env]);action,_,_,_=agent.action_value(torch.as_tensor(obs,dtype=torch.float32),torch.as_tensor(roles),torch.as_tensor(adj),torch.as_tensor(masks),torch.as_tensor(share,dtype=torch.float32),deterministic=True);_,_,_,_,_,info=env.step(action.squeeze(0).numpy())
            out.append(float(info.get("defense_success",0.0)))
    return float(np.mean(out))


def main():
    p=argparse.ArgumentParser();p.add_argument("--output-root",type=Path,required=True);p.add_argument("--episodes",type=int,default=96);p.add_argument("--epochs",type=int,default=120);p.add_argument("--device",default="cpu");p.add_argument("--execute",action="store_true");a=p.parse_args()
    if not a.execute:raise SystemExit("pass --execute")
    if a.output_root.exists():raise FileExistsError(f"refusing to overwrite {a.output_root}")
    a.output_root.mkdir(parents=True);torch.manual_seed(105001);device=torch.device(a.device);(obs,roles,adj,masks,share,actions),teacher_success=collect(105001,a.episodes)
    agent=SGMPPO(obs.shape[-1],share.shape[-1],masks.shape[-1]).to(device);opt=torch.optim.Adam(agent.actor.parameters(),lr=5e-4);o=torch.as_tensor(obs,dtype=torch.float32,device=device);r=torch.as_tensor(roles,device=device);ad=torch.as_tensor(adj,device=device);m=torch.as_tensor(masks,device=device);y=torch.as_tensor(actions,dtype=torch.int64,device=device);losses=[]
    for _ in range(a.epochs):
        logits=agent.actor(o,r,ad,m);loss=torch.nn.functional.cross_entropy(logits.reshape(-1,logits.shape[-1]),y.reshape(-1));opt.zero_grad();loss.backward();torch.nn.utils.clip_grad_norm_(agent.actor.parameters(),.5);opt.step();losses.append(float(loss.detach()))
    agent=agent.cpu();success=evaluate(agent,106001,96)
    report={"protocol":"MULTI-THREAT-CAPACITY-GRAPH-BC-INTERFACE-AUDIT-V1","diagnostic_only":True,"training_started":False,"teacher_success_episodes":teacher_success,"teacher_total_episodes":a.episodes,"supervised_graph_states":int(len(obs)),"final_cross_entropy":losses[-1],"legal_graph_clone_success":success,"interpretation":"Nonzero success shows that a graph policy using only legal node observations and active communication edges can express complementary execution. It does not yet validate the final learning algorithm or a paper claim."}
    (a.output_root/"MULTI_THREAT_CAPACITY_GRAPH_BC_AUDIT.json").write_text(json.dumps(report,indent=2),encoding="utf-8");torch.save({"protocol":report["protocol"],"state_dict":agent.state_dict(),"obs_dim":obs.shape[-1],"share_dim":share.shape[-1],"action_dim":masks.shape[-1]},a.output_root/"graph_bc_actor.pt");print(json.dumps(report,indent=2))
if __name__=="__main__":main()
