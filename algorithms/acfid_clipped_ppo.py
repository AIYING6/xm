"""Matched one-decision clipped-PPO utilities for the ACFID pilot."""
from __future__ import annotations

from dataclasses import dataclass

import torch
import torch.nn as nn
from torch.distributions import Categorical


class InvariantRecoveryCritic(nn.Module):
    """Common critic that cannot encode a fault-combination identity lookup."""

    def __init__(self, context_dim: int, fault_dim: int, hidden: int = 64):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(context_dim + fault_dim + 1, hidden), nn.Tanh(),
            nn.Linear(hidden, hidden), nn.Tanh(), nn.Linear(hidden, 1),
        )

    def forward(self, context: torch.Tensor, fault_features: torch.Tensor,
                active: torch.Tensor) -> torch.Tensor:
        active_count = active.sum(dim=1, keepdim=True).clamp_min(1.0)
        pooled = (fault_features * active[..., None]).sum(dim=1) / active_count
        pooled = torch.where(active_count > 0, pooled, torch.zeros_like(pooled))
        return self.net(torch.cat((context, pooled, active.sum(dim=1, keepdim=True)), dim=-1)).squeeze(-1)


@dataclass
class PPOBatch:
    context: torch.Tensor
    fault_features: torch.Tensor
    active: torch.Tensor
    pair_relations: torch.Tensor
    actions: torch.Tensor
    old_log_prob: torch.Tensor
    returns: torch.Tensor
    advantages: torch.Tensor


def ppo_loss(policy: nn.Module, critic: InvariantRecoveryCritic, batch: PPOBatch,
             clip_ratio: float = 0.2, value_coef: float = 0.5,
             entropy_coef: float = 0.01) -> tuple[torch.Tensor, dict[str, float]]:
    logits = policy(batch.context, batch.fault_features, batch.active, batch.pair_relations)
    distribution = Categorical(logits=logits)
    log_prob = distribution.log_prob(batch.actions)
    ratio = torch.exp(log_prob - batch.old_log_prob)
    normalized_advantage = (batch.advantages - batch.advantages.mean()) / (batch.advantages.std() + 1e-8)
    clipped = torch.clamp(ratio, 1.0 - clip_ratio, 1.0 + clip_ratio) * normalized_advantage
    policy_loss = -torch.minimum(ratio * normalized_advantage, clipped).mean()
    values = critic(batch.context, batch.fault_features, batch.active)
    value_loss = (values - batch.returns).square().mean()
    entropy = distribution.entropy().mean()
    loss = policy_loss + value_coef * value_loss - entropy_coef * entropy
    return loss, {"policy_loss": float(policy_loss.detach()), "value_loss": float(value_loss.detach()),
                  "entropy": float(entropy.detach()), "ratio_mean": float(ratio.mean().detach())}
