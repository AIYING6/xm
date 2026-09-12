"""Reliability-conditioned commitment--release MAPPO for PSCR P4.

The execution actor receives only legal local observations and public request
fields.  A training-only action-conditioned opportunity head estimates the
long-horizon value of currently legal pre-arrival intents.  Three modes share
the same architecture: ``full`` uses that signal; ``phase_control`` fits the
head without sending it to the actor loss; and ``permuted_reliability`` uses
the same signal after a deterministic swap of the two public reliability bands.
"""
from __future__ import annotations

import torch
from torch import nn
from torch.distributions import Categorical


class PSCRReliabilityCommitmentMAPPO(nn.Module):
    public_indices = (6, 14, 15, 19, 20, 21, 22, 23)
    future_active_index = 22

    def __init__(self, *, mode: str = "full", obs_dim: int = 27, critic_dim: int = 47, hidden_dim: int = 128, action_dim: int = 5) -> None:
        super().__init__()
        if mode not in {"full", "phase_control", "permuted_reliability"}:
            raise ValueError(f"unsupported RC-PSCR mode: {mode}")
        self.mode, self.action_dim = mode, action_dim
        self.pre_plan = nn.Sequential(nn.Linear(len(self.public_indices), 64), nn.Tanh(), nn.Linear(64, action_dim))
        self.post_plan = nn.Sequential(nn.Linear(len(self.public_indices), 64), nn.Tanh(), nn.Linear(64, action_dim))
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
        # Shared across agents because it estimates the joint opportunity of
        # allocating the service chain to one macro intent at this time.
        self.commitment_q = nn.Sequential(
            nn.Linear(critic_dim, hidden_dim), nn.Tanh(),
            nn.Linear(hidden_dim, action_dim),
        )

    def public_context(self, actor_obs: torch.Tensor) -> torch.Tensor:
        context = actor_obs[..., list(self.public_indices)]
        if self.mode == "permuted_reliability":
            context = context.clone()
            # P4 freezes two public values {0.25, 0.90}; this is their exact
            # involution, retaining the marginal range and dimensionality.
            context[..., 3] = 1.15 - context[..., 3]
        return context

    @staticmethod
    def _masked(logits: torch.Tensor, masks: torch.Tensor) -> Categorical:
        return Categorical(logits=logits.masked_fill(masks <= 0, -1.0e9))

    def plan_distribution(self, actor_obs: torch.Tensor, action_masks: torch.Tensor) -> Categorical:
        context = self.public_context(actor_obs)
        pre = self._masked(self.pre_plan(context), action_masks).probs
        post = self._masked(self.post_plan(context), action_masks).probs
        active = actor_obs[..., self.future_active_index:self.future_active_index + 1] > 0.5
        return Categorical(probs=torch.where(active, post, pre))

    def action_distribution(self, actor_obs: torch.Tensor, action_masks: torch.Tensor) -> Categorical:
        plan_probs = self.plan_distribution(actor_obs, action_masks).probs
        private_obs = actor_obs.clone()
        private_obs[..., list(self.public_indices)] = 0.0
        logits = self.actor(torch.cat((private_obs, plan_probs), dim=-1)).masked_fill(action_masks <= 0, -1.0e9)
        return Categorical(logits=logits)

    def value(self, critic_obs: torch.Tensor) -> torch.Tensor:
        return self.critic(critic_obs).squeeze(-1)

    def commitment_values(self, critic_obs: torch.Tensor) -> torch.Tensor:
        return self.commitment_q(critic_obs)

    def commitment_target_distribution(self, critic_obs: torch.Tensor, action_masks: torch.Tensor) -> torch.Tensor:
        """Masked opportunity distribution, broadcast from joint critic to actors."""
        q = self.commitment_values(critic_obs).unsqueeze(-2)
        q = q.masked_fill(action_masks <= 0, -1.0e9)
        return torch.softmax(q / 0.50, dim=-1)
