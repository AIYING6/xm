"""PSCR P7: role-resolved service commitments over the unchanged 3DOF plant.

Before a public future request arrives, the team can either keep every vehicle
on the current service chain or reserve scout/relay capacity in the forecast
sector while the executor continues the current service.  The selected role
allocation is physically locked for a short, public commitment window.

No future-request truth is exposed before arrival.  The class is deliberately
an interface extension rather than a modification of prior PSCR environments.
"""
from __future__ import annotations

from typing import Any

import numpy as np

from envs.pscr_contingency_service_env import CONTINGENCY_STAGE, PSCRContingencyServiceEnv
from envs.pscr_adversarial_service_env import PredictiveServiceChainReconfigurationEnv
from envs.pscr_service_reconfiguration_env import FORECAST_STAGE, FUTURE_SERVICE, PRIMARY_SERVICE, SAFE_HOLD


class PSCRRoleCommitmentEnv(PSCRContingencyServiceEnv):
    """Adds a public, role-resolved, irreversible pre-arrival commitment."""

    def reset(self):
        result = super().reset()
        self._committed_intents: np.ndarray | None = None
        return result

    def _role_goal(self, agent: int, intent: int) -> np.ndarray:
        """Map a public allocation intent to an agent-specific legal goal."""
        if intent == FORECAST_STAGE:
            # Reserving the forecast sector consumes scout/relay capacity,
            # while the executor remains available for the active request.
            return self.primary_position if agent == self.executor else self._forecast_position
        if intent == CONTINGENCY_STAGE:
            # A neutral reserve keeps the executor on current service and
            # moves the information-and-link roles to a public hub.
            return self.primary_position if agent == self.executor else self._contingency_position
        return super()._goal(agent, intent)

    def _commitment_active(self) -> bool:
        start = self.config.commitment_start_step
        return start <= self.step_count < start + self.config.commitment_lock_steps

    def actor_observation(self) -> np.ndarray:
        base = super().actor_observation()
        remaining = max(0, self.config.commitment_start_step + self.config.commitment_lock_steps - self.step_count)
        public = np.asarray(
            (
                float(self.step_count >= self.config.commitment_start_step),
                float(self._commitment_active()),
                remaining / self.config.horizon,
            ),
            dtype=np.float32,
        )
        return np.concatenate((base, np.repeat(public[None, :], self.num_agents, axis=0)), axis=1)

    def critic_observation(self) -> np.ndarray:
        base = super().critic_observation()
        remaining = max(0, self.config.commitment_start_step + self.config.commitment_lock_steps - self.step_count)
        return np.concatenate((base, np.asarray((float(self._commitment_active()), remaining / self.config.horizon), dtype=np.float32)))

    def step(self, actions: np.ndarray | list[int]):
        requested = np.asarray(actions, dtype=np.int64).reshape(self.num_agents)
        requested = np.clip(requested, 0, self.action_dim - 1)
        if self._commitment_active():
            if self._committed_intents is None:
                self._committed_intents = requested.copy()
            intents = self._committed_intents
        else:
            intents = requested
        intents = np.where((intents == FUTURE_SERVICE) & (not self.future_active), FORECAST_STAGE, intents)
        primitive = np.asarray(
            [self._autopilot_action(agent, self._role_goal(agent, int(intent))) for agent, intent in enumerate(intents)],
            dtype=np.int64,
        )
        self._last_macro_actions = intents.copy()
        # Bypass the parent macro wrapper: ``primitive`` is already a valid
        # 3DOF action vector generated from the role-resolved allocation.
        obs, critic, graph, rewards, dones, info = PredictiveServiceChainReconfigurationEnv.step(self, primitive)
        info = dict(info)
        info["role_commitment_active"] = float(self._commitment_active())
        info["role_commitment_locked"] = float(self._committed_intents is not None)
        info["role_commitment_executor_primary"] = float(self._commitment_active() and int(intents[self.executor]) in {FORECAST_STAGE, CONTINGENCY_STAGE})
        return obs, critic, graph, rewards, dones, info
