"""Diagnostic: can the legal observation interface express successful division?

Transparent controllers label trajectories using simulator geometry only to
create a training diagnostic.  The cloned actor receives only the frozen local
observation and role identifier at inference.  This is neither a paper method
nor a performance baseline.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from algorithms.m2_commitment_ppo import M2PlainMAPPO
from envs.multi_threat_capacity_shaped_defense_env import MultiThreatCapacityShapedDefenseEnv
from envs.multi_threat_capacity_defense_env import MultiThreatCapacityDefenseConfig
from scripts.audit_multi_threat_capacity_defense_g1 import actions_for
from scripts.run_multi_threat_capacity_plain_mappo import TASK_PARAMETERS, deterministic_action


def make(seed: int) -> MultiThreatCapacityShapedDefenseEnv:
    return MultiThreatCapacityShapedDefenseEnv(MultiThreatCapacityDefenseConfig(seed=seed, **TASK_PARAMETERS))


def collect(seed: int, episodes: int) -> tuple[np.ndarray, np.ndarray, int]:
    rng=np.random.default_rng(seed); observations=[]; actions=[]; successes=0
    for _ in range(episodes):
        env=make(int(rng.integers(0,2**31-1)));env.reset();info={}
        while not env.base.done:
            observations.append(env._obs().copy());actions.append(actions_for(env,"parallel_suppress_intercept"));_,_,_,_,_,info=env.step(actions[-1])
        successes += int(info.get("defense_success",0.0)>0.5)
    return np.concatenate(observations),np.concatenate(actions),successes


def evaluate(agent: M2PlainMAPPO, seed: int, episodes: int) -> float:
    rng=np.random.default_rng(seed);success=[]
    for _ in range(episodes):
        env=make(int(rng.integers(0,2**31-1)));env.reset();info={}
        while not env.base.done:
            _,_,_,_,_,info=env.step(deterministic_action(agent,env,torch.device("cpu")))
        success.append(float(info.get("defense_success",0.0)))
    return float(np.mean(success))


def main()->None:
    p=argparse.ArgumentParser();p.add_argument("--output-root",type=Path,required=True);p.add_argument("--episodes",type=int,default=96);p.add_argument("--epochs",type=int,default=80);p.add_argument("--execute",action="store_true");a=p.parse_args()
    if not a.execute:raise SystemExit("pass --execute")
    if a.output_root.exists():raise FileExistsError(f"refusing to overwrite {a.output_root}")
    a.output_root.mkdir(parents=True);torch.manual_seed(103001);obs,actions,teacher_success=collect(103001,a.episodes)
    agent=M2PlainMAPPO(obs_dim=obs.shape[-1],critic_dim=1,hidden_dim=96,action_dim=27);opt=torch.optim.Adam(agent.actor.parameters(),lr=5e-4);x=torch.as_tensor(obs,dtype=torch.float32);y=torch.as_tensor(actions,dtype=torch.int64);losses=[]
    for _ in range(a.epochs):
        logits=agent.actor(x);loss=torch.nn.functional.cross_entropy(logits.reshape(-1,27),y.reshape(-1));opt.zero_grad();loss.backward();opt.step();losses.append(float(loss.detach()))
    success=evaluate(agent,104001,96)
    report={"protocol":"MULTI-THREAT-CAPACITY-BC-INTERFACE-AUDIT-V1","diagnostic_only":True,"training_started":False,"teacher_success_episodes":teacher_success,"teacher_total_episodes":a.episodes,"supervised_examples":int(len(obs)),"final_cross_entropy":losses[-1],"legal_observation_clone_success":success,"interpretation":"A nonzero cloned-policy success rate supports expressiveness of the legal local observation interface; it does not validate privileged supervision, PPO learnability, or a paper method."}
    (a.output_root/"MULTI_THREAT_CAPACITY_BC_INTERFACE_AUDIT.json").write_text(json.dumps(report,indent=2),encoding="utf-8");print(json.dumps(report,indent=2))


if __name__=="__main__":main()
