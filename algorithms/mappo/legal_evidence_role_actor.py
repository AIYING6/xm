"""Minimal Legal-Evidence Role-Conditioned MAPPO actor.

The gate is deliberately explicit: callers must provide the recipient-local
legal evidence mask produced by ``LegalObservationInterface``.  No global
target state or critic input is accepted by this module.
"""
from __future__ import annotations

import torch
from torch import Tensor, nn

from .continuous_guidance_distribution import TanhGaussianGuidance


class LegalEvidenceRoleActor(nn.Module):
    def __init__(self, obs_dim: int, num_roles: int = 4, hidden_dim: int = 128):
        super().__init__()
        self.encoder = nn.Sequential(nn.Linear(obs_dim, hidden_dim), nn.Tanh())
        self.role_heads = nn.ModuleList([nn.Linear(hidden_dim, 2) for _ in range(num_roles)])
        self.gate = nn.Sequential(nn.Linear(1, hidden_dim), nn.Sigmoid())
        self.log_std = nn.Parameter(torch.full((2,), -0.5))

    def distribution(self, obs: Tensor, role_ids: Tensor, evidence_mask: Tensor) -> TanhGaussianGuidance:
        if obs.ndim != 2 or role_ids.ndim != 1 or evidence_mask.ndim != 1:
            raise ValueError("expected obs [N,D], role_ids [N], evidence_mask [N]")
        if obs.shape[0] != role_ids.shape[0] or obs.shape[0] != evidence_mask.shape[0]:
            raise ValueError("recipient dimensions must match")
        h = self.encoder(obs)
        # Evidence gate only scales the legal actor representation; it cannot
        # create evidence or alter the binary engage_commit head.
        h = h * self.gate(evidence_mask.float().unsqueeze(-1))
        means = torch.stack([head(h) for head in self.role_heads], dim=1)
        mean = means[torch.arange(obs.shape[0], device=obs.device), role_ids.long()]
        return TanhGaussianGuidance(mean, self.log_std.expand_as(mean).clamp(-5.0, 2.0))

    def forward(self, obs: Tensor, role_ids: Tensor, evidence_mask: Tensor, deterministic: bool = False):
        dist = self.distribution(obs, role_ids, evidence_mask)
        if deterministic:
            action = dist.deterministic()
            return action, dist.log_prob(action)
        return dist.sample()
