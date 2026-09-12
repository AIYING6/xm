"""Public-belief role-commitment MAPPO policy for the frozen P8 interface."""
from __future__ import annotations

import torch
from torch import nn
from torch.distributions import Categorical

from algorithms.pscr_p8_plain_mappo import PSCRP8PlainMAPPO
from envs.pscr_service_reconfiguration_env import FORECAST_STAGE, PRIMARY_SERVICE


class PSCRPBRCRoleCommitmentMAPPO(PSCRP8PlainMAPPO):
    """Adds one public, team-level plan head during the existing lock window.

    Plan 0 maps to maintaining the primary chain.  Plan 1 maps to the only
    legal forecast prefix: Scout/Relay stage while Executor keeps primary
    service.  Outside that public window this remains the same individual
    role-intent actor as the fixed-capacity baseline.
    """

    context_dim = 5

    def __init__(self) -> None:
        super().__init__()
        self.plan_actor = nn.Sequential(
            nn.Linear(self.context_dim, 64), nn.Tanh(),
            nn.Linear(64, 64), nn.Tanh(),
            nn.Linear(64, 2),
        )

    def plan_distribution(self, public_context: torch.Tensor) -> Categorical:
        return Categorical(logits=self.plan_actor(public_context))

    @staticmethod
    def plan_actions(plan: torch.Tensor) -> torch.Tensor:
        """Map batch-shaped binary plans to ordered Scout/Relay/Executor intents."""
        maintain = torch.full((*plan.shape, 3), PRIMARY_SERVICE, dtype=torch.long, device=plan.device)
        stage = maintain.clone()
        stage[..., 0] = FORECAST_STAGE
        stage[..., 1] = FORECAST_STAGE
        return torch.where(plan[..., None].bool(), stage, maintain)

    @staticmethod
    def transform_context(context: torch.Tensor, arm: str) -> torch.Tensor:
        """Capacity-matched ablations vary only public-reliability semantics."""
        if arm == "pbrc":
            return context
        altered = context.clone()
        if arm == "plan_no_reliability":
            altered[..., 0] = 0.5
        elif arm == "permuted_pbrc":
            altered[..., 0] = 1.0 - altered[..., 0]
        else:
            raise ValueError(f"unsupported PBRC arm: {arm}")
        return altered
