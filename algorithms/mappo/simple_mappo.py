from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

import csv
import random

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.distributions import Categorical

from envs import UAVPursuitConfig, UAVPursuitEnv


@dataclass
class MAPPOConfig:
    seed: int = 0
    num_envs: int = 8
    rollout_steps: int = 128
    updates: int = 200
    hidden_dim: int = 128
    lr: float = 3e-4
    gamma: float = 0.99
    gae_lambda: float = 0.95
    clip_coef: float = 0.2
    entropy_coef: float = 0.01
    value_coef: float = 0.5
    max_grad_norm: float = 0.5
    ppo_epochs: int = 4
    minibatch_size: int = 512
    eval_interval: int = 10
    eval_episodes: int = 20
    target_policy: str = "mixed"
    target_speed: float = 0.75
    communication_radius: float = 8.0
    device: str = "cpu"
    out_dir: str = "results/mappo"
    save_interval: int = 10
    resume: str | None = None


class MLP(nn.Module):
    def __init__(self, in_dim: int, out_dim: int, hidden_dim: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, out_dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class MAPPOAgent(nn.Module):
    """Shared actor with centralized critic.

    This is intentionally compact for the phase-1 baseline. It uses a shared
    actor for all UAVs and a centralized critic that receives the global state.
    """

    def __init__(self, obs_dim: int, share_obs_dim: int, action_dim: int, hidden_dim: int):
        super().__init__()
        self.actor = MLP(obs_dim, action_dim, hidden_dim)
        self.critic = MLP(share_obs_dim, 1, hidden_dim)

    def get_action_and_value(
        self,
        obs: torch.Tensor,
        share_obs: torch.Tensor,
        action: torch.Tensor | None = None,
        deterministic: bool = False,
    ):
        logits = self.actor(obs)
        dist = Categorical(logits=logits)
        if action is None:
            action = torch.argmax(logits, dim=-1) if deterministic else dist.sample()
        log_prob = dist.log_prob(action)
        entropy = dist.entropy()
        value = self.critic(share_obs).squeeze(-1)
        return action, log_prob, entropy, value


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def make_envs(cfg: MAPPOConfig) -> List[UAVPursuitEnv]:
    return [
        UAVPursuitEnv(
            UAVPursuitConfig(
                seed=cfg.seed + i,
                target_policy=cfg.target_policy,
                target_speed=cfg.target_speed,
                communication_radius=cfg.communication_radius,
            )
        )
        for i in range(cfg.num_envs)
    ]


def eval_policy(agent: MAPPOAgent, cfg: MAPPOConfig, base_seed: int = 10_000) -> dict:
    device = torch.device(cfg.device)
    records = []
    agent.eval()
    with torch.no_grad():
        for ep in range(cfg.eval_episodes):
            env = UAVPursuitEnv(
                UAVPursuitConfig(
                    seed=base_seed + ep,
                    target_policy=cfg.target_policy,
                    target_speed=cfg.target_speed,
                    communication_radius=cfg.communication_radius,
                )
            )
            obs, share_obs, _ = env.reset()
            while True:
                obs_t = torch.as_tensor(obs, dtype=torch.float32, device=device)
                share_t = torch.as_tensor(share_obs, dtype=torch.float32, device=device)
                actions, _, _, _ = agent.get_action_and_value(obs_t, share_t, deterministic=True)
                obs, share_obs, _, _, dones, info = env.step(actions.cpu().numpy())
                if np.all(dones):
                    records.append(info)
                    break
    agent.train()
    return {
        "eval_success_rate": float(np.mean([r["success"] for r in records])),
        "eval_collision_rate": float(np.mean([r["collision"] for r in records])),
        "eval_timeout_rate": float(np.mean([r["timeout"] for r in records])),
        "eval_avg_steps": float(np.mean([r["step"] for r in records])),
        "eval_avg_distance": float(np.mean([r["mean_distance"] for r in records])),
    }


def train_mappo(cfg: MAPPOConfig) -> Path:
    set_seed(cfg.seed)
    device = torch.device(cfg.device)
    out_dir = Path(cfg.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    envs = make_envs(cfg)
    obs_list, share_list = [], []
    for env in envs:
        obs, share_obs, _ = env.reset()
        obs_list.append(obs)
        share_list.append(share_obs)
    obs = np.stack(obs_list)
    share_obs = np.stack(share_list)

    sample_env = envs[0]
    agent = MAPPOAgent(sample_env.obs_dim, sample_env.share_obs_dim, sample_env.action_dim, cfg.hidden_dim).to(device)
    if cfg.resume:
        agent.load_state_dict(torch.load(cfg.resume, map_location=device, weights_only=True))
    optimizer = optim.Adam(agent.parameters(), lr=cfg.lr, eps=1e-5)

    log_path = out_dir / "train_log.csv"
    with log_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "update",
                "loss",
                "policy_loss",
                "value_loss",
                "entropy",
                "train_avg_reward",
                "eval_success_rate",
                "eval_collision_rate",
                "eval_timeout_rate",
                "eval_avg_steps",
                "eval_avg_distance",
            ],
        )
        writer.writeheader()
        f.flush()
        best_eval_key = (-1.0, float("-inf"), float("-inf"), float("-inf"))

        for update in range(1, cfg.updates + 1):
            batch = collect_rollout(agent, envs, obs, share_obs, cfg, device)
            obs, share_obs = batch["next_obs"], batch["next_share_obs"]
            train_info = update_policy(agent, optimizer, batch, cfg, device)
            row = {
                "update": update,
                **train_info,
                "train_avg_reward": float(batch["rewards"].mean()),
            }
            if update % cfg.eval_interval == 0 or update == 1:
                row.update(eval_policy(agent, cfg, base_seed=10_000 + update * 100))
                print(row, flush=True)
                eval_key = (
                    float(row["eval_success_rate"]),
                    -float(row["eval_collision_rate"]),
                    -float(row["eval_timeout_rate"]),
                    -float(row["eval_avg_steps"]),
                )
                if eval_key > best_eval_key:
                    best_eval_key = eval_key
                    torch.save(agent.state_dict(), out_dir / "actor_critic_best.pt")
            else:
                row.update(
                    {
                        "eval_success_rate": "",
                        "eval_collision_rate": "",
                        "eval_timeout_rate": "",
                        "eval_avg_steps": "",
                        "eval_avg_distance": "",
                    }
                )
            writer.writerow(row)
            f.flush()
            if update % cfg.save_interval == 0 or update == cfg.updates:
                torch.save(agent.state_dict(), out_dir / "actor_critic_latest.pt")
    return log_path


def collect_rollout(
    agent: MAPPOAgent,
    envs: List[UAVPursuitEnv],
    obs: np.ndarray,
    share_obs: np.ndarray,
    cfg: MAPPOConfig,
    device: torch.device,
) -> dict:
    num_agents = envs[0].num_agents
    obs_buf, share_buf, action_buf, logp_buf = [], [], [], []
    reward_buf, done_buf, value_buf = [], [], []

    for _ in range(cfg.rollout_steps):
        obs_t = torch.as_tensor(obs, dtype=torch.float32, device=device)
        share_t = torch.as_tensor(share_obs, dtype=torch.float32, device=device)
        flat_obs = obs_t.reshape(cfg.num_envs * num_agents, -1)
        flat_share = share_t.reshape(cfg.num_envs * num_agents, -1)
        with torch.no_grad():
            actions, logp, _, values = agent.get_action_and_value(flat_obs, flat_share)

        actions_np = actions.cpu().numpy().reshape(cfg.num_envs, num_agents)
        values_np = values.cpu().numpy().reshape(cfg.num_envs, num_agents)
        logp_np = logp.cpu().numpy().reshape(cfg.num_envs, num_agents)

        next_obs, next_share, rewards, dones = [], [], [], []
        for e, env in enumerate(envs):
            o, s, _, r, d, _ = env.step(actions_np[e])
            if np.all(d):
                o, s, _ = env.reset()
            next_obs.append(o)
            next_share.append(s)
            rewards.append(r[:, 0])
            dones.append(d[:, 0])

        obs_buf.append(obs.copy())
        share_buf.append(share_obs.copy())
        action_buf.append(actions_np.copy())
        logp_buf.append(logp_np.copy())
        value_buf.append(values_np.copy())
        reward_buf.append(np.asarray(rewards, dtype=np.float32))
        done_buf.append(np.asarray(dones, dtype=np.float32))

        obs = np.stack(next_obs)
        share_obs = np.stack(next_share)

    with torch.no_grad():
        next_values = agent.critic(torch.as_tensor(share_obs, dtype=torch.float32, device=device).reshape(cfg.num_envs * num_agents, -1))
        next_values = next_values.squeeze(-1).cpu().numpy().reshape(cfg.num_envs, num_agents)

    rewards_np = np.asarray(reward_buf, dtype=np.float32)
    dones_np = np.asarray(done_buf, dtype=np.float32)
    values_np = np.asarray(value_buf, dtype=np.float32)
    advantages, returns = compute_gae(rewards_np, dones_np, values_np, next_values, cfg.gamma, cfg.gae_lambda)

    return {
        "obs": np.asarray(obs_buf, dtype=np.float32),
        "share_obs": np.asarray(share_buf, dtype=np.float32),
        "actions": np.asarray(action_buf, dtype=np.int64),
        "logp": np.asarray(logp_buf, dtype=np.float32),
        "values": values_np,
        "rewards": rewards_np,
        "dones": dones_np,
        "advantages": advantages,
        "returns": returns,
        "next_obs": obs,
        "next_share_obs": share_obs,
    }


def compute_gae(
    rewards: np.ndarray,
    dones: np.ndarray,
    values: np.ndarray,
    next_values: np.ndarray,
    gamma: float,
    gae_lambda: float,
) -> tuple[np.ndarray, np.ndarray]:
    advantages = np.zeros_like(rewards, dtype=np.float32)
    last_gae = np.zeros_like(next_values, dtype=np.float32)
    for t in reversed(range(rewards.shape[0])):
        next_nonterminal = 1.0 - dones[t]
        next_value = next_values if t == rewards.shape[0] - 1 else values[t + 1]
        delta = rewards[t] + gamma * next_value * next_nonterminal - values[t]
        last_gae = delta + gamma * gae_lambda * next_nonterminal * last_gae
        advantages[t] = last_gae
    returns = advantages + values
    return advantages, returns


def update_policy(
    agent: MAPPOAgent,
    optimizer: optim.Optimizer,
    batch: dict,
    cfg: MAPPOConfig,
    device: torch.device,
) -> dict:
    num_samples = cfg.rollout_steps * cfg.num_envs * agent_count(batch)
    obs = torch.as_tensor(batch["obs"].reshape(num_samples, -1), dtype=torch.float32, device=device)
    share_obs = torch.as_tensor(batch["share_obs"].reshape(num_samples, -1), dtype=torch.float32, device=device)
    actions = torch.as_tensor(batch["actions"].reshape(num_samples), dtype=torch.long, device=device)
    old_logp = torch.as_tensor(batch["logp"].reshape(num_samples), dtype=torch.float32, device=device)
    advantages = torch.as_tensor(batch["advantages"].reshape(num_samples), dtype=torch.float32, device=device)
    returns = torch.as_tensor(batch["returns"].reshape(num_samples), dtype=torch.float32, device=device)
    advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)

    losses = []
    policy_losses = []
    value_losses = []
    entropies = []
    indices = np.arange(num_samples)
    for _ in range(cfg.ppo_epochs):
        np.random.shuffle(indices)
        for start in range(0, num_samples, cfg.minibatch_size):
            mb = indices[start : start + cfg.minibatch_size]
            _, new_logp, entropy, values = agent.get_action_and_value(obs[mb], share_obs[mb], actions[mb])
            log_ratio = new_logp - old_logp[mb]
            ratio = log_ratio.exp()
            pg_loss1 = -advantages[mb] * ratio
            pg_loss2 = -advantages[mb] * torch.clamp(ratio, 1.0 - cfg.clip_coef, 1.0 + cfg.clip_coef)
            policy_loss = torch.max(pg_loss1, pg_loss2).mean()
            value_loss = 0.5 * (returns[mb] - values).pow(2).mean()
            entropy_loss = entropy.mean()
            loss = policy_loss + cfg.value_coef * value_loss - cfg.entropy_coef * entropy_loss

            optimizer.zero_grad()
            loss.backward()
            nn.utils.clip_grad_norm_(agent.parameters(), cfg.max_grad_norm)
            optimizer.step()

            losses.append(float(loss.detach().cpu()))
            policy_losses.append(float(policy_loss.detach().cpu()))
            value_losses.append(float(value_loss.detach().cpu()))
            entropies.append(float(entropy_loss.detach().cpu()))

    return {
        "loss": float(np.mean(losses)),
        "policy_loss": float(np.mean(policy_losses)),
        "value_loss": float(np.mean(value_losses)),
        "entropy": float(np.mean(entropies)),
    }


def agent_count(batch: dict) -> int:
    return int(batch["actions"].shape[2])
