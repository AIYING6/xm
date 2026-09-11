"""Minimal shared-actor, centralized-critic PPO baseline for M1.

This is deliberately a plain baseline: it has no freshness--uncertainty
marginal-value tensor, graph module, auxiliary task, recurrence, curriculum or
privileged actor information.
"""
from __future__ import annotations

import torch
from torch import nn
from torch.distributions import Categorical


class M1UTRPPO(nn.Module):
    def __init__(self, obs_dim: int = 22, critic_dim: int = 23, hidden_dim: int = 96, action_dim: int = 5):
        super().__init__()
        self.actor = nn.Sequential(
            nn.Linear(obs_dim, hidden_dim), nn.Tanh(),
            nn.Linear(hidden_dim, hidden_dim), nn.Tanh(),
            nn.Linear(hidden_dim, action_dim),
        )
        self.critic = nn.Sequential(
            nn.Linear(critic_dim, hidden_dim), nn.Tanh(),
            nn.Linear(hidden_dim, hidden_dim), nn.Tanh(),
            nn.Linear(hidden_dim, 1),
        )

    def action_distribution(self, actor_obs: torch.Tensor, action_masks: torch.Tensor) -> Categorical:
        logits = self.actor(actor_obs)
        logits = logits.masked_fill(action_masks <= 0, -1.0e9)
        return Categorical(logits=logits)

    def value(self, critic_obs: torch.Tensor) -> torch.Tensor:
        return self.critic(critic_obs).squeeze(-1)
