"""Phase-released public planning for predictive service-chain reconfiguration."""
from __future__ import annotations

import torch
from torch import nn
from torch.distributions import Categorical

from algorithms.pscr_contingency_predictive_mappo import PSCRContingencyPredictiveMAPPO


class PSCRPhaseReleaseMAPPO(PSCRContingencyPredictiveMAPPO):
    """Separate public plans before and after the publicly observed arrival.

    Before the request is revealed, ``robust`` plans over the announced sector
    and its opposite public hypothesis.  After the public arrival event, all
    arms use the same release head.  The actor can then combine this release
    plan with the newly legal local relative request coordinates.  Neither
    head receives the unrevealed future realization before arrival.
    """

    future_active_index = 22

    def __init__(self, *, planning_mode: str = "robust", shuffle_forecast_context: bool = False) -> None:
        super().__init__(planning_mode=planning_mode, shuffle_forecast_context=shuffle_forecast_context)
        self.pre_plan = self.plan
        self.post_plan = nn.Sequential(nn.Linear(len(self.public_indices), 64), nn.Tanh(), nn.Linear(64, self.action_dim))

    def _pre_distribution(self, actor_obs: torch.Tensor, action_masks: torch.Tensor) -> Categorical:
        context = self._context_with_sector(actor_obs)
        if self.planning_mode == "masked":
            context = context.clone(); context[..., 4] = 0.0
            return self._masked(self.pre_plan(context), action_masks)
        if self.planning_mode == "direct":
            return self._masked(self.pre_plan(context), action_masks)
        announced = self._masked(self.pre_plan(context), action_masks).probs
        opposite = self._masked(self.pre_plan(self._context_with_sector(actor_obs, -context[..., 4])), action_masks).probs
        return Categorical(probs=0.5 * (announced + opposite))

    def plan_distribution(self, actor_obs: torch.Tensor, action_masks: torch.Tensor) -> Categorical:
        pre = self._pre_distribution(actor_obs, action_masks).probs
        post = self._masked(self.post_plan(self._context_with_sector(actor_obs)), action_masks).probs
        active = (actor_obs[..., self.future_active_index:self.future_active_index + 1] > 0.5)
        return Categorical(probs=torch.where(active, post, pre))
