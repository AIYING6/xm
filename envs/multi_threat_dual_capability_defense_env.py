"""G0-only multi-threat defense with physically constrained dual capabilities.

The attacker UAV retains kinetic neutralisation.  The scout can maintain one
focused, range- and communication-limited non-kinetic disruption beam.  The
beam is automatic once its physical preconditions hold; it is not a learnt
button, macro action, reward switch, or privileged label.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from envs.multi_threat_asset_defense_env import MultiThreatAssetDefenseConfig, MultiThreatAssetDefenseEnv


@dataclass(frozen=True)
class MultiThreatDualCapabilityDefenseConfig(MultiThreatAssetDefenseConfig):
    suppression_range: float = 8_000.0
    suppression_hold_steps: int = 4
    suppression_duration_steps: int = 16
    suppressed_speed_scale: float = 0.58


class MultiThreatDualCapabilityDefenseEnv(MultiThreatAssetDefenseEnv):
    """Two-threat asset defense with one kinetic and one focused disruption role."""

    scout, relay, attacker = 0, 1, 2

    def __init__(self, config: MultiThreatDualCapabilityDefenseConfig | None = None):
        self.dual_config = config or MultiThreatDualCapabilityDefenseConfig()
        super().__init__(self.dual_config)

    def reset(self):
        result = super().reset()
        self.suppression_hold = np.zeros(2, dtype=np.int64)
        self.suppressed_until = np.full(2, -1, dtype=np.int64)
        self.focused_threat = -1
        return result

    def _can_focus(self, threat: int) -> bool:
        if self.blue_destroyed[threat] or not self._visible(self.scout, threat):
            return False
        distance = float(np.linalg.norm(self.red_pos[threat] - self.base.blue_pos[self.scout]))
        # The relay must provide a current legal path from scout to attacker;
        # disruption status cannot become a hidden global coordination signal.
        reach = self.base._transitive_comm()
        return distance <= self.dual_config.suppression_range and bool(reach[self.attacker, self.scout] > 0.5)

    def _update_suppression(self) -> None:
        feasible = [t for t in range(2) if self._can_focus(t)]
        if not feasible:
            self.focused_threat = -1
            self.suppression_hold[:] = 0
            return
        # One steerable beam: select the nearest feasible threat.  This is a
        # physical capacity limit, deliberately independent of rewards.
        self.focused_threat = min(feasible, key=lambda t: float(np.linalg.norm(self.red_pos[t] - self.base.blue_pos[self.scout])))
        for threat in range(2):
            self.suppression_hold[threat] = self.suppression_hold[threat] + 1 if threat == self.focused_threat else 0
        t = self.focused_threat
        if self.suppression_hold[t] >= self.dual_config.suppression_hold_steps:
            self.suppressed_until[t] = max(self.suppressed_until[t], self.base.step_count + self.dual_config.suppression_duration_steps)

    def _move_red(self, threat: int) -> None:
        original_speed = float(self.red_speed[threat])
        if self.base.step_count <= self.suppressed_until[threat]:
            self.red_speed[threat] = original_speed * self.dual_config.suppressed_speed_scale
        super()._move_red(threat)
        self.red_speed[threat] = original_speed

    def _threat_breach(self, threat: int, asset_sign: int) -> bool:
        """Default v1 endpoint: arrival at the asset causes immediate loss."""
        return bool(np.linalg.norm(self.red_pos[threat] - self._asset(asset_sign)) <= self.config.asset_strike_radius)

    def step(self, actions: np.ndarray | list[int]):
        if self.base.done:
            raise RuntimeError("Call reset() before stepping a finished episode.")
        actions = np.asarray(actions, dtype=np.int64).reshape(self.num_agents)
        self.base.step_count += 1
        self.base._move_blue(np.clip(actions, 0, self.action_dim - 1))
        # Communication is updated before disruption eligibility is checked.
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
        defense_success = bool(self.blue_destroyed.all())
        collision, constraint = self.base._has_collision(), self.base._has_constraint_violation()
        timeout = self.base.step_count >= self.config.horizon
        self.base.done = bool(defense_success or breach or collision or constraint or timeout)
        rewards = np.full((self.num_agents, 1), 1.5 if defense_success else (-1.0 if breach else -0.005), dtype=np.float32)
        dones = np.full((self.num_agents, 1), self.base.done, dtype=np.float32)
        return self._obs(), self._share_obs(), self._graph(), rewards, dones, {
            "defense_success": float(defense_success), "asset_breach": float(breach),
            "neutralized_threats": float(self.blue_destroyed.sum()), "route_committed": float(self.route_assignment is not None),
            "focused_threat": float(self.focused_threat), "suppressed_threats": float(np.sum(self.base.step_count <= self.suppressed_until)),
            "timeout": float(timeout and not defense_success and not breach and not collision and not constraint),
            "collision": float(collision), "constraint_violation": float(constraint),
            "primitive_action_interface": "3dof_27_discrete",
        }
