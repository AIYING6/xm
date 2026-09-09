"""Recurrent graph MAPPO contract for the active-diagnosis pilot.

Collection stores low-level sampled actions separately from gate-executed
options.  PPO actor replay is chronological, resets completed environments
before their next observation, and masks samples controlled by the external
gate.  The centralized critic consumes the real executed transition returns.
"""

from __future__ import annotations

from dataclasses import dataclass
import random
from typing import Any

import numpy as np
import torch
import torch.nn as nn
from torch.distributions import Categorical

from algorithms.redundant_topology_sg_mappo import GraphLayer


class RecurrentRoleGraphActor(nn.Module):
    def __init__(self, obs_dim: int, action_dim: int, hidden_dim: int = 96, role_dim: int = 8) -> None:
        super().__init__()
        self.hidden_dim = int(hidden_dim)
        self.role = nn.Embedding(3, role_dim)
        self.input = nn.Sequential(nn.Linear(obs_dim + role_dim, hidden_dim), nn.Tanh())
        self.g1 = GraphLayer(hidden_dim)
        self.g2 = GraphLayer(hidden_dim)
        self.memory = nn.GRUCell(hidden_dim, hidden_dim)
        self.head = nn.Sequential(nn.Linear(hidden_dim, hidden_dim), nn.Tanh(), nn.Linear(hidden_dim, action_dim))

    def initial_state(self, batch: int, agents: int, *, device: torch.device | str) -> torch.Tensor:
        return torch.zeros(batch, agents, self.hidden_dim, device=device)

    def forward_step(
        self,
        obs: torch.Tensor,
        roles: torch.Tensor,
        adj: torch.Tensor,
        masks: torch.Tensor,
        hidden: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        if obs.ndim != 3 or hidden.shape[:2] != obs.shape[:2]:
            raise ValueError("obs and hidden must have [batch, agent, ...] axes")
        x = self.input(torch.cat((obs, self.role(roles.long())), dim=-1))
        x = self.g2(self.g1(x, adj), adj)
        next_hidden = self.memory(x.reshape(-1, x.shape[-1]), hidden.reshape(-1, hidden.shape[-1]))
        next_hidden = next_hidden.reshape_as(hidden)
        logits = self.head(next_hidden).masked_fill(masks <= 0, -1e9)
        return logits, next_hidden


class RecurrentSGMAPPO(nn.Module):
    def __init__(self, obs_dim: int, share_dim: int, action_dim: int, hidden_dim: int = 96, role_dim: int = 8) -> None:
        super().__init__()
        self.actor = RecurrentRoleGraphActor(obs_dim, action_dim, hidden_dim, role_dim)
        self.critic = nn.Sequential(
            nn.Linear(share_dim, hidden_dim), nn.Tanh(),
            nn.Linear(hidden_dim, hidden_dim), nn.Tanh(),
            nn.Linear(hidden_dim, 1),
        )

    def action_value_step(
        self,
        obs: torch.Tensor,
        roles: torch.Tensor,
        adj: torch.Tensor,
        masks: torch.Tensor,
        share: torch.Tensor,
        hidden: torch.Tensor,
        action: torch.Tensor | None = None,
        deterministic: bool = False,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        logits, next_hidden = self.actor.forward_step(obs, roles, adj, masks, hidden)
        distribution = Categorical(logits=logits)
        if action is None:
            action = logits.argmax(-1) if deterministic else distribution.sample()
        value = self.critic(share).squeeze(-1)
        return action, distribution.log_prob(action), distribution.entropy(), value, next_hidden, logits


@dataclass(frozen=True)
class RecurrentSequenceReplay:
    logits: torch.Tensor
    log_prob: torch.Tensor
    entropy: torch.Tensor
    values: torch.Tensor
    final_hidden: torch.Tensor


def replay_recurrent_sequence(
    agent: RecurrentSGMAPPO,
    *,
    obs: torch.Tensor,
    roles: torch.Tensor,
    adj: torch.Tensor,
    masks: torch.Tensor,
    share: torch.Tensor,
    sampled_actions: torch.Tensor,
    episode_starts: torch.Tensor,
    initial_hidden: torch.Tensor,
    bptt_horizon: int,
) -> RecurrentSequenceReplay:
    """Replay ``[time, environment, agent]`` sequences with truncated BPTT."""
    if obs.ndim != 4 or sampled_actions.ndim != 3 or episode_starts.ndim != 2:
        raise ValueError("invalid recurrent rollout axes")
    time_steps, environments, agents = sampled_actions.shape
    if tuple(obs.shape[:3]) != (time_steps, environments, agents):
        raise ValueError("observation and action axes differ")
    if tuple(episode_starts.shape) != (time_steps, environments):
        raise ValueError("episode_starts must have [time, environment] shape")
    if bptt_horizon <= 0:
        raise ValueError("bptt_horizon must be positive")
    hidden = initial_hidden
    logits_rows, log_prob_rows, entropy_rows, value_rows = [], [], [], []
    for t in range(time_steps):
        if t and t % bptt_horizon == 0:
            hidden = hidden.detach()
        reset = episode_starts[t].to(device=hidden.device, dtype=torch.bool)
        hidden = torch.where(reset[:, None, None], torch.zeros_like(hidden), hidden)
        action, log_prob, entropy, value, hidden, logits = agent.action_value_step(
            obs[t], roles[t], adj[t], masks[t], share[t], hidden, action=sampled_actions[t]
        )
        del action
        logits_rows.append(logits)
        log_prob_rows.append(log_prob)
        entropy_rows.append(entropy)
        value_rows.append(value)
    return RecurrentSequenceReplay(
        logits=torch.stack(logits_rows),
        log_prob=torch.stack(log_prob_rows),
        entropy=torch.stack(entropy_rows),
        values=torch.stack(value_rows),
        final_hidden=hidden,
    )


def masked_clipped_actor_objective(
    replay: RecurrentSequenceReplay,
    old_log_prob: torch.Tensor,
    advantages: torch.Tensor,
    actor_control_mask: torch.Tensor,
    clip_coef: float,
    entropy_coef: float,
) -> torch.Tensor:
    if not (replay.log_prob.shape == old_log_prob.shape == advantages.shape == actor_control_mask.shape):
        raise ValueError("actor PPO tensors must have identical sequence axes")
    weights = actor_control_mask.to(dtype=replay.log_prob.dtype)
    denominator = weights.sum()
    if denominator.item() <= 0:
        raise ValueError("rollout contains no actor-controlled samples")
    ratio = (replay.log_prob - old_log_prob).exp()
    unclipped = -advantages * ratio
    clipped = -advantages * torch.clamp(ratio, 1.0 - clip_coef, 1.0 + clip_coef)
    policy = (torch.maximum(unclipped, clipped) * weights).sum() / denominator
    entropy = (replay.entropy * weights).sum() / denominator
    return policy - entropy_coef * entropy


def recurrent_training_checkpoint(
    agent: RecurrentSGMAPPO,
    optimizer: torch.optim.Optimizer,
    hidden: torch.Tensor,
    *,
    update: int,
    auxiliary: dict[str, Any],
) -> dict[str, Any]:
    """Exact pilot state; caller supplies gates, belief, envs and value model."""
    return {
        "format": "active_diagnosis_recurrent_sg_mappo_v1",
        "update": int(update),
        "model": agent.state_dict(),
        "optimizer": optimizer.state_dict(),
        "hidden": hidden.detach().cpu().clone(),
        "auxiliary": auxiliary,
        "torch_rng": torch.get_rng_state(),
        "numpy_rng": np.random.get_state(),
        "python_rng": random.getstate(),
    }


def load_recurrent_training_checkpoint(
    payload: dict[str, Any],
    agent: RecurrentSGMAPPO,
    optimizer: torch.optim.Optimizer,
) -> tuple[int, torch.Tensor, dict[str, Any]]:
    if payload.get("format") != "active_diagnosis_recurrent_sg_mappo_v1":
        raise ValueError("incompatible recurrent training checkpoint")
    agent.load_state_dict(payload["model"])
    optimizer.load_state_dict(payload["optimizer"])
    torch.set_rng_state(payload["torch_rng"])
    np.random.set_state(payload["numpy_rng"])
    random.setstate(payload["python_rng"])
    return int(payload["update"]), payload["hidden"].clone(), payload["auxiliary"]
