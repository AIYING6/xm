"""Minimal vanilla actor for v1.6R continuous-guidance baselines."""
from __future__ import annotations

import torch
from torch import Tensor, nn

from .continuous_guidance_distribution import TanhGaussianGuidance


class ContinuousGuidanceActor(nn.Module):
    """Feed-forward actor; no memory, graph, or privileged input."""

    def __init__(self, obs_dim: int, hidden_dim: int = 128):
        super().__init__()
        self.backbone = nn.Sequential(
            nn.Linear(obs_dim, hidden_dim), nn.Tanh(),
            nn.Linear(hidden_dim, hidden_dim), nn.Tanh(),
        )
        self.mean_head = nn.Linear(hidden_dim, 2)
        self.log_std = nn.Parameter(torch.full((2,), -0.5))

    def distribution(self, obs: Tensor) -> TanhGaussianGuidance:
        hidden = self.backbone(obs)
        mean = self.mean_head(hidden)
        log_std = self.log_std.expand_as(mean).clamp(-5.0, 2.0)
        return TanhGaussianGuidance(mean, log_std)

    def forward(self, obs: Tensor, deterministic: bool = False):
        dist = self.distribution(obs)
        if deterministic:
            action = dist.deterministic()
            return action, dist.log_prob(action)
        return dist.sample()

