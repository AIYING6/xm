"""Timed-handoff mission layer for the existing 3DOF interception plant.

The layer preserves the underlying flight dynamics, sensing, message delivery
and 27 primitive flight actions.  It changes only the mission completion
contract: a successful interception must contain a legal relay-mediated target
handoff in a specified temporal stage.  This produces a testable distinction
between retaining a current relay bridge and preparing a later one.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Dict, Tuple

import numpy as np

from envs.uav_intercept_3d_env import UAVIntercept3DConfig, UAVIntercept3DEnv


HANDOFF_CONTEXTS = ("current_authorization", "postbranch_refresh")


@dataclass
class TimedHandoffIntercept3DConfig(UAVIntercept3DConfig):
    """Mission-stage requirements layered on top of :class:`UAVIntercept3DEnv`.

    ``current_authorization`` requires a legal relay-mediated track to reach
    the attacker before ``authorization_deadline``.  ``postbranch_refresh``
    requires a relay-mediated track generated after ``branch_step``.  Both
    contexts still require legal attacker information and physical terminal
    attack geometry; no message or target truth is inserted into the actor
    observation.
    """

    handoff_context: str = "current_authorization"
    authorization_deadline: int = 88
    branch_step: int = 108
    prebranch_target_policy: str = "weaving_mild"
    postbranch_target_policy: str = "break_turn_param"


class TimedHandoffIntercept3DEnv(UAVIntercept3DEnv):
    """3DOF interception with an explicit, legal staged-handoff objective."""

    def __init__(self, config: TimedHandoffIntercept3DConfig | None = None):
        staged = copy.deepcopy(config or TimedHandoffIntercept3DConfig())
        if staged.handoff_context not in HANDOFF_CONTEXTS:
            raise ValueError(f"unsupported handoff_context: {staged.handoff_context}")
        if staged.authorization_deadline <= 0 or staged.branch_step <= staged.authorization_deadline:
            raise ValueError("require 0 < authorization_deadline < branch_step")
        # The base environment must not independently terminate on its legacy
        # chain-closed condition.  Its physics, information propagation and
        # safety termination remain intact; this layer owns mission success.
        staged.strict_target_sensing = True
        staged.agent_target_info_bottleneck = True
        staged.relay_dependent_task = True
        staged.min_success_step = staged.max_steps + 1
        # The base constructor invokes reset(), so the staged contract must be
        # available before delegating to it.
        self.handoff_config: TimedHandoffIntercept3DConfig = staged
        super().__init__(staged)

    def reset(self) -> Tuple[np.ndarray, np.ndarray, Dict[str, np.ndarray]]:
        obs, share, graph = super().reset()
        self.authorization_handoff_observed = False
        self.postbranch_refresh_observed = False
        self.handoff_success = False
        self.handoff_branch_active = False
        return self._augment_obs(obs), self._augment_share(share), graph

    def _move_red(self) -> None:
        """Use a scheduled maneuver change without exposing future truth."""
        policy = self.config.target_policy
        self.handoff_branch_active = bool(self.step_count >= self.handoff_config.branch_step)
        self.config.target_policy = (
            self.handoff_config.postbranch_target_policy
            if self.handoff_branch_active
            else self.handoff_config.prebranch_target_policy
        )
        try:
            super()._move_red()
        finally:
            self.config.target_policy = policy

    def _context_vector(self) -> np.ndarray:
        # Mission service class is public before the decision; target branch
        # direction is deliberately not included.
        return np.asarray(
            [
                float(self.handoff_config.handoff_context == "current_authorization"),
                float(self.handoff_config.handoff_context == "postbranch_refresh"),
            ],
            dtype=np.float32,
        )

    def _augment_obs(self, obs: np.ndarray) -> np.ndarray:
        return np.concatenate([obs, np.tile(self._context_vector(), (self.num_agents, 1))], axis=-1).astype(np.float32)

    def _augment_share(self, share: np.ndarray) -> np.ndarray:
        return np.concatenate([share, np.tile(self._context_vector(), (self.num_agents, 1))], axis=-1).astype(np.float32)

    def _relay_mediated_fresh_attacker_track(self) -> bool:
        attacker = 2
        path = list(self.target_cache_path[attacker])
        return bool(self._has_fresh_target_cache(attacker) and 1 in path)

    def _update_handoff_milestones(self) -> None:
        if self._relay_mediated_fresh_attacker_track():
            generation_step = int(self.target_cache_generation_step[2])
            if self.step_count <= self.handoff_config.authorization_deadline:
                self.authorization_handoff_observed = True
            if self.step_count >= self.handoff_config.branch_step and generation_step >= self.handoff_config.branch_step:
                self.postbranch_refresh_observed = True

    def _mission_requirement_met(self) -> bool:
        if self.handoff_config.handoff_context == "current_authorization":
            return self.authorization_handoff_observed
        return self.postbranch_refresh_observed

    def step(self, actions: np.ndarray | list[int]):
        obs, share, graph, rewards, dones, info = super().step(actions)
        self._update_handoff_milestones()
        attacker_window_and_info = bool(
            self.attack_window[2] > 0.5 and self._has_target_information(2)
        )
        self.handoff_success = bool(self._mission_requirement_met() and attacker_window_and_info)
        if self.handoff_success and not bool(dones[0, 0]):
            self.done = True
            dones = np.ones_like(dones, dtype=np.float32)
            rewards = rewards + 2.0
        info = dict(info)
        info.update(
            {
                "handoff_context_current_authorization": float(self.handoff_config.handoff_context == "current_authorization"),
                "handoff_context_postbranch_refresh": float(self.handoff_config.handoff_context == "postbranch_refresh"),
                "handoff_branch_active": float(self.handoff_branch_active),
                "authorization_handoff_observed": float(self.authorization_handoff_observed),
                "postbranch_refresh_observed": float(self.postbranch_refresh_observed),
                "handoff_success": float(self.handoff_success),
                "legacy_success_disabled": 1.0,
            }
        )
        if self.handoff_success:
            info["success"] = 1.0
            info["timeout"] = 0.0
        return self._augment_obs(obs), self._augment_share(share), graph, rewards, dones, info
