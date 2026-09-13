"""Capacity-defense task with state-potential team credit for baseline learning.

The transition, observations, action interface, resource capacities and
terminal success definition are inherited unchanged.  Only the training reward
adds a bounded difference of a current-state threat-risk potential.
"""
from __future__ import annotations

import numpy as np

from envs.multi_threat_capacity_defense_env import MultiThreatCapacityDefenseConfig, MultiThreatCapacityDefenseEnv


class MultiThreatCapacityShapedDefenseEnv(MultiThreatCapacityDefenseEnv):
    """Adds non-privileged state-potential credit without altering the task."""

    potential_gamma = 0.99
    potential_scale = 0.35

    def reset(self):
        result = super().reset()
        self.previous_risk_potential = self._risk_potential()
        return result

    def _risk_potential(self) -> float:
        if self.route_assignment is None:
            return 0.0
        risk = 0.0
        for threat, asset_sign in enumerate(self.route_assignment):
            if self.blue_destroyed[threat]:
                continue
            asset_distance = float(np.linalg.norm(self.red_pos[threat] - self._asset(asset_sign)))
            proximity = float(np.exp(-asset_distance / 6000.0))
            lock_fraction = float(self.red_target_lock_hold[threat]) / float(self.lock_config.red_target_lock_steps)
            suppressed = self.base.step_count <= self.suppressed_until[threat]
            risk += (0.20 if suppressed else 1.0) * (proximity + 0.50 * lock_fraction)
        return -risk

    def step(self, actions: np.ndarray | list[int]):
        obs, share, graph, rewards, dones, info = super().step(actions)
        current = self._risk_potential()
        shaping = self.potential_scale * (self.potential_gamma * current - self.previous_risk_potential)
        self.previous_risk_potential = current
        rewards = rewards + np.full_like(rewards, shaping)
        info["risk_potential"] = float(current)
        info["potential_shaping_reward"] = float(shaping)
        return obs, share, graph, rewards, dones, info
