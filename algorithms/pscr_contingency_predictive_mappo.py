"""Public, uncertainty-aware planning for the PSCR contingency interface.

The robust mode never accesses the unrevealed future request.  It combines
plans under the announced sector and its public counterfactual opposite,
which makes the neutral contingency intent useful only when it is supported
by return feedback under forecast uncertainty.
"""
from __future__ import annotations

import torch
from torch.distributions import Categorical

from algorithms.pscr_predictive_mappo import PSCRPredictiveMAPPO


class PSCRContingencyPredictiveMAPPO(PSCRPredictiveMAPPO):
    """Five-intent PSCR planner with selectable public forecast treatment.

    ``direct`` uses the announced sector as-is. ``robust`` averages plans for
    the announced sector and its opposite. ``masked`` removes sector identity
    while retaining all other public lifecycle fields.  These are execution
    legal transformations of public observations, not privileged labels.
    """

    def __init__(self, *, planning_mode: str = "robust", shuffle_forecast_context: bool = False) -> None:
        if planning_mode not in {"direct", "robust", "masked"}:
            raise ValueError(f"unknown planning mode: {planning_mode}")
        if shuffle_forecast_context:
            raise ValueError("use planning_mode='masked' for the contingency control")
        super().__init__(action_dim=5)
        self.planning_mode = planning_mode

    def _context_with_sector(self, actor_obs: torch.Tensor, sector: torch.Tensor | None = None) -> torch.Tensor:
        context = super().public_context(actor_obs)
        if sector is not None:
            context = context.clone()
            # Within public_indices, index 4 is the announced forecast sector.
            context[..., 4] = sector
        return context

    @staticmethod
    def _masked(logits: torch.Tensor, masks: torch.Tensor) -> Categorical:
        return Categorical(logits=logits.masked_fill(masks <= 0, -1.0e9))

    def plan_distribution(self, actor_obs: torch.Tensor, action_masks: torch.Tensor) -> Categorical:
        context = self._context_with_sector(actor_obs)
        if self.planning_mode == "masked":
            context = context.clone()
            context[..., 4] = 0.0
            return self._masked(self.plan(context), action_masks)
        if self.planning_mode == "direct":
            return self._masked(self.plan(context), action_masks)

        # The opposite sector is a counterfactual public hypothesis, not the
        # sampled future sector. Averaging distributions avoids selecting a
        # plan that succeeds only if the announced direction happens to hold.
        announced = self._masked(self.plan(context), action_masks).probs
        opposite = self._masked(self.plan(self._context_with_sector(actor_obs, -context[..., 4])), action_masks).probs
        return Categorical(probs=0.5 * (announced + opposite))
