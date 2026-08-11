"""Transparent unified-graph baseline for v1.6R (not TEAR)."""
from __future__ import annotations

import torch
from torch import Tensor, nn

from .continuous_guidance_distribution import TanhGaussianGuidance


class RecipientGraphGuidanceActor(nn.Module):
    """Mean-pool legal recipient graph evidence with no temporal alignment."""

    def __init__(self, obs_dim: int, node_dim: int = 20, relation_dim: int = 2, hidden_dim: int = 128):
        super().__init__()
        self.encoder = nn.Sequential(nn.Linear(node_dim + relation_dim, hidden_dim), nn.Tanh())
        self.fuse = nn.Sequential(nn.Linear(obs_dim + hidden_dim, hidden_dim), nn.Tanh())
        self.mean_head = nn.Linear(hidden_dim, 2)
        self.log_std = nn.Parameter(torch.full((2,), -0.5))

    def distribution(self, obs: Tensor, graph_node: Tensor, graph_relation_adj: Tensor) -> TanhGaussianGuidance:
        if obs.ndim != 2 or graph_node.ndim != 3 or graph_relation_adj.ndim != 4:
            raise ValueError("expected obs [N,D], node [N,V,F], relation [N,R,V,V]")
        relation_summary = graph_relation_adj.mean(dim=(-1, -2))
        node_aug = torch.cat([graph_node, relation_summary.unsqueeze(1).expand(-1, graph_node.shape[1], -1)], dim=-1)
        pooled = self.encoder(node_aug).mean(dim=1)
        hidden = self.fuse(torch.cat([obs, pooled], dim=-1))
        mean = self.mean_head(hidden)
        return TanhGaussianGuidance(mean, self.log_std.expand_as(mean).clamp(-5.0, 2.0))

    def forward(self, obs: Tensor, graph_node: Tensor, graph_relation_adj: Tensor, deterministic: bool = False):
        dist = self.distribution(obs, graph_node, graph_relation_adj)
        if deterministic:
            action = dist.deterministic()
            return action, dist.log_prob(action)
        return dist.sample()
