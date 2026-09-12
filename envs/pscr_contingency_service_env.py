"""Uncertainty-aware PSCR interface with a public contingency staging intent."""
from __future__ import annotations

import numpy as np

from envs.pscr_service_reconfiguration_env import (
    FORECAST_STAGE,
    FUTURE_SERVICE,
    PSCRServiceReconfigurationEnv,
    SERVICE_INTENT_NAMES,
)


CONTINGENCY_STAGE = 4
CONTINGENCY_SERVICE_INTENT_NAMES = SERVICE_INTENT_NAMES + ("contingency_stage",)


class PSCRContingencyServiceEnv(PSCRServiceReconfigurationEnv):
    """Adds a neutral, publicly defined staging hub without hidden truth."""

    action_dim = 5

    def reset(self):
        result = super().reset()
        centroid = self.base.blue_pos.mean(axis=0)
        # This hub lies between the known primary site and both possible
        # future sectors.  It is derived from the frozen geometry only, not
        # from the sampled future location, sector realization, or urgency.
        canonical_hub = np.asarray((10_000.0, 0.0, 5_000.0), dtype=np.float32)
        self._contingency_position = centroid + self.config.geometry_scale * (canonical_hub - centroid)
        return result

    def _goal(self, agent: int, intent: int) -> np.ndarray:
        if intent == CONTINGENCY_STAGE:
            return self._formation_goal(self._contingency_position, agent)
        return super()._goal(agent, intent)

    def step(self, actions):
        obs, critic, graph, rewards, dones, info = super().step(actions)
        info = dict(info)
        info["intent_contingency_stage_count"] = float(np.sum(np.asarray(actions, dtype=np.int64).reshape(self.num_agents) == CONTINGENCY_STAGE))
        info["macro_interface"] = "public_contingency_service_intent_v2"
        return obs, critic, graph, rewards, dones, info
