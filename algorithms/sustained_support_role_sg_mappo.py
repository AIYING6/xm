"""Role-shared graph MAPPO policy for the independent 6-UAV V3 task.

Unlike the legacy 6-UAV task, V3 relays select one of two objectives or idle.
This module changes only the task-required relay action head. Any future UTR
and DRTP run must instantiate this exact same policy class.
"""
from __future__ import annotations

from typing import Mapping

import torch
import torch.nn as nn
from torch.distributions import Categorical

from algorithms.redundant_topology_sg_mappo import GraphLayer

SCOUT, RELAY, TERMINAL = 0, 1, 2
V3_ROLE_ACTION_DIMS: Mapping[int, int] = {SCOUT: 3, RELAY: 3, TERMINAL: 3}


class V3RoleActor(nn.Module):
    def __init__(self, obs_dim: int, role: int, action_dim: int, hidden: int = 96, role_dim: int = 8):
        super().__init__()
        self.action_dim = action_dim
        self.role_embedding = nn.Embedding(3, role_dim)
        self.input = nn.Sequential(nn.Linear(obs_dim + role_dim, hidden), nn.Tanh())
        self.g1, self.g2 = GraphLayer(hidden), GraphLayer(hidden)
        self.head = nn.Sequential(nn.Linear(hidden, hidden), nn.Tanh(), nn.Linear(hidden, action_dim))

    def forward(self, obs: torch.Tensor, roles: torch.Tensor, adjacency: torch.Tensor) -> torch.Tensor:
        value = self.input(torch.cat((obs, self.role_embedding(roles.long())), dim=-1))
        return self.head(self.g2(self.g1(value, adjacency), adjacency))


class SustainedSupportRoleSharedSGMPPO(nn.Module):
    """Equal-capacity role-shared policy for every future V3 comparison arm."""
    def __init__(self, obs_dim: int, share_dim: int, hidden: int = 96, role_dim: int = 8):
        super().__init__()
        self.role_actors = nn.ModuleDict({str(role): V3RoleActor(obs_dim, role, action_dim, hidden, role_dim) for role, action_dim in V3_ROLE_ACTION_DIMS.items()})
        self.critic = nn.Sequential(nn.Linear(share_dim, hidden), nn.Tanh(), nn.Linear(hidden, hidden), nn.Tanh(), nn.Linear(hidden, 1))

    def action_value(self, obs: torch.Tensor, roles: torch.Tensor, adjacency: torch.Tensor, masks: torch.Tensor, share: torch.Tensor,
                     action: torch.Tensor | None = None, deterministic: bool = False):
        batch, agents, _ = obs.shape
        actions = torch.zeros((batch, agents), dtype=torch.long, device=obs.device) if action is None else action.clone().long()
        logp = torch.zeros((batch, agents), dtype=torch.float32, device=obs.device)
        entropy = torch.zeros((batch, agents), dtype=torch.float32, device=obs.device)
        for role, action_dim in V3_ROLE_ACTION_DIMS.items():
            positions = roles == role
            logits = self.role_actors[str(role)](obs, roles, adjacency)
            selected_logits = logits[positions]
            selected_masks = masks[positions][:, :action_dim]
            if torch.any(selected_masks.sum(dim=-1) <= 0):
                raise RuntimeError("V3 action mask removed every legal action")
            distribution = Categorical(logits=selected_logits.masked_fill(selected_masks <= 0, -1e9))
            selected = torch.argmax(distribution.logits, dim=-1) if action is None and deterministic else (distribution.sample() if action is None else actions[positions])
            if torch.any(selected < 0) or torch.any(selected >= action_dim):
                raise ValueError("action outside V3 role head")
            actions[positions] = selected
            logp[positions] = distribution.log_prob(selected)
            entropy[positions] = distribution.entropy()
        value = self.critic(share).squeeze(-1).unsqueeze(-1).expand_as(actions).float()
        return actions, logp, entropy, value


def v3_policy_spec() -> dict[str, object]:
    return {"policy": "SustainedSupportRoleSharedSGMPPO", "role_action_dims": dict(V3_ROLE_ACTION_DIMS), "shared_actor_within_role": True, "relay_decision_head": "idle_or_forward_objective"}
