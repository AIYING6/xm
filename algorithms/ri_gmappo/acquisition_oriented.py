"""Minimal acquisition-oriented actor core for the corrected L4 task.

This module deliberately has an explicit recurrent-state API.  The training
collector must carry ``target_state`` and ``self_state`` per recipient and
reset both at episode boundaries.  Crucially, target state is also reset when
the current actor observation has no *currently legal* target evidence; it
cannot act as an unlimited cache after a packet expires.

The module is not wired into a training launch in M2.  It exists so the M2
gate can verify the information and comparator contracts before any pilot is
authorised.
"""

from __future__ import annotations

from dataclasses import dataclass

import torch
from torch import nn

from envs.uav_intercept_3d_env import OBS3D_FIELD_NAMES


TARGET_VALUE_INDICES = tuple(range(8, 15))
# These fields describe the legality/freshness of target evidence and must not
# enter the target-free self-history recurrent state.
TARGET_EVIDENCE_INDICES = TARGET_VALUE_INDICES + (18, 19, 30, 31)
SELF_HISTORY_INDICES = tuple(index for index in range(len(OBS3D_FIELD_NAMES)) if index not in TARGET_EVIDENCE_INDICES)
TARGET_HISTORY_INDICES = TARGET_VALUE_INDICES + (18, 30, 31)


@dataclass(frozen=True)
class AcquisitionHistoryState:
    """Explicit, serialisable recurrent state for a batch of actor views."""

    target: torch.Tensor
    self_state: torch.Tensor


class LegalTargetHistory(nn.Module):
    """GRU whose target content is zeroed and reset whenever evidence expires."""

    def __init__(self, input_dim: int, hidden_dim: int):
        super().__init__()
        self.cell = nn.GRUCell(input_dim, hidden_dim)
        self.hidden_dim = hidden_dim

    def forward(
        self,
        target_features: torch.Tensor,
        evidence_valid: torch.Tensor,
        state: torch.Tensor | None = None,
    ) -> torch.Tensor:
        if evidence_valid.ndim != target_features.ndim - 1:
            raise ValueError("evidence_valid must be one boolean per actor view")
        valid = evidence_valid.to(dtype=torch.bool).reshape(-1)
        flat = target_features.reshape(-1, target_features.shape[-1])
        if state is None:
            state = flat.new_zeros((flat.shape[0], self.hidden_dim))
        else:
            state = state.reshape(-1, self.hidden_dim)
        # Reset before and after the cell.  The second reset makes the expiry
        # property robust even if GRU biases are non-zero.
        state = torch.where(valid.unsqueeze(-1), state, torch.zeros_like(state))
        next_state = self.cell(flat * valid.unsqueeze(-1).to(flat.dtype), state)
        return torch.where(valid.unsqueeze(-1), next_state, torch.zeros_like(next_state)).reshape(*target_features.shape[:-1], self.hidden_dim)


class AcquisitionOrientedCore(nn.Module):
    """Shared legal-history core for Full and history/capacity-matched B1.

    ``full=True`` uses a progress latent to multiplicatively modulate target
    history before fusion.  ``full=False`` uses exactly the same parameter
    shapes and legal histories, but direct fusion instead.  This is the M2
    primary comparator boundary: no raw input, recurrent history, reward, or
    action-semantic difference is permitted.
    """

    def __init__(self, obs_dim: int, hidden_dim: int = 128, progress_dim: int = 16, *, full: bool):
        super().__init__()
        if obs_dim < len(OBS3D_FIELD_NAMES):
            raise ValueError(f"expected corrected 3DOF actor vector with >= {len(OBS3D_FIELD_NAMES)} fields")
        self.obs_dim = obs_dim
        self.hidden_dim = hidden_dim
        self.full = full
        self.target_history = LegalTargetHistory(len(TARGET_HISTORY_INDICES), hidden_dim)
        # The previous *executed* hybrid action is target-free and is passed
        # explicitly, preventing any future action leakage.
        self.self_history = nn.GRUCell(len(SELF_HISTORY_INDICES) + 3, hidden_dim)
        # Both arms contain these exact layers.  Their use, rather than their
        # capacity or legal input, is the only Full/B1 distinction.
        self.progress_encoder = nn.Sequential(nn.Linear(hidden_dim * 2, hidden_dim), nn.Tanh(), nn.Linear(hidden_dim, progress_dim), nn.Tanh())
        self.fusion_projection = nn.Sequential(nn.Linear(progress_dim, hidden_dim), nn.Tanh())

    @staticmethod
    def split_observation(obs: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        return obs[..., TARGET_HISTORY_INDICES], obs[..., SELF_HISTORY_INDICES]

    @staticmethod
    def validate_evidence_mask(evidence_valid: torch.Tensor, obs: torch.Tensor) -> None:
        if evidence_valid.shape != obs.shape[:-1]:
            raise ValueError("evidence_valid must align with obs batch dimensions")

    def initial_state(self, obs: torch.Tensor) -> AcquisitionHistoryState:
        shape = (*obs.shape[:-1], self.hidden_dim)
        return AcquisitionHistoryState(target=obs.new_zeros(shape), self_state=obs.new_zeros(shape))

    def forward_step(
        self,
        obs: torch.Tensor,
        previous_action: torch.Tensor,
        evidence_valid: torch.Tensor,
        state: AcquisitionHistoryState | None = None,
    ) -> tuple[torch.Tensor, torch.Tensor, AcquisitionHistoryState]:
        """Return fused features, progress latent, and next explicit state.

        ``evidence_valid`` is a canonical boolean derived from the existing
        actor contract (local sensing OR delivered/cache-valid evidence).  It
        conveys no new target information and is intentionally required rather
        than inferred from target coordinates.
        """
        self.validate_evidence_mask(evidence_valid, obs)
        if previous_action.shape != (*obs.shape[:-1], 3):
            raise ValueError("previous_action must be [..., 3] hybrid action")
        if state is None:
            state = self.initial_state(obs)
        target_input, self_input = self.split_observation(obs)
        target_next = self.target_history(target_input, evidence_valid, state.target)
        self_flat = torch.cat([self_input, previous_action], dim=-1).reshape(-1, len(SELF_HISTORY_INDICES) + 3)
        previous_self = state.self_state.reshape(-1, self.hidden_dim)
        self_next = self.self_history(self_flat, previous_self).reshape_as(target_next)
        progress = self.progress_encoder(torch.cat([target_next, self_next], dim=-1))
        projection = self.fusion_projection(progress)
        if self.full:
            # Progress-conditioned modulation: B1 intentionally does not
            # multiply target history by this inferred control signal.
            fused = self_next + torch.sigmoid(projection) * target_next
        else:
            fused = self_next + target_next + projection
        return fused, progress, AcquisitionHistoryState(target=target_next, self_state=self_next)


class AcquisitionOrientedHybridPolicy(nn.Module):
    """Role-head-compatible minimal policy wrapper around the paired core."""

    def __init__(self, obs_dim: int, num_roles: int, hidden_dim: int = 128, progress_dim: int = 16, *, full: bool):
        super().__init__()
        self.core = AcquisitionOrientedCore(obs_dim, hidden_dim, progress_dim, full=full)
        self.role_heads = nn.ModuleList(
            [nn.Sequential(nn.Linear(hidden_dim, hidden_dim), nn.Tanh(), nn.Linear(hidden_dim, 5)) for _ in range(num_roles)]
        )

    def forward_step(self, obs: torch.Tensor, previous_action: torch.Tensor, evidence_valid: torch.Tensor, role: torch.Tensor, state: AcquisitionHistoryState | None = None):
        fused, progress, next_state = self.core.forward_step(obs, previous_action, evidence_valid, state)
        flat = fused.reshape(-1, fused.shape[-1])
        roles = role.reshape(-1).long().clamp(0, len(self.role_heads) - 1)
        logits = flat.new_zeros((flat.shape[0], 5))
        for role_id, head in enumerate(self.role_heads):
            mask = roles == role_id
            if torch.any(mask):
                logits[mask] = head(flat[mask])
        return logits.reshape(*fused.shape[:-1], 5), progress, next_state

