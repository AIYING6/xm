"""Minimal shared-actor, centralized-critic PPO reference for P41 T4.

This is intentionally a baseline-only learner.  It has no topology-specific
module, recurrence, adaptive sampling, curriculum, auxiliary loss, or access to
future request realization in the actor pathway.
"""
from __future__ import annotations

import torch
from torch import nn
from torch.distributions import Categorical


class P41UTRPPO(nn.Module):
    def __init__(self, obs_dim: int = 12, critic_dim: int = 6, hidden_dim: int = 64, action_dim: int = 3):
        super().__init__()
        self.actor = nn.Sequential(nn.Linear(obs_dim, hidden_dim), nn.Tanh(), nn.Linear(hidden_dim, hidden_dim), nn.Tanh(), nn.Linear(hidden_dim, action_dim))
        self.critic = nn.Sequential(nn.Linear(critic_dim, hidden_dim), nn.Tanh(), nn.Linear(hidden_dim, hidden_dim), nn.Tanh(), nn.Linear(hidden_dim, 1))

    def action_distribution(self, actor_obs: torch.Tensor) -> Categorical:
        # actor_obs: [batch, agent, local-feature]; no global critic state here.
        return Categorical(logits=self.actor(actor_obs))

    def value(self, critic_obs: torch.Tensor) -> torch.Tensor:
        return self.critic(critic_obs).squeeze(-1)
