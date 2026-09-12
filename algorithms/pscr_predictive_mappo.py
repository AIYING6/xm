"""Forecast-conditioned public-plan MAPPO for service-chain reconfiguration."""
from __future__ import annotations

import torch
from torch import nn
from torch.distributions import Categorical


class PSCRPredictiveMAPPO(nn.Module):
    """MAPPO with a public plan bottleneck and training-only opportunity head.

    The plan module receives only fields that are exactly common to all three
    agents: clock, request lifecycle, announced-sector reliability/identity,
    and the public arrival/urgency fields.  Relative request coordinates are
    deliberately excluded, so the module cannot reconstruct an unrevealed
    future request location.
    """

    public_indices = (6, 14, 15, 19, 20, 21, 22, 23)

    def __init__(self, obs_dim: int = 27, critic_dim: int = 47, hidden_dim: int = 128, action_dim: int = 4, *, shuffle_forecast_context: bool = False) -> None:
        super().__init__()
        self.action_dim = action_dim
        self.shuffle_forecast_context = shuffle_forecast_context
        self.plan = nn.Sequential(nn.Linear(len(self.public_indices), 64), nn.Tanh(), nn.Linear(64, action_dim))
        self.actor = nn.Sequential(
            nn.Linear(obs_dim + action_dim, hidden_dim), nn.Tanh(),
            nn.Linear(hidden_dim, hidden_dim), nn.Tanh(),
            nn.Linear(hidden_dim, action_dim),
        )
        self.critic = nn.Sequential(
            nn.Linear(critic_dim, hidden_dim), nn.Tanh(),
            nn.Linear(hidden_dim, hidden_dim), nn.Tanh(),
            nn.Linear(hidden_dim, 1),
        )
        # This head is used only in the loss.  It maps joint public state to
        # action-conditioned service opportunity estimates, never to actor
        # inputs at execution.
        self.opportunity = nn.Sequential(
            nn.Linear(critic_dim, hidden_dim), nn.Tanh(),
            nn.Linear(hidden_dim, action_dim),
        )

    def public_context(self, actor_obs: torch.Tensor) -> torch.Tensor:
        context = actor_obs[..., list(self.public_indices)]
        if self.shuffle_forecast_context:
            # Deterministically break forecast--outcome alignment only for
            # the public planning channel; this is an ablation, not a new
            # environmental signal.
            context = context.clone()
            context[..., 4] = -context[..., 4]
        return context

    def plan_distribution(self, actor_obs: torch.Tensor, action_masks: torch.Tensor) -> Categorical:
        logits = self.plan(self.public_context(actor_obs)).masked_fill(action_masks <= 0, -1.0e9)
        return Categorical(logits=logits)

    def action_distribution(self, actor_obs: torch.Tensor, action_masks: torch.Tensor) -> Categorical:
        plan_probs = self.plan_distribution(actor_obs, action_masks).probs
        # Keep public forecast/lifecycle fields inside the shared plan channel
        # so a forecast-label ablation cannot be bypassed by the local actor.
        private_obs = actor_obs.clone()
        private_obs[..., list(self.public_indices)] = 0.0
        logits = self.actor(torch.cat((private_obs, plan_probs), dim=-1)).masked_fill(action_masks <= 0, -1.0e9)
        return Categorical(logits=logits)

    def value(self, critic_obs: torch.Tensor) -> torch.Tensor:
        return self.critic(critic_obs).squeeze(-1)

    def opportunity_values(self, critic_obs: torch.Tensor) -> torch.Tensor:
        return self.opportunity(critic_obs)
