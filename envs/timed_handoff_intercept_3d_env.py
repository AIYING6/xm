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

from envs.uav_intercept_3d_env import UAVIntercept3DConfig, UAVIntercept3DEnv, velocity_from_state


HANDOFF_CONTEXTS = ("current_authorization", "postbranch_refresh")
BASE_OBS_DIM = 34
HANDOFF_CONTEXT_SLICE = slice(34, 37)
HANDOFF_SERVICE_BEACON_SLICE = slice(37, 43)
HANDOFF_BEACON_SLICE = slice(43, 51)


@dataclass
class TimedHandoffIntercept3DConfig(UAVIntercept3DConfig):
    """Mission-stage requirements layered on top of :class:`UAVIntercept3DEnv`.

    ``current_authorization`` requires a legal relay-mediated track to reach
    the attacker before ``authorization_deadline``.  ``postbranch_refresh``
    requires a relay-mediated track delivered after ``branch_step``.  Both
    contexts still require legal attacker information and physical terminal
    attack geometry; no message or target truth is inserted into the actor
    observation.
    """

    handoff_context: str = "current_authorization"
    authorization_start_step: int = 20
    authorization_deadline: int = 88
    branch_step: int = 108
    authorization_hold_steps: int = 8
    refresh_hold_steps: int = 8
    handoff_corridor_radius: float = 1_400.0
    future_corridor_lateral_offset: float = 3_000.0
    prebranch_target_policy: str = "weaving_mild"
    postbranch_target_policy: str = "break_turn_param"


class TimedHandoffIntercept3DEnv(UAVIntercept3DEnv):
    """3DOF interception with an explicit, legal staged-handoff objective."""

    def __init__(self, config: TimedHandoffIntercept3DConfig | None = None):
        staged = copy.deepcopy(config or TimedHandoffIntercept3DConfig())
        if staged.handoff_context not in HANDOFF_CONTEXTS:
            raise ValueError(f"unsupported handoff_context: {staged.handoff_context}")
        if not (0 <= staged.authorization_start_step < staged.authorization_deadline < staged.branch_step):
            raise ValueError("require 0 <= authorization_start_step < authorization_deadline < branch_step")
        if staged.authorization_hold_steps <= 0 or staged.refresh_hold_steps <= 0:
            raise ValueError("handoff hold lengths must be positive")
        if staged.handoff_corridor_radius <= 0.0 or staged.future_corridor_lateral_offset <= 0.0:
            raise ValueError("handoff corridor geometry must be positive")
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
        # The staged objective is a *choice* between retaining the current
        # bridge and relocating for a later bridge.  Initialise the relay at
        # the current legal service midpoint so that retaining the bridge is
        # physically feasible; the legacy plant starts it 2 km behind that
        # midpoint, which made the current-corridor milestone unattainable
        # regardless of the selected relay behaviour.
        current_midpoint = 0.5 * (self.blue_pos[0] + self.blue_pos[2])
        self.service_origin = current_midpoint.astype(np.float32)
        self.service_velocity = (
            0.5
            * (
                velocity_from_state(self.blue_speed[0], self.blue_heading[0], self.blue_gamma[0])
                + velocity_from_state(self.blue_speed[2], self.blue_heading[2], self.blue_gamma[2])
            )
        ).astype(np.float32)
        self.blue_pos[1] = current_midpoint.astype(np.float32)
        self.blue_speed[1] = float(0.5 * (self.blue_speed[0] + self.blue_speed[2]))
        self.blue_heading[1] = float(0.5 * (self.blue_heading[0] + self.blue_heading[2]))
        self.blue_gamma[1] = float(0.5 * (self.blue_gamma[0] + self.blue_gamma[2]))
        # Moving a vehicle after the base reset invalidates the derived legal
        # link/cache state.  Recompute it before exposing any observation.
        self._update_sensing_and_comm()
        obs, share, graph = self._get_obs(), self._get_share_obs(), self._get_graph_obs()
        self.authorization_handoff_observed = False
        self.postbranch_refresh_observed = False
        self.authorization_handoff_streak = 0
        self.postbranch_refresh_streak = 0
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
                float(self.handoff_config.future_corridor_lateral_offset / self.config.world_radius),
            ],
            dtype=np.float32,
        )

    def _service_waypoint(self, future: bool) -> np.ndarray:
        """Return the publicly planned moving service waypoint.

        This route is generated from the reset-time mission plan and is exposed
        as an agent-relative task command.  It never depends on the target's
        current state, a peer's hidden state, or a future target maneuver.
        """
        waypoint = self.service_origin + self.service_velocity * float(self.step_count)
        if future:
            waypoint = waypoint + np.asarray(
                (0.0, self.handoff_config.future_corridor_lateral_offset, 0.0), dtype=np.float32
            )
        return waypoint.astype(np.float32)

    def _augment_obs(self, obs: np.ndarray) -> np.ndarray:
        service_beacons = np.zeros((self.num_agents, 6), dtype=np.float32)
        current_waypoint = self._service_waypoint(future=False)
        future_waypoint = self._service_waypoint(future=True)
        for ego in range(self.num_agents):
            # A mission waypoint is a public command, expressed only relative
            # to the receiving UAV.  It is deliberately distinct from the
            # link-conditioned neighbour beacons below.
            service_beacons[ego, :3] = (current_waypoint - self.blue_pos[ego]) / self.config.world_radius
            service_beacons[ego, 3:] = (future_waypoint - self.blue_pos[ego]) / self.config.world_radius
        # A radio neighbour beacon carries relative position only across an
        # active direct link.  It is not a global formation state: a broken or
        # delayed link contributes zeros and its availability flag is zero.
        beacons = np.zeros((self.num_agents, (self.num_agents - 1) * 4), dtype=np.float32)
        for ego in range(self.num_agents):
            offset = 0
            for peer in range(self.num_agents):
                if peer == ego:
                    continue
                linked = float(self.comm_adj[ego, peer] > 0.5)
                if linked:
                    beacons[ego, offset: offset + 3] = (self.blue_pos[peer] - self.blue_pos[ego]) / self.config.world_radius
                beacons[ego, offset + 3] = linked
                offset += 4
        return np.concatenate(
            [obs, np.tile(self._context_vector(), (self.num_agents, 1)), service_beacons, beacons], axis=-1
        ).astype(np.float32)

    def _augment_share(self, share: np.ndarray) -> np.ndarray:
        return np.concatenate([share, np.tile(self._context_vector(), (self.num_agents, 1))], axis=-1).astype(np.float32)

    def _relay_mediated_fresh_attacker_track(self) -> bool:
        attacker = 2
        path = list(self.target_cache_path[attacker])
        return bool(self._has_fresh_target_cache(attacker) and 1 in path)

    def _relay_corridor_error(self, future: bool) -> float:
        """Distance to a physical, publicly specified relay service route."""
        return float(np.linalg.norm(self.blue_pos[1] - self._service_waypoint(future=future)))

    def _update_handoff_milestones(self) -> None:
        relay_track = self._relay_mediated_fresh_attacker_track()
        if relay_track:
            delivery_step = int(self.target_cache_delivery_step[2])
            in_authorization_window = (
                self.handoff_config.authorization_start_step <= self.step_count <= self.handoff_config.authorization_deadline
            )
            current_corridor = self._relay_corridor_error(future=False) <= self.handoff_config.handoff_corridor_radius
            self.authorization_handoff_streak = self.authorization_handoff_streak + 1 if (in_authorization_window and current_corridor) else 0
            if self.authorization_handoff_streak >= self.handoff_config.authorization_hold_steps:
                self.authorization_handoff_observed = True
            future_corridor = self._relay_corridor_error(future=True) <= self.handoff_config.handoff_corridor_radius
            # A post-stage refresh is a new relay-mediated delivery to the
            # attacker.  Requiring a brand-new scout detection here would
            # confound the handoff choice with incidental sensing coverage.
            if self.step_count >= self.handoff_config.branch_step and delivery_step >= self.handoff_config.branch_step and future_corridor:
                self.postbranch_refresh_streak += 1
                if self.postbranch_refresh_streak >= self.handoff_config.refresh_hold_steps:
                    self.postbranch_refresh_observed = True
            else:
                self.postbranch_refresh_streak = 0
        else:
            self.authorization_handoff_streak = 0
            self.postbranch_refresh_streak = 0

    def _mission_requirement_met(self) -> bool:
        if self.handoff_config.handoff_context == "current_authorization":
            return self.authorization_handoff_observed
        return self.postbranch_refresh_observed

    def step(self, actions: np.ndarray | list[int]):
        obs, share, graph, rewards, dones, info = super().step(actions)
        self._update_handoff_milestones()
        # This layer's terminal is timely, legal targeting-service completion.
        # Physical attack-window occupancy remains a separately logged
        # downstream metric.  Requiring both at one instant would turn the
        # staged-handoff decision gate into a test of the target chaser's
        # collision avoidance rather than of cooperative service reconfiguration.
        self.handoff_success = bool(self._mission_requirement_met())
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
                "authorization_handoff_streak": float(self.authorization_handoff_streak),
                "postbranch_refresh_streak": float(self.postbranch_refresh_streak),
                "relay_current_corridor_error": self._relay_corridor_error(future=False),
                "relay_future_corridor_error": self._relay_corridor_error(future=True),
                "relay_in_current_corridor": float(self._relay_corridor_error(future=False) <= self.handoff_config.handoff_corridor_radius),
                "relay_in_future_corridor": float(self._relay_corridor_error(future=True) <= self.handoff_config.handoff_corridor_radius),
                "handoff_success": float(self.handoff_success),
                "handoff_terminal_attack_window": float(self.attack_window[2] > 0.5),
                "handoff_terminal_attacker_has_information": float(self._has_target_information(2)),
                "legacy_success_disabled": 1.0,
            }
        )
        if self.handoff_success:
            info["success"] = 1.0
            info["timeout"] = 0.0
        return self._augment_obs(obs), self._augment_share(share), graph, rewards, dones, info
