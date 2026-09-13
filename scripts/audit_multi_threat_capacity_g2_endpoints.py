"""Read-only endpoint diagnosis for the G2 plain-MAPPO learnability pilot."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from algorithms.m2_commitment_ppo import M2PlainMAPPO
from scripts.run_multi_threat_capacity_plain_mappo import PROTOCOL, deterministic_action, make_env, stack


def evaluate(agent: M2PlainMAPPO, seed: int, repeats: int, stochastic: bool) -> dict[str, float]:
    rng=np.random.default_rng(seed); successes=[]; breaches=[]; entropies=[]; unique_actions=[]
    for _ in range(repeats):
        env=make_env(int(rng.integers(0,2**31-1)));env.reset();info={};actions_seen=[]
        while not env.base.done:
            obs,_,masks=stack([env]);obs_t=torch.as_tensor(obs,dtype=torch.float32);masks_t=torch.as_tensor(masks,dtype=torch.float32)
            with torch.no_grad():dist=agent.action_distribution(obs_t,masks_t);action=dist.sample() if stochastic else torch.argmax(dist.logits,dim=-1);entropies.append(float(dist.entropy().mean()))
            actions_seen.extend(action.squeeze(0).tolist());_,_,_,_,_,info=env.step(action.squeeze(0).numpy())
        successes.append(float(info.get("defense_success",0.0)));breaches.append(float(info.get("asset_breach",0.0)));unique_actions.append(float(len(set(actions_seen))))
    return {"success":float(np.mean(successes)),"breach":float(np.mean(breaches)),"mean_action_entropy":float(np.mean(entropies)),"mean_unique_actions_per_episode":float(np.mean(unique_actions))}


def main()->None:
    p=argparse.ArgumentParser();p.add_argument("--root",type=Path,required=True);p.add_argument("--output",type=Path,required=True);p.add_argument("--episodes",type=int,default=96);p.add_argument("--execute",action="store_true");a=p.parse_args()
    if not a.execute:raise SystemExit("pass --execute")
    if a.output.exists():raise FileExistsError(f"refusing to overwrite {a.output}")
    report={"protocol":"MULTI-THREAT-CAPACITY-G2-ENDPOINT-AUDIT-V1","diagnostic_only":True,"training_started":False,"endpoint_results":{}}
    for checkpoint in sorted(a.root.glob("seed*/endpoint.pt")):
        payload=torch.load(checkpoint,map_location="cpu",weights_only=True)
        if payload.get("protocol")!=PROTOCOL:raise ValueError(f"unexpected checkpoint {checkpoint}")
        agent=M2PlainMAPPO(obs_dim=payload["obs_dim"],critic_dim=payload["critic_dim"],hidden_dim=96,action_dim=payload["action_dim"]);agent.load_state_dict(payload["state_dict"]);agent.eval()
        report["endpoint_results"][checkpoint.parent.name]={"deterministic":evaluate(agent,11_000+payload["seed"],a.episodes,False),"stochastic":evaluate(agent,21_000+payload["seed"],a.episodes,True)}
    a.output.mkdir(parents=True);(a.output/"MULTI_THREAT_CAPACITY_G2_ENDPOINT_AUDIT.json").write_text(json.dumps(report,indent=2),encoding="utf-8");print(json.dumps(report,indent=2))


if __name__=="__main__":main()
