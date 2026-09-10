"""Composable high-level recovery policies for the ACFID learning pilot."""
from __future__ import annotations

import torch
import torch.nn as nn


class ContextEncoder(nn.Module):
    def __init__(self, context_dim: int, hidden: int):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(context_dim, hidden), nn.Tanh(), nn.Linear(hidden, hidden), nn.Tanh())

    def forward(self, context: torch.Tensor) -> torch.Tensor:
        return self.net(context)


class AdditiveRecoveryPolicy(nn.Module):
    """Base recovery logits plus a shared primitive-fault main-effect head."""

    def __init__(self, context_dim: int, fault_dim: int, actions: int = 5, hidden: int = 64):
        super().__init__(); self.actions = actions
        self.context = ContextEncoder(context_dim, hidden)
        self.base = nn.Linear(hidden, actions)
        self.main = nn.Sequential(nn.Linear(hidden + fault_dim, hidden), nn.Tanh(), nn.Linear(hidden, actions))

    def forward(self, context: torch.Tensor, fault_features: torch.Tensor, active: torch.Tensor,
                pair_relations: torch.Tensor | None = None) -> torch.Tensor:
        encoded = self.context(context); batch, faults, _ = fault_features.shape
        expanded = encoded[:, None, :].expand(batch, faults, encoded.shape[-1])
        effects = self.main(torch.cat((expanded, fault_features), dim=-1)) * active[..., None]
        return self.base(encoded) + effects.sum(dim=1)


class ACFIDRecoveryPolicy(AdditiveRecoveryPolicy):
    """Additive policy plus shared action-conditioned pair interactions.

    ``pair_relations`` is a precomputed, causal relation descriptor.  No pair
    identity embedding is used, so held-out fault pairs have no unseen lookup
    parameters.
    """

    def __init__(self, context_dim: int, fault_dim: int, relation_dim: int, actions: int = 5, hidden: int = 64):
        super().__init__(context_dim, fault_dim, actions, hidden)
        self.interaction = nn.Sequential(
            nn.Linear(hidden + 2 * fault_dim + relation_dim, hidden), nn.Tanh(), nn.Linear(hidden, actions)
        )

    def forward(self, context: torch.Tensor, fault_features: torch.Tensor, active: torch.Tensor,
                pair_relations: torch.Tensor) -> torch.Tensor:
        logits = super().forward(context, fault_features, active)
        encoded = self.context(context); faults = fault_features.shape[1]
        interaction_sum = torch.zeros_like(logits)
        for i in range(faults):
            for j in range(i + 1, faults):
                # Symmetric descriptor prevents arbitrary fault ordering from
                # becoming a hidden pair identifier.
                lo = torch.minimum(fault_features[:, i], fault_features[:, j])
                hi = torch.maximum(fault_features[:, i], fault_features[:, j])
                pair_input = torch.cat((encoded, lo, hi, pair_relations[:, i, j]), dim=-1)
                mask = (active[:, i] * active[:, j])[:, None]
                interaction_sum = interaction_sum + self.interaction(pair_input) * mask
        return logits + interaction_sum


class DirectFaultAwareRecoveryPolicy(nn.Module):
    """Non-compositional fixed-fault-count control policy."""

    def __init__(self, context_dim: int, fault_dim: int, fault_count: int = 6, actions: int = 5, hidden: int = 96):
        super().__init__(); self.fault_count = fault_count
        self.net = nn.Sequential(
            nn.Linear(context_dim + fault_count * (fault_dim + 1), hidden), nn.Tanh(),
            nn.Linear(hidden, hidden), nn.Tanh(), nn.Linear(hidden, actions),
        )

    def forward(self, context: torch.Tensor, fault_features: torch.Tensor, active: torch.Tensor,
                pair_relations: torch.Tensor | None = None) -> torch.Tensor:
        if fault_features.shape[1] != self.fault_count:
            raise ValueError("direct baseline freezes the primitive-fault registry")
        return self.net(torch.cat((context, fault_features.flatten(1), active), dim=-1))


def parameter_count(module: nn.Module) -> int:
    return sum(parameter.numel() for parameter in module.parameters() if parameter.requires_grad)
