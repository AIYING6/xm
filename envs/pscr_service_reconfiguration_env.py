"""PSCR with a public, role-conditioned service-intent control interface.

The learning agent chooses a service allocation intent.  A deterministic
controller, shared by every future method and baseline, maps that public goal
to the existing 3DOF turn/climb/acceleration commands.  It never receives an
unrevealed future-request location or urgency.
"""
from __future__ import annotations

import math
from typing import Any

import numpy as np

from envs.pscr_adversarial_service_env import PSCRConfig, PredictiveServiceChainReconfigurationEnv


PRIMARY_SERVICE, FORECAST_STAGE, FUTURE_SERVICE, SAFE_HOLD = range(4)
SERVICE_INTENT_NAMES = ("primary_service", "forecast_stage", "future_service", "safe_hold")


class PSCRServiceReconfigurationEnv(PredictiveServiceChainReconfigurationEnv):
    """A state-closed high-level decision interface over unchanged 3DOF flight."""

    action_dim = 4
    def reset(self) -> tuple[np.ndarray, np.ndarray, dict[str, np.ndarray]]:
        result = super().reset()
        self._safe_positions = self.base.blue_pos.copy()
        centroid = self.base.blue_pos.mean(axis=0)
        # This is the public forecast-sector centre, not the sampled future
        # request coordinate.  It can therefore be used before arrival.
        forecast_canonical = np.asarray((11_000.0, float(self.forecast_sector) * 11_000.0, 5_000.0), dtype=np.float32)
        self._forecast_position = centroid + self.config.geometry_scale * (forecast_canonical - centroid)
        self._last_macro_actions = np.full(self.num_agents, SAFE_HOLD, dtype=np.int64)
        return result

    def _formation_goal(self, position: np.ndarray, agent: int) -> np.ndarray:
        # The original transparent feasibility controller established that a
        # common request point satisfies the physical sensing and relay-chain
        # predicate.  Retaining that formation avoids adding an unvalidated
        # geometric offset as an extra source of task failure.
        return np.asarray(position, dtype=np.float32)

    def _goal(self, agent: int, intent: int) -> np.ndarray:
        if intent == PRIMARY_SERVICE:
            return self._formation_goal(self.primary_position, agent)
        if intent == FORECAST_STAGE:
            return self._formation_goal(self._forecast_position, agent)
        if intent == FUTURE_SERVICE and self.future_active:
            return self._formation_goal(self.future_position, agent)
        return self._safe_positions[agent]

    def _autopilot_action(self, agent: int, goal: np.ndarray) -> int:
        """Map a public waypoint and own state to one existing 3DOF action."""
        position = self.base.blue_pos[agent]
        delta = np.asarray(goal - position, dtype=np.float32)
        horizontal = float(np.linalg.norm(delta[:2]))
        distance = float(np.linalg.norm(delta))
        heading = float(self.base.blue_heading[agent])
        desired_heading = heading if horizontal < 1.0 else math.atan2(float(delta[1]), float(delta[0]))
        heading_error = math.atan2(math.sin(desired_heading - heading), math.cos(desired_heading - heading))
        turn = int(np.sign(heading_error)) if abs(heading_error) > 0.035 else 0
        altitude_error = float(delta[2])
        climb = int(np.sign(altitude_error)) if abs(altitude_error) > 250.0 else 0
        # Match the transparent reachability controller's monotone closure
        # policy.  The high-level interface must first preserve established
        # physical feasibility before it can be used for learning.
        accel = 1
        return int((turn + 1) * 9 + (climb + 1) * 3 + (accel + 1))

    def graph_observation(self) -> dict[str, np.ndarray]:
        masks = np.ones((self.num_agents, self.action_dim), dtype=np.int8)
        if not self.future_active:
            masks[:, FUTURE_SERVICE] = 0
        return {
            "node_features": self.actor_observation(),
            "active_adj": self.base.comm_adj.astype(np.int8),
            "roles": np.asarray((self.scout, self.relay, self.executor), dtype=np.int64),
            "action_masks": masks,
        }

    def step(self, actions: np.ndarray | list[int]):
        intents = np.asarray(actions, dtype=np.int64).reshape(self.num_agents)
        intents = np.clip(intents, 0, self.action_dim - 1)
        intents = np.where((intents == FUTURE_SERVICE) & (not self.future_active), FORECAST_STAGE, intents)
        primitive = np.asarray([self._autopilot_action(agent, self._goal(agent, int(intent))) for agent, intent in enumerate(intents)], dtype=np.int64)
        self._last_macro_actions = intents.copy()
        obs, critic, graph, rewards, dones, info = super().step(primitive)
        info = dict(info)
        for index, name in enumerate(SERVICE_INTENT_NAMES):
            info[f"intent_{name}_count"] = float(np.sum(intents == index))
        info["macro_interface"] = "public_role_conditioned_service_intent_v1"
        return obs, critic, graph, rewards, dones, info
