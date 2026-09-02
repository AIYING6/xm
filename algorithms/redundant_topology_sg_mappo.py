"""Independent SG-MAPPO learner for the frozen redundant-topology task.

This module deliberately does not import or modify any legacy learner.  It is
the P2 qualification interface: role-shared graph actor, centralized critic,
legal action masks and reproducible PPO state serialization.
"""
from __future__ import annotations

from dataclasses import dataclass
import random
from typing import Any

import numpy as np
import torch
import torch.nn as nn
from torch.distributions import Categorical


@dataclass(frozen=True)
class SGMPPOConfig:
    num_envs: int = 8
    rollout_steps: int = 32
    updates: int = 3907
    hidden_dim: int = 96
    role_dim: int = 8
    lr: float = 3e-4
    gamma: float = 0.99
    gae_lambda: float = 0.95
    clip_coef: float = 0.2
    entropy_coef: float = 0.01
    value_coef: float = 0.5
    max_grad_norm: float = 0.5
    ppo_epochs: int = 4
    minibatch_graphs: int = 128


def set_seed(seed: int) -> None:
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    if torch.cuda.is_available(): torch.cuda.manual_seed_all(seed)


class GraphLayer(nn.Module):
    def __init__(self, dim: int):
        super().__init__()
        self.proj = nn.Linear(dim, dim, bias=False)
        self.score = nn.Linear(2 * dim, 1, bias=False)

    def forward(self, x: torch.Tensor, adj: torch.Tensor) -> torch.Tensor:
        h = self.proj(x); b, n, d = h.shape
        left = h.unsqueeze(2).expand(b, n, n, d)
        right = h.unsqueeze(1).expand(b, n, n, d)
        logits = torch.nn.functional.leaky_relu(self.score(torch.cat((left, right), -1)).squeeze(-1), 0.2)
        eye = torch.eye(n, device=x.device).unsqueeze(0)
        logits = logits.masked_fill((adj + eye) <= 0, -1e9)
        return torch.tanh(torch.bmm(torch.softmax(logits, -1), h))


class RoleGraphActor(nn.Module):
    def __init__(self, obs_dim: int, action_dim: int, hidden: int, role_dim: int):
        super().__init__()
        self.role = nn.Embedding(3, role_dim)
        self.input = nn.Sequential(nn.Linear(obs_dim + role_dim, hidden), nn.Tanh())
        self.g1, self.g2 = GraphLayer(hidden), GraphLayer(hidden)
        self.head = nn.Sequential(nn.Linear(hidden, hidden), nn.Tanh(), nn.Linear(hidden, action_dim))

    def forward(self, obs: torch.Tensor, roles: torch.Tensor, adj: torch.Tensor, masks: torch.Tensor) -> torch.Tensor:
        x = self.input(torch.cat((obs, self.role(roles.long())), -1))
        x = self.g2(self.g1(x, adj), adj)
        return self.head(x).masked_fill(masks <= 0, -1e9)


class SGMPPO(nn.Module):
    def __init__(self, obs_dim: int, share_dim: int, action_dim: int, hidden: int = 96, role_dim: int = 8):
        super().__init__()
        self.actor = RoleGraphActor(obs_dim, action_dim, hidden, role_dim)
        self.critic = nn.Sequential(nn.Linear(share_dim, hidden), nn.Tanh(), nn.Linear(hidden, hidden), nn.Tanh(), nn.Linear(hidden, 1))

    def action_value(self, obs: torch.Tensor, roles: torch.Tensor, adj: torch.Tensor, masks: torch.Tensor, share: torch.Tensor,
                     action: torch.Tensor | None = None, deterministic: bool = False):
        dist = Categorical(logits=self.actor(obs, roles, adj, masks))
        if action is None: action = torch.argmax(dist.logits, -1) if deterministic else dist.sample()
        value = self.critic(share).squeeze(-1).unsqueeze(-1).expand_as(action).float()
        return action, dist.log_prob(action), dist.entropy(), value


def gae(rewards: np.ndarray, dones: np.ndarray, values: np.ndarray, bootstrap: np.ndarray, gamma: float, lam: float):
    advantages = np.zeros_like(rewards, dtype=np.float32); running = np.zeros_like(bootstrap, dtype=np.float32)
    for t in range(len(rewards) - 1, -1, -1):
        nxt = bootstrap if t == len(rewards) - 1 else values[t + 1]
        keep = 1.0 - dones[t]
        delta = rewards[t] + gamma * nxt * keep - values[t]
        running = delta + gamma * lam * keep * running
        advantages[t] = running
    return advantages, advantages + values


def checkpoint_payload(agent: SGMPPO, optimizer: torch.optim.Optimizer, env_states: list[dict[str, Any]], update: int, seed: int) -> dict[str, Any]:
    return {"format": "redundant_topology_sg_mappo_p2_v1", "update": update, "seed": seed,
            "model": agent.state_dict(), "optimizer": optimizer.state_dict(), "env_states": env_states,
            "torch_rng": torch.get_rng_state(), "numpy_rng": np.random.get_state(), "python_rng": random.getstate()}
