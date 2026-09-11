"""Small MAPPO models for the C1 posterior-identifiability pilot.

This module is intentionally independent from the maintained UAV learner.  It
implements only the public LBF pilot's four observation paths: feed-forward,
legal-history recurrent, posterior-conditioned recurrent, and a posterior-
shuffled control.  The critic is identical in every arm.
"""
from __future__ import annotations

import torch
from torch import nn
from torch.distributions import Categorical


class C1PilotMAPPO(nn.Module):
    """Shared actor plus centralized critic with optional legal-history state."""

    def __init__(
        self,
        *,
        obs_dim: int,
        critic_dim: int,
        action_dim: int,
        arm: str,
        hidden_dim: int = 96,
    ) -> None:
        super().__init__()
        if arm not in {"ff_mappo", "recurrent_mappo", "bc3_mappo", "shuffled_bc3_mappo"}:
            raise ValueError(f"unknown C1 pilot arm: {arm}")
        self.arm = arm
        self.action_dim = action_dim
        self.uses_memory = arm != "ff_mappo"
        self.uses_posterior = arm in {"bc3_mappo", "shuffled_bc3_mappo"}
        actor_input = obs_dim + (1 if self.uses_posterior else 0)
        if self.uses_memory:
            self.actor_cell = nn.GRUCell(actor_input, hidden_dim)
            self.actor_head = nn.Linear(hidden_dim, action_dim)
        else:
            self.actor = nn.Sequential(
                nn.Linear(actor_input, hidden_dim), nn.Tanh(),
                nn.Linear(hidden_dim, hidden_dim), nn.Tanh(),
                nn.Linear(hidden_dim, action_dim),
            )
        self.critic = nn.Sequential(
            nn.Linear(critic_dim, hidden_dim), nn.Tanh(),
            nn.Linear(hidden_dim, hidden_dim), nn.Tanh(),
            nn.Linear(hidden_dim, 1),
        )
        self.hidden_dim = hidden_dim

    def initial_memory(self, batch: int, agents: int, *, device: torch.device | str) -> torch.Tensor:
        return torch.zeros((batch, agents, self.hidden_dim), dtype=torch.float32, device=device)

    def _actor_input(self, obs: torch.Tensor, posterior: torch.Tensor | None) -> torch.Tensor:
        if not self.uses_posterior:
            return obs
        if posterior is None:
            raise ValueError("BC3 arm requires a legal posterior tensor")
        if posterior.shape != obs.shape[:2]:
            raise ValueError("posterior must have shape [batch, agents]")
        return torch.cat((obs, posterior.unsqueeze(-1)), dim=-1)

    def action_distribution(
        self,
        obs: torch.Tensor,
        masks: torch.Tensor,
        *,
        memory: torch.Tensor | None = None,
        posterior: torch.Tensor | None = None,
    ) -> tuple[Categorical, torch.Tensor | None]:
        actor_input = self._actor_input(obs, posterior)
        if self.uses_memory:
            if memory is None:
                memory = self.initial_memory(obs.shape[0], obs.shape[1], device=obs.device)
            next_memory = self.actor_cell(
                actor_input.reshape(-1, actor_input.shape[-1]),
                memory.reshape(-1, memory.shape[-1]),
            ).reshape_as(memory)
            logits = self.actor_head(next_memory)
        else:
            next_memory = None
            logits = self.actor(actor_input)
        return Categorical(logits=logits.masked_fill(masks <= 0, -1.0e9)), next_memory

    def value(self, critic_obs: torch.Tensor) -> torch.Tensor:
        return self.critic(critic_obs).squeeze(-1)


def update_capability_posterior(
    posterior: torch.Tensor,
    *,
    joint_load_receipt: torch.Tensor,
    public_team_reward: torch.Tensor,
) -> torch.Tensor:
    """Update a legal probability feature from a public joint-load outcome.

    This is a deliberately fixed diagnostic filter, not a true-capability
    label.  A joint request followed by non-positive public reward shifts mass
    toward insufficient teammate capability; a positive outcome shifts mass in
    the opposite direction.  With no public joint request the feature is held.
    """
    if posterior.shape != joint_load_receipt.shape:
        raise ValueError("receipt and posterior shapes must match")
    if public_team_reward.shape != posterior.shape:
        raise ValueError("public reward and posterior shapes must match")
    attempted = joint_load_receipt > 0.5
    success = public_team_reward > 0.0
    likelihood_high = torch.where(success, torch.full_like(posterior, 0.9), torch.full_like(posterior, 0.2))
    likelihood_low = torch.where(success, torch.full_like(posterior, 0.1), torch.full_like(posterior, 0.9))
    updated = posterior * likelihood_high
    updated = updated / (updated + (1.0 - posterior) * likelihood_low).clamp_min(1e-8)
    return torch.where(attempted, updated.clamp(0.01, 0.99), posterior)
