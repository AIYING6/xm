"""Minimal vanilla actor for v1.6R continuous-guidance baselines."""
from __future__ import annotations

import torch
from torch import Tensor, nn

from .continuous_guidance_distribution import TanhGaussianGuidance


class ContinuousGuidanceActor(nn.Module):
    """Feed-forward actor; no memory, graph, or privileged input."""

    def __init__(self, obs_dim: int, hidden_dim: int = 128, role_specific: bool = False):
        super().__init__()
        self.backbone = nn.Sequential(
            nn.Linear(obs_dim, hidden_dim), nn.Tanh(),
            nn.Linear(hidden_dim, hidden_dim), nn.Tanh(),
        )
        self.role_specific = role_specific
        self.mean_head = nn.Linear(hidden_dim, 2)
        self.role_heads = nn.ModuleList([nn.Linear(hidden_dim, 2) for _ in range(4)]) if role_specific else None
        self.log_std = nn.Parameter(torch.full((2,), -0.5))

    def distribution(self, obs: Tensor) -> TanhGaussianGuidance:
        hidden = self.backbone(obs)
        if self.role_specific:
            # OBS3D role one-hot is fixed at [24:28]; for stacked history use
            # the final frame's slice.
            role_start = (obs.shape[-1] - 34) + 24 if obs.shape[-1] >= 34 else 24
            role_ids = obs[..., role_start:role_start + 4].argmax(dim=-1)
            mean = torch.stack([head(hidden) for head in self.role_heads], dim=-2)
            mean = mean.gather(-2, role_ids.unsqueeze(-1).unsqueeze(-1).expand(*role_ids.shape, 1, 2)).squeeze(-2)
        else:
            mean = self.mean_head(hidden)
        log_std = self.log_std.expand_as(mean).clamp(-5.0, 2.0)
        return TanhGaussianGuidance(mean, log_std)

    def forward(self, obs: Tensor, deterministic: bool = False):
        dist = self.distribution(obs)
        if deterministic:
            action = dist.deterministic()
            return action, dist.log_prob(action)
        return dist.sample()
