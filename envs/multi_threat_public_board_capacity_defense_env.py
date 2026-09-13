"""Capacity-limited defense under an explicit public operational picture.

This variant makes current blue/red tracks and remaining shared resources
available to every actor as a command-and-control board.  Physical feasibility
of suppression and interception is intentionally unchanged.
"""
from __future__ import annotations

import numpy as np

from .multi_threat_capacity_defense_env import MultiThreatCapacityDefenseEnv
from .multi_threat_capacity_shaped_defense_env import MultiThreatCapacityShapedDefenseEnv


class MultiThreatPublicBoardCapacityDefenseEnv(MultiThreatCapacityShapedDefenseEnv):
    """Public-state version of the two-threat, two-capability defense task."""

    def _public_board(self) -> np.ndarray:
        horizon = max(1, self.config.horizon)
        destroyed = getattr(self, "blue_destroyed", np.zeros(2, dtype=bool))
        suppressed_until = getattr(self, "suppressed_until", np.full(2, -1, dtype=np.int64))
        kinetic = float(getattr(self, "kinetic_engagements_remaining", 0))
        suppression_remaining = np.maximum(0, suppressed_until - self.base.step_count) / horizon
        return np.concatenate(
            (
                self.base.blue_pos.flatten() / self.base.config.world_radius,
                self.red_pos.flatten() / self.base.config.world_radius,
                destroyed.astype(np.float32),
                suppression_remaining.astype(np.float32),
                np.asarray([kinetic, self.base.step_count / horizon], dtype=np.float32),
            )
        ).astype(np.float32)

    def _obs(self) -> np.ndarray:
        base = super()._obs()
        return np.concatenate((base, np.tile(self._public_board(), (self.num_agents, 1))), axis=1).astype(np.float32)

    def _share_obs(self) -> np.ndarray:
        base = super()._share_obs()
        resources = np.concatenate(
            (
                getattr(self, "blue_destroyed", np.zeros(2, dtype=bool)).astype(np.float32),
                np.maximum(0, getattr(self, "suppressed_until", np.full(2, -1, dtype=np.int64)) - self.base.step_count) / max(1, self.config.horizon),
                np.asarray([getattr(self, "kinetic_engagements_remaining", 0)], dtype=np.float32),
            )
        )
        return np.concatenate((base, np.tile(resources, (self.num_agents, 1))), axis=1).astype(np.float32)
