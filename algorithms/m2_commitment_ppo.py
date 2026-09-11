"""Plain shared-actor, centralized-critic PPO for the M2 task.

This baseline intentionally contains no forecast-specific mechanism, memory,
graph encoder, auxiliary loss, curriculum, or privileged observation.
"""
from __future__ import annotations

import torch
from torch import nn
from torch.distributions import Categorical


class M2PlainMAPPO(nn.Module):
    def __init__(self, obs_dim: int = 8, critic_dim: int = 8, hidden_dim: int = 96, action_dim: int = 4):
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
        logits = self.actor(actor_obs).masked_fill(action_masks <= 0, -1.0e9)
        return Categorical(logits=logits)

    def value(self, critic_obs: torch.Tensor) -> torch.Tensor:
        return self.critic(critic_obs).squeeze(-1)
