"""P9: physically exclusive full-team forecast commitment over the P8 plant.

Unlike P8's role-preserving staging contract, a forecast commitment in this
environment assigns *all* three roles to the public forecast sector.  It is
therefore a genuine resource decision: retaining the primary chain and
pre-positioning a complete future chain cannot happen simultaneously.  Exact
future geometry and urgency remain hidden until the ordinary public-arrival
event.
"""
from __future__ import annotations

import numpy as np

from envs.pscr_search_prefix_env import P8SearchPrefixConfig, PSCRSearchPrefixEnv
from envs.pscr_service_reconfiguration_env import FORECAST_STAGE


class PSCRFullTeamCommitmentEnv(PSCRSearchPrefixEnv):
    """A separate task contract with physically exclusive team commitment."""

    def _role_goal(self, agent: int, intent: int) -> np.ndarray:
        if intent == FORECAST_STAGE:
            return self._forecast_position
        return super()._role_goal(agent, intent)

    def graph_observation(self) -> dict[str, np.ndarray]:
        graph = super().graph_observation()
        graph["task_contract"] = np.asarray((1,), dtype=np.int8)  # P9 full-team commitment
        return graph


__all__ = ("P8SearchPrefixConfig", "PSCRFullTeamCommitmentEnv")
