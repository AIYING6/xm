"""Identity-preserving acquisition control for the M2R development repair.

This is deliberately a policy interface, not a new training objective.  The
base (B1) control path always emits the complete hybrid-action distribution.
Full adds only a zero-initialized, bounded residual to turn and climb means;
the Bernoulli commit logit and continuous-action scale are exactly untouched.
"""
from __future__ import annotations

from dataclasses import dataclass

import torch
from torch import nn

from algorithms.ri_gmappo.acquisition_oriented import (
    SELF_HISTORY_INDICES,
    TARGET_HISTORY_INDICES,
    AcquisitionHistoryState,
    LegalTargetHistory,
)


class IdentityPreservingAcquisitionCore(nn.Module):
    """Legal target/self histories plus a progress latent for a bounded residual."""

    def __init__(self, obs_dim: int, hidden_dim: int = 128, progress_dim: int = 16):
        super().__init__()
        self.hidden_dim, self.progress_dim = hidden_dim, progress_dim
        self.target_history = LegalTargetHistory(len(TARGET_HISTORY_INDICES), hidden_dim)
        self.self_history = nn.GRUCell(len(SELF_HISTORY_INDICES) + 3, hidden_dim)
        self.progress_encoder = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim), nn.Tanh(), nn.Linear(hidden_dim, progress_dim), nn.Tanh()
        )
        self.obs_dim = obs_dim

    def initial_state(self, obs: torch.Tensor) -> AcquisitionHistoryState:
        shape = (*obs.shape[:-1], self.hidden_dim)
        return AcquisitionHistoryState(obs.new_zeros(shape), obs.new_zeros(shape))

    def forward_step(self, obs, previous_action, evidence_valid, state=None):
        if evidence_valid.shape != obs.shape[:-1]:
            raise ValueError("evidence mask must align with actor observations")
        if previous_action.shape != (*obs.shape[:-1], 3):
            raise ValueError("previous action must be the executed hybrid action")
        if state is None:
            state = self.initial_state(obs)
        target_input = obs[..., TARGET_HISTORY_INDICES]
        self_input = obs[..., SELF_HISTORY_INDICES]
        target_next = self.target_history(target_input, evidence_valid, state.target)
        self_flat = torch.cat([self_input, previous_action], dim=-1).reshape(-1, len(SELF_HISTORY_INDICES) + 3)
        self_next = self.self_history(self_flat, state.self_state.reshape(-1, self.hidden_dim)).reshape_as(target_next)
        progress = self.progress_encoder(torch.cat([target_next, self_next], dim=-1))
        return self_next + target_next, progress, AcquisitionHistoryState(target_next, self_next)


class IdentityPreservingResidualPolicy(nn.Module):
    """Paired Full/B1 policy with an optional, bounded progress residual.

    Full and B1 have exactly the same parameters.  B1 simply does not route
    its matched residual branch into action logits.  At initialization Full is
    therefore exactly B1; thereafter only continuous guidance means may differ.
    """

    residual_limit = 0.25

    def __init__(self, obs_dim: int, num_roles: int = 4, hidden_dim: int = 128, progress_dim: int = 16, *, full: bool):
        super().__init__()
        self.full = full
        self.core = IdentityPreservingAcquisitionCore(obs_dim, hidden_dim, progress_dim)
        self.role_heads = nn.ModuleList([
            nn.Sequential(nn.Linear(hidden_dim, hidden_dim), nn.Tanh(), nn.Linear(hidden_dim, 5))
            for _ in range(num_roles)
        ])
        # Both arms own the same residual head count and shape.  Only Full
        # routes the output to action means; B1 is a capacity-matched base.
        self.progress_residual_heads = nn.ModuleList([nn.Linear(progress_dim, 2) for _ in range(num_roles)])
        for head in self.progress_residual_heads:
            nn.init.zeros_(head.weight); nn.init.zeros_(head.bias)

    def residual(self, progress: torch.Tensor, role: torch.Tensor) -> torch.Tensor:
        flat = progress.reshape(-1, progress.shape[-1])
        roles = role.reshape(-1).long().clamp(0, len(self.role_heads) - 1)
        raw = flat.new_zeros((flat.shape[0], 2))
        for role_id, head in enumerate(self.progress_residual_heads):
            mask = roles == role_id
            if torch.any(mask): raw[mask] = head(flat[mask])
        return (self.residual_limit * torch.tanh(raw)).reshape(*progress.shape[:-1], 2)

    def forward_step(self, obs, previous_action, evidence_valid, role, state=None):
        base, progress, next_state = self.core.forward_step(obs, previous_action, evidence_valid, state)
        flat, roles = base.reshape(-1, base.shape[-1]), role.reshape(-1).long().clamp(0, len(self.role_heads) - 1)
        base_logits = flat.new_zeros((flat.shape[0], 5))
        for role_id, head in enumerate(self.role_heads):
            mask = roles == role_id
            if torch.any(mask): base_logits[mask] = head(flat[mask])
        logits = base_logits.reshape(*base.shape[:-1], 5)
        if self.full:
            logits = logits.clone()
            logits[..., :2] = logits[..., :2] + self.residual(progress, role)
        return logits, progress, next_state
