"""Plain MAPPO G2 learnability pilot on the frozen capacity-defense task."""
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
from algorithms.m2_commitment_ppo import M2PlainMAPPO
from envs.multi_threat_capacity_defense_env import MultiThreatCapacityDefenseConfig, MultiThreatCapacityDefenseEnv

PROTOCOL = "MULTI-THREAT-CAPACITY-DEFENSE-G2-PLAIN-MAPPO-V1"
TASK_PARAMETERS = {
    "red_start_x": 14000.0, "suppression_range": 12000.0, "branch_step": 12,
    "red_initial_lateral": 8500.0, "asset_lateral": 15000.0,
    "red_center_y_jitter": 1500.0, "approach_speed_jitter": 16.0, "branch_step_jitter": 3,
}


def seed_all(seed: int) -> torch.Generator:
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    generator = torch.Generator(device="cpu"); generator.manual_seed(seed)
    return generator


def make_env(seed: int) -> MultiThreatCapacityDefenseEnv:
    return MultiThreatCapacityDefenseEnv(MultiThreatCapacityDefenseConfig(seed=seed, **TASK_PARAMETERS))


class Cursor:
    def __init__(self, seed: int):
        self.rng = np.random.default_rng(seed)
    def next(self) -> MultiThreatCapacityDefenseEnv:
        return make_env(int(self.rng.integers(0, 2**31 - 1)))


def stack(envs: list[MultiThreatCapacityDefenseEnv]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    return (
        np.stack([env._obs() for env in envs]),
        np.stack([env._share_obs()[0] for env in envs]),
        np.stack([env._graph()["action_masks"] for env in envs]),
    )


def deterministic_action(agent: M2PlainMAPPO, env: MultiThreatCapacityDefenseEnv, device: torch.device) -> np.ndarray:
    obs, _, masks = stack([env])
    with torch.no_grad():
        dist = agent.action_distribution(torch.as_tensor(obs, dtype=torch.float32, device=device), torch.as_tensor(masks, dtype=torch.float32, device=device))
    return torch.argmax(dist.logits, dim=-1).squeeze(0).cpu().numpy().astype(np.int64)


def evaluate(agent: M2PlainMAPPO, seed: int, repeats: int, device: torch.device) -> tuple[list[dict[str, Any]], dict[str, float]]:
    rng = np.random.default_rng(seed); rows=[]
    for episode in range(repeats):
        env = make_env(int(rng.integers(0, 2**31 - 1))); env.reset(); total=0.0; info: dict[str, Any]={}
        while not env.base.done:
            _, _, _, reward, _, info = env.step(deterministic_action(agent, env, device)); total += float(reward.mean())
        rows.append({"episode":episode,"return":total,"defense_success":float(info.get("defense_success",0.0)),"asset_breach":float(info.get("asset_breach",0.0)),"timeout":float(info.get("timeout",0.0)),"collision":float(info.get("collision",0.0)),"constraint_violation":float(info.get("constraint_violation",0.0)),"neutralized_threats":float(info.get("neutralized_threats",0.0))})
    return rows, {key:float(np.mean([row[key] for row in rows])) for key in rows[0] if key != "episode"}


def train(seed: int, updates: int, parallel_envs: int, rollout_steps: int, eval_episodes: int, output: Path, device: torch.device) -> None:
    generator=seed_all(seed); cursor=Cursor(seed+41); envs=[cursor.next() for _ in range(parallel_envs)]
    probe_obs, probe_critic, probe_masks=stack(envs)
    agent=M2PlainMAPPO(obs_dim=probe_obs.shape[-1],critic_dim=probe_critic.shape[-1],hidden_dim=96,action_dim=probe_masks.shape[-1]).to(device)
    optimizer=torch.optim.Adam(agent.parameters(),lr=3e-4); gamma,lam,clip,epochs=0.99,0.95,0.2,4
    fields=("update","environment_steps","train_reward","policy_loss","value_loss","eval_return","eval_defense_success","eval_asset_breach")
    with (output/"train_log.csv").open("w",newline="",encoding="utf-8") as handle:
        writer=csv.DictWriter(handle,fieldnames=fields);writer.writeheader()
        for update in range(1,updates+1):
            records=[]
            for _ in range(rollout_steps):
                obs,critic,masks=stack(envs); obs_t=torch.as_tensor(obs,dtype=torch.float32,device=device); critic_t=torch.as_tensor(critic,dtype=torch.float32,device=device); masks_t=torch.as_tensor(masks,dtype=torch.float32,device=device)
                with torch.no_grad():
                    # Global Torch seeding above covers CUDA and CPU.  Passing
                    # a CPU-only Generator to CUDA multinomial would fail.
                    dist=agent.action_distribution(obs_t,masks_t); actions=dist.sample(); logp=dist.log_prob(actions).sum(dim=-1); value=agent.value(critic_t)
                rewards=[];dones=[]
                for index,env in enumerate(envs):
                    _,_,_,reward,done,_=env.step(actions[index].cpu().numpy());rewards.append(float(reward.mean()));dones.append(float(done[0,0]))
                    if done[0,0]:envs[index]=cursor.next()
                records.append((obs,critic,masks,actions.cpu().numpy(),logp.cpu().numpy(),value.cpu().numpy(),np.asarray(rewards,dtype=np.float32),np.asarray(dones,dtype=np.float32)))
            _,next_critic,_=stack(envs)
            with torch.no_grad():next_value=agent.value(torch.as_tensor(next_critic,dtype=torch.float32,device=device)).cpu().numpy()
            advantages=np.zeros((rollout_steps,parallel_envs),dtype=np.float32);returns=np.zeros_like(advantages);gae=np.zeros(parallel_envs,dtype=np.float32)
            for step in reversed(range(rollout_steps)):
                values,rewards,dones=records[step][5],records[step][6],records[step][7];following=next_value if step==rollout_steps-1 else records[step+1][5]
                delta=rewards+gamma*(1.0-dones)*following-values;gae=delta+gamma*lam*(1.0-dones)*gae;advantages[step]=gae;returns[step]=gae+values
            flat_obs=torch.as_tensor(np.concatenate([r[0] for r in records]),dtype=torch.float32,device=device);flat_critic=torch.as_tensor(np.concatenate([r[1] for r in records]),dtype=torch.float32,device=device);flat_masks=torch.as_tensor(np.concatenate([r[2] for r in records]),dtype=torch.float32,device=device);flat_actions=torch.as_tensor(np.concatenate([r[3] for r in records]),dtype=torch.int64,device=device);old_logp=torch.as_tensor(np.concatenate([r[4] for r in records]),dtype=torch.float32,device=device);adv=torch.as_tensor(advantages.reshape(-1),dtype=torch.float32,device=device);adv=(adv-adv.mean())/(adv.std()+1e-8);target=torch.as_tensor(returns.reshape(-1),dtype=torch.float32,device=device)
            for _ in range(epochs):
                dist=agent.action_distribution(flat_obs,flat_masks);ratio=torch.exp(dist.log_prob(flat_actions).sum(dim=-1)-old_logp);policy_loss=-torch.minimum(ratio*adv,torch.clamp(ratio,1-clip,1+clip)*adv).mean();value_loss=torch.nn.functional.mse_loss(agent.value(flat_critic),target);loss=policy_loss+0.5*value_loss-0.01*dist.entropy().mean();optimizer.zero_grad();loss.backward();torch.nn.utils.clip_grad_norm_(agent.parameters(),0.5);optimizer.step()
            validation={}
            if update%64==0 or update==updates:_,validation=evaluate(agent,seed+update,24,device)
            writer.writerow({"update":update,"environment_steps":update*parallel_envs*rollout_steps,"train_reward":float(np.mean([r[6].mean() for r in records])),"policy_loss":float(policy_loss.detach()),"value_loss":float(value_loss.detach()),"eval_return":validation.get("return",""),"eval_defense_success":validation.get("defense_success",""),"eval_asset_breach":validation.get("asset_breach","")});handle.flush()
    torch.save({"protocol":PROTOCOL,"seed":seed,"task_parameters":TASK_PARAMETERS,"obs_dim":probe_obs.shape[-1],"critic_dim":probe_critic.shape[-1],"action_dim":probe_masks.shape[-1],"state_dict":agent.state_dict()},output/"endpoint.pt")


def main() -> None:
    p=argparse.ArgumentParser();p.add_argument("mode",choices=("train","evaluate"));p.add_argument("--seed",type=int,required=True);p.add_argument("--output-root",type=Path,required=True);p.add_argument("--updates",type=int,default=512);p.add_argument("--parallel-envs",type=int,default=12);p.add_argument("--rollout-steps",type=int,default=24);p.add_argument("--evaluation-episodes",type=int,default=96);p.add_argument("--checkpoint",type=Path);p.add_argument("--device",default="cpu");p.add_argument("--execute",action="store_true");a=p.parse_args()
    if not a.execute:raise SystemExit("pass --execute")
    if a.output_root.exists():raise FileExistsError(f"refusing to overwrite {a.output_root}")
    a.output_root.mkdir(parents=True);device=torch.device(a.device)
    if a.mode=="train":train(a.seed,a.updates,a.parallel_envs,a.rollout_steps,a.evaluation_episodes,a.output_root,device);return
    if a.checkpoint is None:raise ValueError("evaluate requires --checkpoint")
    payload=torch.load(a.checkpoint,map_location=device,weights_only=True)
    if payload.get("protocol")!=PROTOCOL or payload.get("task_parameters")!=TASK_PARAMETERS:raise ValueError("unexpected G2 checkpoint")
    agent=M2PlainMAPPO(obs_dim=payload["obs_dim"],critic_dim=payload["critic_dim"],hidden_dim=96,action_dim=payload["action_dim"]).to(device);agent.load_state_dict(payload["state_dict"]);rows,summary=evaluate(agent,a.seed,a.evaluation_episodes,device)
    with (a.output_root/"episode_metrics.csv").open("w",newline="",encoding="utf-8") as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    (a.output_root/"summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8");print(json.dumps(summary,indent=2))


if __name__=="__main__":main()
