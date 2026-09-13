"""Primitive-control dual-asset UAV defense environment.

This environment starts a new task line.  Its terminal event is asset damage,
not a generic pursuit timeout: a red attacker selects one of two separated
assets after observing realised blue coverage, and wins by reaching that asset.
Blue UAVs retain the repository's 27 primitive 3DOF actions and existing legal
sensing/communication/attack-chain mechanics.

The module is G0-only.  It does not contain a learning method or claim that
the task is yet suitable for a paper.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from envs.pscr_v3_dual_exit_interception_env import PSCRV3Config, PSCRV3DualExitInterceptionEnv


@dataclass(frozen=True)
class DualAssetDefenseConfig(PSCRV3Config):
    """Physical contract for the G0 dual-asset-defense task."""

    horizon: int = 190
    branch_step: int = 28
    decision_zone_x: float = 4_000.0
    asset_x: float = -8_000.0
    asset_lateral: float = 7_500.0
    asset_strike_radius: float = 1_200.0
    # The target starts beyond the immediate attack window and accelerates to
    # its existing type limit only after choosing an attack route.
    post_branch_speed: float = 255.0


class DualAssetDefenseEnv(PSCRV3DualExitInterceptionEnv):
    """Three-UAV defense against an adaptive, single-target strike attempt."""

    def __init__(self, config: DualAssetDefenseConfig | None = None):
        self.defense_config = config or DualAssetDefenseConfig()
        super().__init__(self.defense_config)

    def _asset_position(self, sign: int) -> np.ndarray:
        return np.asarray(
            (self.defense_config.asset_x, sign * self.defense_config.asset_lateral, 5_000.0),
            dtype=np.float32,
        )

    def _egress_position(self, sign: int) -> np.ndarray:
        # Parent motion uses an egress endpoint.  In this task it is a real
        # physical asset: arrival is a strike event, not an abstract escape.
        return self._asset_position(sign)

    def reset(self):
        obs, critic, graph = super().reset()
        self.asset_breached = 0
        self.asset_integrity = {-1: 1.0, 1: 1.0}
        return obs, critic, graph

    def step(self, actions: np.ndarray | list[int]):
        if self.base.done:
            raise RuntimeError("Call reset() before stepping a finished episode.")
        actions = np.asarray(actions, dtype=np.int64).reshape(self.num_agents)
        actions = np.clip(actions, 0, self.action_dim - 1)
        prev_range = self.base._mean_target_range()
        prev_tracking = float(np.mean(self.base.detected_by))
        prev_window = float(np.max(self.base.attack_window))
        self.base.step_count += 1
        self.base._move_blue(actions)
        self._move_red_to_exit()
        self.base._update_sensing_and_comm()
        cur_range = self.base._mean_target_range()
        tracking = float(np.mean(self.base.detected_by))
        window = float(np.max(self.base.attack_window))
        if window > 0.5 and tracking > 0.0 and self.base._comm_has_chain_to_attacker():
            self.base.attack_hold += 1
        else:
            self.base.attack_hold = 0
        self.base.success = self.base.attack_hold >= self.base.config.attack_hold_steps
        self.base.collision = self.base._has_collision()
        self.base.constraint_violation = self.base._has_constraint_violation()
        if self.exit_choice is not None:
            self.asset_breached = int(
                np.linalg.norm(self.base.red_pos[0] - self._asset_position(self.exit_choice))
                <= self.defense_config.asset_strike_radius
            )
            if self.asset_breached:
                self.asset_integrity[self.exit_choice] = 0.0
        timeout = self.base.step_count >= self.defense_config.horizon
        self.base.done = bool(self.base.success or self.asset_breached or self.base.collision or self.base.constraint_violation or timeout)
        self.base.history["blue_pos"].append(self.base.blue_pos.copy())
        self.base.history["red_pos"].append(self.base.red_pos.copy())
        self.base.history["detected_by"].append(self.base.detected_by.copy())
        self.base.history["attack_window"].append(self.base.attack_window.copy())
        rewards = self.base._compute_rewards(prev_range, cur_range, prev_tracking, tracking, prev_window, window)
        if self.asset_breached:
            rewards = rewards - 1.0
        dones = np.full((self.num_agents, 1), self.base.done, dtype=np.float32)
        info: dict[str, Any] = {
            "defense_success": float(self.base.success),
            "asset_breach": float(self.asset_breached),
            "asset_integrity_negative": self.asset_integrity[-1],
            "asset_integrity_positive": self.asset_integrity[1],
            "timeout": float(timeout and not self.base.success and not self.asset_breached and not self.base.collision and not self.base.constraint_violation),
            "collision": float(self.base.collision),
            "constraint_violation": float(self.base.constraint_violation),
            "attack_route_committed": float(self.exit_choice is not None),
            "attacked_asset": float(self.exit_choice or 0),
            "primitive_action_interface": "3dof_27_discrete",
        }
        if self._coverage_at_branch is not None:
            info.update({f"branch_asset_coverage_{key}": value for key, value in self._coverage_at_branch.items()})
        return self._get_obs(), self._get_share_obs(), self._get_graph_obs(), rewards, dones, info
