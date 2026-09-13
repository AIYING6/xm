"""Capacity-limited multi-threat UAV defense with a real assignment conflict.

One attacker has a single kinetic engagement for the episode.  The scout can
keep at most one remaining threat from completing its target-lock chain.  A
safe episode therefore requires complementary allocation: intercept one
threat and continuously suppress the other through the deadline.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from envs.multi_threat_target_lock_defense_env import (
    MultiThreatTargetLockDefenseConfig,
    MultiThreatTargetLockDefenseEnv,
)


@dataclass(frozen=True)
class MultiThreatCapacityDefenseConfig(MultiThreatTargetLockDefenseConfig):
    kinetic_engagement_capacity: int = 1


class MultiThreatCapacityDefenseEnv(MultiThreatTargetLockDefenseEnv):
    """Two-threat defense where kinetic and non-kinetic resources are complementary."""

    def __init__(self, config: MultiThreatCapacityDefenseConfig | None = None):
        self.capacity_config = config or MultiThreatCapacityDefenseConfig()
        super().__init__(self.capacity_config)

    def reset(self):
        result = super().reset()
        self.kinetic_engagements_remaining = int(self.capacity_config.kinetic_engagement_capacity)
        return result

    def _update_kinetic_hold(self, threat: int) -> bool:
        if self.blue_destroyed[threat] or self.kinetic_engagements_remaining <= 0:
            self.kinetic_hold[threat] = 0
            return bool(self.blue_destroyed[threat])
        destroyed_before = bool(self.blue_destroyed[threat])
        result = super()._update_kinetic_hold(threat)
        if result and not destroyed_before:
            self.kinetic_engagements_remaining -= 1
        return result

    def step(self, actions: np.ndarray | list[int]):
        if self.base.done:
            raise RuntimeError("Call reset() before stepping a finished episode.")
        actions = np.asarray(actions, dtype=np.int64).reshape(self.num_agents)
        self.base.step_count += 1
        self.base._move_blue(np.clip(actions, 0, self.action_dim - 1))
        self._sync_base_target(0)
        self.base._update_sensing_and_comm()
        self._update_suppression()
        if self.route_assignment is None and self.base.step_count >= self.episode_branch_step:
            self._assign_routes()
        for threat in range(2):
            if not self.blue_destroyed[threat]:
                self._move_red(threat)
                self._update_kinetic_hold(threat)
        self._sync_base_target(0)
        self.base._update_sensing_and_comm()
        breach = False
        if self.route_assignment is not None:
            for threat, asset_sign in enumerate(self.route_assignment):
                if not self.blue_destroyed[threat] and self._threat_breach(threat, asset_sign):
                    self.asset_integrity[asset_sign] = 0.0
                    breach = True
        collision, constraint = self.base._has_collision(), self.base._has_constraint_violation()
        reached_deadline = self.base.step_count >= self.config.horizon
        safely_contained = bool(np.all(self.blue_destroyed | (self.base.step_count <= self.suppressed_until)))
        defense_success = bool(reached_deadline and not breach and safely_contained)
        self.base.done = bool(defense_success or breach or collision or constraint or reached_deadline)
        rewards = np.full((self.num_agents, 1), 1.5 if defense_success else (-1.0 if breach else -0.005), dtype=np.float32)
        dones = np.full((self.num_agents, 1), self.base.done, dtype=np.float32)
        return self._obs(), self._share_obs(), self._graph(), rewards, dones, {
            "defense_success": float(defense_success), "asset_breach": float(breach),
            "neutralized_threats": float(self.blue_destroyed.sum()), "route_committed": float(self.route_assignment is not None),
            "focused_threat": float(self.focused_threat), "suppressed_threats": float(np.sum(self.base.step_count <= self.suppressed_until)),
            "kinetic_engagements_remaining": float(self.kinetic_engagements_remaining),
            "timeout": float(reached_deadline and not defense_success and not breach and not collision and not constraint),
            "collision": float(collision), "constraint_violation": float(constraint),
            "primitive_action_interface": "3dof_27_discrete",
        }
