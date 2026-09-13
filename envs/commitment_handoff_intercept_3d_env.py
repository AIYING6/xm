"""Commitment-level interface for the staged 3DOF relay-handoff task.

The plant, sensing, message transport, collision checks and staged endpoint
are inherited unchanged from :mod:`timed_handoff_intercept_3d_env`.  This
adapter deliberately fixes the low-level flight stabilisation problem and
exposes the decision that the research task is meant to study: should the
relay retain the current service route or reconstruct to the announced future
route?  Both macro actions are executed by the same deterministic controller
over the original 27 primitive 3DOF actions.

This is a command-level UAV abstraction, not an additional information
channel.  The controller uses only the same emitted local target observation
and public service waypoints available to the actor.
"""
from __future__ import annotations

import math
from typing import Dict, Tuple

import numpy as np

from envs.timed_handoff_intercept_3d_env import TimedHandoffIntercept3DConfig, TimedHandoffIntercept3DEnv
from envs.uav_intercept_3d_env import ACTION3D_TABLE, angle_diff


RETAIN_CURRENT = 0
RECONSTRUCT_FUTURE = 1
COMMITMENT_ACTIONS = (RETAIN_CURRENT, RECONSTRUCT_FUTURE)


class CommitmentHandoffIntercept3DEnv(TimedHandoffIntercept3DEnv):
    """Stage task with a two-way, role-relevant relay service commitment."""

    action_dim = len(COMMITMENT_ACTIONS)

    def __init__(self, config: TimedHandoffIntercept3DConfig | None = None):
        super().__init__(config)
        # Base construction advertises the primitive flight table.  The
        # actor-facing interface of this adapter is intentionally binary.
        self.action_dim = len(COMMITMENT_ACTIONS)

    @staticmethod
    def _nearest_primitive(command: np.ndarray) -> int:
        return int(np.argmin(np.sum((ACTION3D_TABLE - command[None, :]) ** 2, axis=1)))

    def _tracking_primitives(self, raw_obs: np.ndarray) -> np.ndarray:
        """Role-neutral legal target tracking for non-relay flight control."""
        primitive = np.zeros(self.num_agents, dtype=np.int64)
        max_turn = (0.035, 0.030, 0.052)
        max_climb = (0.26, 0.22, 0.31)
        for agent in range(self.num_agents):
            rel_x, rel_y, rel_z = map(float, raw_obs[agent, 8:11])
            if abs(rel_x) + abs(rel_y) + abs(rel_z) < 1e-8:
                continue
            heading = math.atan2(float(raw_obs[agent, 4]), float(raw_obs[agent, 5]))
            target_heading = math.atan2(rel_y, rel_x)
            turn = np.clip(angle_diff(target_heading, heading) / max_turn[agent], -1.0, 1.0)
            gamma = math.atan2(float(raw_obs[agent, 6]), float(raw_obs[agent, 7]))
            target_gamma = math.atan2(rel_z, math.hypot(rel_x, rel_y) + 1e-6)
            climb = np.clip((target_gamma - gamma) / max_climb[agent], -1.0, 1.0)
            primitive[agent] = self._nearest_primitive(np.asarray((turn, climb, 1.0), dtype=np.float32))
        return primitive

    def _relay_service_primitive(self, future: bool) -> int:
        """Map a public current/future route commitment to a primitive action."""
        relay = 1
        waypoint = self._service_waypoint(future=future)
        desired = waypoint - self.blue_pos[relay]
        if np.linalg.norm(desired) < 1e-8:
            # The verified G0 controller falls back to its local target
            # tracker when it is already at the retained route point.
            return int(self._tracking_primitives(self._get_obs())[relay])
        heading = float(self.blue_heading[relay])
        target_heading = math.atan2(float(desired[1]), float(desired[0]))
        turn = np.clip(angle_diff(target_heading, heading) / 0.030, -1.0, 1.0)
        gamma = float(self.blue_gamma[relay])
        target_gamma = math.atan2(float(desired[2]), math.hypot(float(desired[0]), float(desired[1])) + 1e-6)
        climb = np.clip((target_gamma - gamma) / 0.22, -1.0, 1.0)
        return self._nearest_primitive(np.asarray((turn, climb, 0.0), dtype=np.float32))

    def _macro_to_primitive(self, macro_actions: np.ndarray | list[int]) -> np.ndarray:
        macro = np.asarray(macro_actions, dtype=np.int64).reshape(-1)
        if macro.size != self.num_agents:
            raise ValueError(f"expected {self.num_agents} commitment actions, got {macro.shape}")
        if np.any((macro < RETAIN_CURRENT) | (macro > RECONSTRUCT_FUTURE)):
            raise ValueError("commitment actions must be 0=retain_current or 1=reconstruct_future")
        raw_obs = self._get_obs()
        primitive = self._tracking_primitives(raw_obs)
        primitive[1] = self._relay_service_primitive(future=bool(macro[1] == RECONSTRUCT_FUTURE))
        return primitive

    def step(self, actions: np.ndarray | list[int]):
        macro = np.asarray(actions, dtype=np.int64).reshape(-1)
        primitive = self._macro_to_primitive(macro)
        # ``UAVIntercept3DEnv.step`` clips its input using ``self.action_dim``.
        # Expose two actions to the actor but temporarily restore the
        # primitive-table cardinality while delegating the physical step.
        actor_action_dim = self.action_dim
        self.action_dim = len(ACTION3D_TABLE)
        try:
            obs, share, graph, rewards, dones, info = super().step(primitive)
        finally:
            self.action_dim = actor_action_dim
        info = dict(info)
        info.update(
            {
                "commitment_relay_action": float(macro[1]),
                "commitment_relay_retains_current": float(macro[1] == RETAIN_CURRENT),
                "commitment_relay_reconstructs_future": float(macro[1] == RECONSTRUCT_FUTURE),
                "commitment_relay_primitive_action": float(primitive[1]),
            }
        )
        return obs, share, graph, rewards, dones, info
