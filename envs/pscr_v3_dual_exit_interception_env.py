"""PSCR-v3: delayed-choice dual-exit cooperative interception.

This is a *new* task construction.  It deliberately does not alter the
legacy PSCR service-chain environments or their evidence.  Three heterogeneous
blue UAVs retain the repository's primitive 27-action 3DOF flight interface.
The red evader approaches a public decision zone and, after blue vehicles have
already moved, selects the less-covered of two physical egress corridors.

The task is intended only for zero-training feasibility and identifiability
audits until its registered gates pass.  It makes no algorithmic claim.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np

from envs.uav_intercept_3d_env import (
    ACTION3D_TABLE,
    UAVIntercept3DConfig,
    UAVIntercept3DEnv,
    angle_diff,
    velocity_from_state,
    wrap_angle,
)


@dataclass(frozen=True)
class PSCRV3Config:
    """Frozen physical parameters for the PSCR-v3 G0 task audit."""

    horizon: int = 180
    branch_step: int = 42
    egress_x: float = -11_500.0
    egress_lateral: float = 8_000.0
    egress_radius: float = 1_300.0
    decision_zone_x: float = 1_200.0
    post_branch_speed: float = 255.0
    seed: int = 0


class PSCRV3DualExitInterceptionEnv:
    """Primitive-control pursuit task with an endogenous, delayed exit choice.

    The exit label is not included in observations before the branch event.
    After the event, the red vehicle's *physical motion* is the only source of
    exit information.  The central critic receives no privileged future label.
    """

    num_agents = 3
    action_dim = len(ACTION3D_TABLE)

    def __init__(self, config: PSCRV3Config | None = None):
        self.config = config or PSCRV3Config()
        if not 5 < self.config.branch_step < self.config.horizon - 30:
            raise ValueError("branch_step must leave time both before and after the decision")
        self.rng = np.random.default_rng(self.config.seed)
        self.base = UAVIntercept3DEnv(
            UAVIntercept3DConfig(
                max_steps=self.config.horizon,
                strict_target_sensing=True,
                agent_target_info_bottleneck=True,
                relay_dependent_task=True,
                target_policy="straight",
                seed=self.config.seed,
            )
        )
        self.reset()

    def seed(self, seed: int) -> None:
        self.rng = np.random.default_rng(seed)

    def _egress_position(self, sign: int) -> np.ndarray:
        return np.asarray((self.config.egress_x, sign * self.config.egress_lateral, 5_000.0), dtype=np.float32)

    def reset(self) -> tuple[np.ndarray, np.ndarray, dict[str, np.ndarray]]:
        self.base.seed(int(self.rng.integers(0, 2**31 - 1)))
        self.base.reset()
        # A common public approach trajectory.  No future exit is sampled at
        # reset: it is selected only from realised blue coverage at branch time.
        self.base.red_pos[0] = np.asarray((11_000.0, 0.0, 5_000.0), dtype=np.float32)
        self.base.red_heading[0] = math.pi
        self.base.red_gamma[0] = 0.0
        self.base.red_speed[0] = 205.0
        self.base.step_count = 0
        self.base.done = False
        self.base.success = False
        self.base.collision = False
        self.base.constraint_violation = False
        self.base.attack_hold = 0
        self.base._update_sensing_and_comm()
        self.base.history = {
            "blue_pos": [self.base.blue_pos.copy()],
            "red_pos": [self.base.red_pos.copy()],
            "detected_by": [self.base.detected_by.copy()],
            "attack_window": [self.base.attack_window.copy()],
        }
        self.exit_choice: int | None = None
        self.evader_escaped = False
        self._coverage_at_branch: dict[str, float] | None = None
        return self._get_obs(), self._get_share_obs(), self._get_graph_obs()

    def _coverage_score(self, gate: np.ndarray) -> float:
        """Physical coverage proxy used only by the red's bounded response rule."""
        distances = np.linalg.norm(self.base.blue_pos - gate[None, :], axis=1)
        # Nearer blue agents provide more potential interception coverage.  This
        # is a deterministic function of public geometry, not an oracle score.
        return float(np.sum(np.exp(-distances / 7_000.0)))

    def _choose_exit(self) -> None:
        coverage_neg = self._coverage_score(self._egress_position(-1))
        coverage_pos = self._coverage_score(self._egress_position(+1))
        # The evader takes the weakly covered corridor.  A fixed, seeded tie
        # break prevents an invisible preference from being encoded in the task.
        if math.isclose(coverage_neg, coverage_pos, rel_tol=0.0, abs_tol=1e-8):
            choice = -1 if self.rng.random() < 0.5 else 1
        else:
            choice = -1 if coverage_neg < coverage_pos else 1
        self.exit_choice = choice
        self._coverage_at_branch = {"negative": coverage_neg, "positive": coverage_pos}

    def _move_red_to_exit(self) -> None:
        if self.exit_choice is None and self.base.step_count >= self.config.branch_step:
            self._choose_exit()
            # The target's post-decision speed is its already configured
            # physical maximum, not a new capability.  This removes the
            # artificial slack that let a single late pursuit solve every
            # instance in the first G1 audit.
            self.base.red_speed[0] = self.config.post_branch_speed
        target = (
            np.asarray((self.config.decision_zone_x, 0.0, 5_000.0), dtype=np.float32)
            if self.exit_choice is None
            else self._egress_position(self.exit_choice)
        )
        delta = target - self.base.red_pos[0]
        horizontal = float(np.linalg.norm(delta[:2]))
        desired_heading = float(self.base.red_heading[0]) if horizontal < 1.0 else math.atan2(float(delta[1]), float(delta[0]))
        target_type = self.base.config.target_type
        turn = float(np.clip(angle_diff(desired_heading, float(self.base.red_heading[0])), -target_type.max_turn_rate, target_type.max_turn_rate))
        climb = float(np.clip(delta[2] / 1_500.0, -1.0, 1.0))
        self.base.red_heading[0] = wrap_angle(float(self.base.red_heading[0]) + turn * self.base.config.dt)
        self.base.red_gamma[0] = float(np.clip(self.base.red_gamma[0] + climb * 0.25 * target_type.max_gamma * self.base.config.dt, -target_type.max_gamma, target_type.max_gamma))
        self.base.red_pos[0] += velocity_from_state(float(self.base.red_speed[0]), float(self.base.red_heading[0]), float(self.base.red_gamma[0])) * self.base.config.dt

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
            self.evader_escaped = bool(np.linalg.norm(self.base.red_pos[0] - self._egress_position(self.exit_choice)) <= self.config.egress_radius)
        timeout = self.base.step_count >= self.config.horizon
        self.base.done = bool(self.base.success or self.evader_escaped or self.base.collision or self.base.constraint_violation or timeout)
        self.base.history["blue_pos"].append(self.base.blue_pos.copy())
        self.base.history["red_pos"].append(self.base.red_pos.copy())
        self.base.history["detected_by"].append(self.base.detected_by.copy())
        self.base.history["attack_window"].append(self.base.attack_window.copy())
        rewards = self.base._compute_rewards(prev_range, cur_range, prev_tracking, tracking, prev_window, window)
        if self.evader_escaped:
            rewards = rewards - 0.75
        dones = np.full((self.num_agents, 1), self.base.done, dtype=np.float32)
        info: dict[str, Any] = {
            "success": float(self.base.success),
            "evader_escape": float(self.evader_escaped),
            "timeout": float(timeout and not self.base.success and not self.evader_escaped and not self.base.collision and not self.base.constraint_violation),
            "collision": float(self.base.collision),
            "constraint_violation": float(self.base.constraint_violation),
            "branch_committed": float(self.exit_choice is not None),
            "exit_choice": float(self.exit_choice or 0),
            "primitive_action_interface": "3dof_27_discrete",
        }
        if self._coverage_at_branch is not None:
            info.update({f"branch_coverage_{key}": value for key, value in self._coverage_at_branch.items()})
        return self._get_obs(), self._get_share_obs(), self._get_graph_obs(), rewards, dones, info

    def _get_obs(self) -> np.ndarray:
        return self.base._get_obs()

    def _get_share_obs(self) -> np.ndarray:
        return self.base._get_share_obs()

    def _get_graph_obs(self) -> dict[str, np.ndarray]:
        graph = dict(self.base._get_graph_obs())
        # The legacy 3DOF graph encoder does not need a mask because every
        # primitive action is legal.  Keeping an explicit all-valid mask here
        # makes that invariant machine-checkable for any later learner.
        graph["action_masks"] = np.ones((self.num_agents, self.action_dim), dtype=np.int8)
        return graph
