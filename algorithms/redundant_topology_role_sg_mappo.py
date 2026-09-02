"""P2.6 corrected role-shared SG-MAPPO interface.

This is intentionally separate from the historical P2 learner.  Scouts share
one actor, relays share one actor, and terminals share one actor; no policy-body
parameter is shared across roles.  Relay has exactly one PASS/IDLE action.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import torch
import torch.nn as nn
from torch.distributions import Categorical

from algorithms.redundant_topology_sg_mappo import GraphLayer

SCOUT, RELAY, TERMINAL = 0, 1, 2
ROLE_ACTION_DIMS: Mapping[int, int] = {SCOUT: 3, RELAY: 1, TERMINAL: 3}


class RoleActor(nn.Module):
    """An independent graph-policy body used by all instances of one role."""
    def __init__(self, obs_dim: int, role: int, action_dim: int, hidden: int = 96, role_dim: int = 8):
        super().__init__()
        self.role_id, self.action_dim = role, action_dim
        self.role_embedding = nn.Embedding(3, role_dim)  # retained, harmless contextual identity
        self.input = nn.Sequential(nn.Linear(obs_dim + role_dim, hidden), nn.Tanh())
        self.g1, self.g2 = GraphLayer(hidden), GraphLayer(hidden)
        self.head = nn.Sequential(nn.Linear(hidden, hidden), nn.Tanh(), nn.Linear(hidden, action_dim))

    def forward(self, obs: torch.Tensor, roles: torch.Tensor, adj: torch.Tensor) -> torch.Tensor:
        x = self.input(torch.cat((obs, self.role_embedding(roles.long())), -1))
        x = self.g2(self.g1(x, adj), adj)
        return self.head(x)


class RoleSharedSGMPPO(nn.Module):
    """Corrected policy interface, with an unchanged centralized critic shape."""
    def __init__(self, obs_dim: int, share_dim: int, action_dim: int, hidden: int = 96, role_dim: int = 8):
        super().__init__()
        if action_dim != 3:
            raise ValueError("P2.6 freezes two-objective scout/terminal action dim = 3")
        self.scout_actor = RoleActor(obs_dim, SCOUT, 3, hidden, role_dim)
        self.relay_actor = RoleActor(obs_dim, RELAY, 1, hidden, role_dim)
        self.terminal_actor = RoleActor(obs_dim, TERMINAL, 3, hidden, role_dim)
        # Byte-for-byte architecture of the historical P2 critic, only actor wiring differs.
        self.critic = nn.Sequential(nn.Linear(share_dim, hidden), nn.Tanh(), nn.Linear(hidden, hidden), nn.Tanh(), nn.Linear(hidden, 1))

    @property
    def role_actors(self) -> Mapping[int, RoleActor]:
        return {SCOUT: self.scout_actor, RELAY: self.relay_actor, TERMINAL: self.terminal_actor}

    def action_value(self, obs: torch.Tensor, roles: torch.Tensor, adj: torch.Tensor, masks: torch.Tensor, share: torch.Tensor,
                     action: torch.Tensor | None = None, deterministic: bool = False):
        b, n, _ = obs.shape
        actions = torch.zeros((b, n), dtype=torch.long, device=obs.device) if action is None else action.clone().long()
        logp = torch.zeros((b, n), dtype=torch.float32, device=obs.device)
        entropy = torch.zeros((b, n), dtype=torch.float32, device=obs.device)
        for role, actor in self.role_actors.items():
            logits = actor(obs, roles, adj)
            positions = roles == role
            if role == RELAY:
                # One action: its categorical log-prob and entropy are exactly zero.
                actions = torch.where(positions, torch.zeros_like(actions), actions)
                continue
            selected_logits = logits[positions]
            selected_masks = masks[positions][:, :actor.action_dim]
            selected_logits = selected_logits.masked_fill(selected_masks <= 0, -1e9)
            dist = Categorical(logits=selected_logits)
            selected_action = torch.argmax(dist.logits, -1) if action is None and deterministic else (dist.sample() if action is None else actions[positions])
            if torch.any(selected_action < 0) or torch.any(selected_action >= actor.action_dim):
                raise ValueError("role action outside its frozen legal head")
            actions[positions] = selected_action
            logp[positions] = dist.log_prob(selected_action)
            entropy[positions] = dist.entropy()
        value = self.critic(share).squeeze(-1).unsqueeze(-1).expand_as(actions).float()
        return actions, logp, entropy, value

    def actor_parameter_sets(self) -> Mapping[str, set[int]]:
        return {name: {id(p) for p in actor.parameters()} for name, actor in (("scout", self.scout_actor), ("relay", self.relay_actor), ("terminal", self.terminal_actor))}
