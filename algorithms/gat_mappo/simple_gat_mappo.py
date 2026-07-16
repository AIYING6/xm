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
class GATMAPPOConfig:
    seed: int = 0
    num_envs: int = 8
    rollout_steps: int = 128
    updates: int = 200
    hidden_dim: int = 128
    role_dim: int = 8
    lr: float = 3e-4
    gamma: float = 0.99
    gae_lambda: float = 0.95
    clip_coef: float = 0.2
    entropy_coef: float = 0.01
    value_coef: float = 0.5
    max_grad_norm: float = 0.5
    ppo_epochs: int = 4
    minibatch_graphs: int = 256
    eval_interval: int = 10
    eval_episodes: int = 20
    target_policy: str = "mixed"
    target_speed: float = 0.75
    communication_radius: float = 8.0
    device: str = "cpu"
    out_dir: str = "results/gat_mappo"
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


class GraphAttentionLayer(nn.Module):
    def __init__(self, in_dim: int, out_dim: int):
        super().__init__()
        self.proj = nn.Linear(in_dim, out_dim, bias=False)
        self.attn = nn.Linear(out_dim * 2, 1, bias=False)
        self.leaky_relu = nn.LeakyReLU(0.2)

    def forward(self, x: torch.Tensor, adj: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        # x: [B, N, F], adj: [B, N, N]
        h = self.proj(x)
        bsz, num_nodes, hidden = h.shape
        hi = h.unsqueeze(2).expand(bsz, num_nodes, num_nodes, hidden)
        hj = h.unsqueeze(1).expand(bsz, num_nodes, num_nodes, hidden)
        scores = self.leaky_relu(self.attn(torch.cat([hi, hj], dim=-1))).squeeze(-1)

        eye = torch.eye(num_nodes, dtype=adj.dtype, device=adj.device).unsqueeze(0)
        mask = torch.clamp(adj + eye, 0.0, 1.0)
        scores = scores.masked_fill(mask <= 0.0, -1e9)
        weights = torch.softmax(scores, dim=-1)
        out = torch.bmm(weights, h)
        return torch.tanh(out), weights


class GATActor(nn.Module):
    def __init__(self, obs_dim: int, node_feat_dim: int, num_roles: int, role_dim: int, hidden_dim: int, action_dim: int):
        super().__init__()
        self.role_emb = nn.Embedding(num_roles, role_dim)
        self.obs_encoder = nn.Sequential(
            nn.Linear(obs_dim, hidden_dim),
            nn.Tanh(),
        )
        self.input = nn.Sequential(
            nn.Linear(node_feat_dim + role_dim, hidden_dim),
            nn.Tanh(),
        )
        self.gat1 = GraphAttentionLayer(hidden_dim, hidden_dim)
        self.gat2 = GraphAttentionLayer(hidden_dim, hidden_dim)
        self.policy_head = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, action_dim),
        )

    def forward(self, obs: torch.Tensor, node_feat: torch.Tensor, role: torch.Tensor, adj: torch.Tensor, num_agents: int):
        role_feat = self.role_emb(role.long())
        x = self.input(torch.cat([node_feat, role_feat], dim=-1))
        x, attn1 = self.gat1(x, adj)
        x, attn2 = self.gat2(x, adj)
        graph_feat = x[:, :num_agents]
        obs_feat = self.obs_encoder(obs)
        logits = self.policy_head(torch.cat([obs_feat, graph_feat], dim=-1))
        return logits, attn2


class GATMAPPOAgent(nn.Module):
    def __init__(
        self,
        obs_dim: int,
        node_feat_dim: int,
        share_obs_dim: int,
        action_dim: int,
        num_agents: int,
        hidden_dim: int,
        role_dim: int,
    ):
        super().__init__()
        self.num_agents = num_agents
        self.actor = GATActor(obs_dim, node_feat_dim, num_roles=4, role_dim=role_dim, hidden_dim=hidden_dim, action_dim=action_dim)
        self.critic = MLP(share_obs_dim, 1, hidden_dim)

    def get_action_and_value(
        self,
        obs: torch.Tensor,
        node_feat: torch.Tensor,
        role: torch.Tensor,
        adj: torch.Tensor,
        share_obs: torch.Tensor,
        action: torch.Tensor | None = None,
        deterministic: bool = False,
    ):
        logits, attn = self.actor(obs, node_feat, role, adj, self.num_agents)
        dist = Categorical(logits=logits)
        if action is None:
            action = torch.argmax(logits, dim=-1) if deterministic else dist.sample()
        log_prob = dist.log_prob(action)
        entropy = dist.entropy()
        value = self.critic(share_obs).squeeze(-1)
        return action, log_prob, entropy, value, attn


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def make_envs(cfg: GATMAPPOConfig) -> List[UAVPursuitEnv]:
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


def stack_graphs(graphs: List[dict]) -> dict:
    return {
        "node_feat": np.stack([g["node_feat"] for g in graphs]).astype(np.float32),
        "role": np.stack([g["role"] for g in graphs]).astype(np.int64),
        "adj": np.stack([g["adj"] for g in graphs]).astype(np.float32),
    }


def eval_policy(agent: GATMAPPOAgent, cfg: GATMAPPOConfig, base_seed: int = 10_000) -> dict:
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
            _, share_obs, graph = env.reset()
            obs, share_obs, graph = env.reset()
            while True:
                g = stack_graphs([graph])
                actions, _, _, _, _ = agent.get_action_and_value(
                    torch.as_tensor(obs[None, ...], dtype=torch.float32, device=device),
                    torch.as_tensor(g["node_feat"], dtype=torch.float32, device=device),
                    torch.as_tensor(g["role"], dtype=torch.long, device=device),
                    torch.as_tensor(g["adj"], dtype=torch.float32, device=device),
                    torch.as_tensor(share_obs[None, ...], dtype=torch.float32, device=device),
                    deterministic=True,
                )
                obs, share_obs, graph, _, dones, info = env.step(actions.squeeze(0).cpu().numpy())
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


def train_gat_mappo(cfg: GATMAPPOConfig) -> Path:
    set_seed(cfg.seed)
    device = torch.device(cfg.device)
    out_dir = Path(cfg.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    envs = make_envs(cfg)
    obs_list, share_list, graph_list = [], [], []
    for env in envs:
        obs, share_obs, graph = env.reset()
        obs_list.append(obs)
        share_list.append(share_obs)
        graph_list.append(graph)
    obs = np.stack(obs_list)
    share_obs = np.stack(share_list)
    graph_obs = stack_graphs(graph_list)

    sample_env = envs[0]
    sample_graph = graph_list[0]
    agent = GATMAPPOAgent(
        obs_dim=sample_env.obs_dim,
        node_feat_dim=sample_graph["node_feat"].shape[-1],
        share_obs_dim=sample_env.share_obs_dim,
        action_dim=sample_env.action_dim,
        num_agents=sample_env.num_agents,
        hidden_dim=cfg.hidden_dim,
        role_dim=cfg.role_dim,
    ).to(device)
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
            batch = collect_rollout(agent, envs, obs, share_obs, graph_obs, cfg, device)
            obs, share_obs, graph_obs = batch["next_obs"], batch["next_share_obs"], batch["next_graph_obs"]
            train_info = update_policy(agent, optimizer, batch, cfg, device)
            row = {"update": update, **train_info, "train_avg_reward": float(batch["rewards"].mean())}
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
    agent: GATMAPPOAgent,
    envs: List[UAVPursuitEnv],
    obs: np.ndarray,
    share_obs: np.ndarray,
    graph_obs: dict,
    cfg: GATMAPPOConfig,
    device: torch.device,
) -> dict:
    obs_buf, share_buf, node_buf, role_buf, adj_buf = [], [], [], [], []
    action_buf, logp_buf, reward_buf, done_buf, value_buf = [], [], [], [], []

    for _ in range(cfg.rollout_steps):
        with torch.no_grad():
            actions, logp, _, values, _ = agent.get_action_and_value(
                torch.as_tensor(obs, dtype=torch.float32, device=device),
                torch.as_tensor(graph_obs["node_feat"], dtype=torch.float32, device=device),
                torch.as_tensor(graph_obs["role"], dtype=torch.long, device=device),
                torch.as_tensor(graph_obs["adj"], dtype=torch.float32, device=device),
                torch.as_tensor(share_obs, dtype=torch.float32, device=device),
            )

        actions_np = actions.cpu().numpy()
        values_np = values.cpu().numpy()
        logp_np = logp.cpu().numpy()
        next_obs, next_share, next_graphs, rewards, dones = [], [], [], [], []
        for e, env in enumerate(envs):
            o, s, g, r, d, _ = env.step(actions_np[e])
            if np.all(d):
                o, s, g = env.reset()
            next_obs.append(o)
            next_share.append(s)
            next_graphs.append(g)
            rewards.append(r[:, 0])
            dones.append(d[:, 0])

        obs_buf.append(obs.copy())
        share_buf.append(share_obs.copy())
        node_buf.append(graph_obs["node_feat"].copy())
        role_buf.append(graph_obs["role"].copy())
        adj_buf.append(graph_obs["adj"].copy())
        action_buf.append(actions_np.copy())
        logp_buf.append(logp_np.copy())
        value_buf.append(values_np.copy())
        reward_buf.append(np.asarray(rewards, dtype=np.float32))
        done_buf.append(np.asarray(dones, dtype=np.float32))

        obs = np.stack(next_obs)
        share_obs = np.stack(next_share)
        graph_obs = stack_graphs(next_graphs)

    with torch.no_grad():
        next_values = agent.critic(torch.as_tensor(share_obs, dtype=torch.float32, device=device)).squeeze(-1)
        next_values = next_values.cpu().numpy()

    rewards_np = np.asarray(reward_buf, dtype=np.float32)
    dones_np = np.asarray(done_buf, dtype=np.float32)
    values_np = np.asarray(value_buf, dtype=np.float32)
    advantages, returns = compute_gae(rewards_np, dones_np, values_np, next_values, cfg.gamma, cfg.gae_lambda)
    return {
        "obs": np.asarray(obs_buf, dtype=np.float32),
        "share_obs": np.asarray(share_buf, dtype=np.float32),
        "node_feat": np.asarray(node_buf, dtype=np.float32),
        "role": np.asarray(role_buf, dtype=np.int64),
        "adj": np.asarray(adj_buf, dtype=np.float32),
        "actions": np.asarray(action_buf, dtype=np.int64),
        "logp": np.asarray(logp_buf, dtype=np.float32),
        "values": values_np,
        "rewards": rewards_np,
        "dones": dones_np,
        "advantages": advantages,
        "returns": returns,
        "next_obs": obs,
        "next_share_obs": share_obs,
        "next_graph_obs": graph_obs,
    }


def compute_gae(rewards, dones, values, next_values, gamma, gae_lambda):
    advantages = np.zeros_like(rewards, dtype=np.float32)
    last_gae = np.zeros_like(next_values, dtype=np.float32)
    for t in reversed(range(rewards.shape[0])):
        next_nonterminal = 1.0 - dones[t]
        next_value = next_values if t == rewards.shape[0] - 1 else values[t + 1]
        delta = rewards[t] + gamma * next_value * next_nonterminal - values[t]
        last_gae = delta + gamma * gae_lambda * next_nonterminal * last_gae
        advantages[t] = last_gae
    return advantages, advantages + values


def update_policy(agent: GATMAPPOAgent, optimizer: optim.Optimizer, batch: dict, cfg: GATMAPPOConfig, device):
    t_steps, n_envs, num_agents = batch["actions"].shape
    num_graphs = t_steps * n_envs
    obs = torch.as_tensor(batch["obs"].reshape(num_graphs, num_agents, -1), dtype=torch.float32, device=device)
    node_feat = torch.as_tensor(batch["node_feat"].reshape(num_graphs, *batch["node_feat"].shape[2:]), dtype=torch.float32, device=device)
    role = torch.as_tensor(batch["role"].reshape(num_graphs, *batch["role"].shape[2:]), dtype=torch.long, device=device)
    adj = torch.as_tensor(batch["adj"].reshape(num_graphs, *batch["adj"].shape[2:]), dtype=torch.float32, device=device)
    share_obs = torch.as_tensor(batch["share_obs"].reshape(num_graphs, num_agents, -1), dtype=torch.float32, device=device)
    actions = torch.as_tensor(batch["actions"].reshape(num_graphs, num_agents), dtype=torch.long, device=device)
    old_logp = torch.as_tensor(batch["logp"].reshape(num_graphs, num_agents), dtype=torch.float32, device=device)
    advantages = torch.as_tensor(batch["advantages"].reshape(num_graphs, num_agents), dtype=torch.float32, device=device)
    returns = torch.as_tensor(batch["returns"].reshape(num_graphs, num_agents), dtype=torch.float32, device=device)
    advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)

    losses, policy_losses, value_losses, entropies = [], [], [], []
    indices = np.arange(num_graphs)
    for _ in range(cfg.ppo_epochs):
        np.random.shuffle(indices)
        for start in range(0, num_graphs, cfg.minibatch_graphs):
            mb = indices[start : start + cfg.minibatch_graphs]
            _, new_logp, entropy, values, _ = agent.get_action_and_value(
                obs[mb], node_feat[mb], role[mb], adj[mb], share_obs[mb], actions[mb]
            )
            ratio = (new_logp - old_logp[mb]).exp()
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
