"""Trainable 3DOF interface for decision-relevant active diagnosis.

This opt-in wrapper leaves :class:`UAVIntercept3DEnv` unchanged.  It adds one
relay-only macro action that executes the legal physical handshake used by the
P1C shadow audit.  The latent failure hypothesis is never appended to actor
observations or graph features.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass

import numpy as np

from envs.active_diagnosis_semantic_env import RECOVERABLE_RANGE_LOSS
from envs.uav_intercept_3d_env import (
    ACTION3D_TABLE,
    UAVIntercept3DConfig,
    UAVIntercept3DEnv,
    angle_diff,
)


HARD_TERMINAL_COMM_FAILURE = "hard_terminal_comm_failure"
TRAINABLE_FAILURE_HYPOTHESES = (RECOVERABLE_RANGE_LOSS, HARD_TERMINAL_COMM_FAILURE)


@dataclass(frozen=True)
class ActiveDiagnosisTrainableConfig:
    hypothesis: str = RECOVERABLE_RANGE_LOSS
    seed: int = 0
    probe_duration_steps: int = 12
    max_probe_count: int = 1
    probe_utility_cost: float = 0.12
    fallback_duration_steps: int = 24
    max_fallback_count: int = 1

    def __post_init__(self) -> None:
        if self.hypothesis not in TRAINABLE_FAILURE_HYPOTHESES:
            raise ValueError(f"unknown hypothesis: {self.hypothesis}")
        if self.probe_duration_steps != 12:
            raise ValueError("P3A freezes the P1C-validated 12-step physical probe")
        if self.max_probe_count != 1:
            raise ValueError("P3A permits exactly one probe per episode")
        if not 0.0 < self.probe_utility_cost < 1.0:
            raise ValueError("probe utility cost must be positive and bounded")
        if self.fallback_duration_steps != 24 or self.max_fallback_count != 1:
            raise ValueError("P3B freezes one 24-step prior-guided fallback option")


class ActiveDiagnosisTrainableUAVEnv:
    """Standard reset/step environment with one relay-only diagnostic option."""

    runtime_format = "active_diagnosis_trainable_uav_state_v1"
    relay_id = 1
    attacker_id = 2

    def __init__(self, config: ActiveDiagnosisTrainableConfig | None = None) -> None:
        self.config = config or ActiveDiagnosisTrainableConfig()
        # The hard mode disables the terminal communication interface. At the
        # frozen initial geometry this is actor-observation equivalent to the
        # recoverable relay-terminal range gap, while leaving direct sensing
        # as a physically available fallback.
        failed_agent = self.attacker_id if self.config.hypothesis == HARD_TERMINAL_COMM_FAILURE else -1
        self.base = UAVIntercept3DEnv(
            UAVIntercept3DConfig(
                business_grounded_geometry=True,
                communication_range_scale=0.64,
                communication_dropout_prob=0.0,
                strict_target_sensing=True,
                agent_target_info_bottleneck=True,
                relay_dependent_task=True,
                target_policy="straight",
                failed_blue_agent=failed_agent,
                node_failure_start_step=0,
                node_failure_duration_steps=260,
                seed=self.config.seed,
            )
        )
        neutral = np.flatnonzero(np.all(ACTION3D_TABLE == 0.0, axis=1))
        if neutral.size != 1:
            raise AssertionError("3DOF action table must contain exactly one neutral action")
        self.neutral_action = int(neutral[0])
        self.flight_action_dim = int(self.base.action_dim)
        self.probe_action = self.flight_action_dim
        self.fallback_action = self.flight_action_dim + 1
        self.action_dim = self.flight_action_dim + 2
        self.num_agents = int(self.base.num_agents)
        self.n = self.num_agents
        self.obs_dim = int(self.base.obs_dim + 5)
        self.share_obs_dim = int(self.base.share_obs_dim + 5)
        self.node_feat_dim = self.obs_dim
        self._runtime_seed = int(self.config.seed)
        self.reset()

    @property
    def hypothesis(self) -> str:
        """Audit-only latent state; callers must not expose it to the actor."""
        return self.config.hypothesis

    @property
    def done(self) -> bool:
        return bool(self.base.done)

    @property
    def step_count(self) -> int:
        return int(self.base.step_count)

    def seed(self, seed: int) -> None:
        self._runtime_seed = int(seed)
        self.base.seed(self._runtime_seed)

    def reset(self) -> tuple[np.ndarray, np.ndarray, dict[str, np.ndarray]]:
        self.base.seed(self._runtime_seed)
        self.base.reset()
        self.base.blue_pos = np.asarray(
            [[-2_000.0, -5_500.0, 5_000.0], [-2_000.0, 0.0, 5_000.0], [-2_000.0, 5_500.0, 5_000.0]],
            dtype=np.float32,
        )
        self.base.blue_heading = np.asarray([0.0, np.pi / 2.0, 0.0], dtype=np.float32)
        self.base.blue_gamma[:] = 0.0
        self.base._update_sensing_and_comm()
        self.probe_count = 0
        self.probe_remaining = 0
        self.probe_ack_state = 0.0  # 0 unknown, +1 ack, -1 completed without ack
        self.fallback_count = 0
        self.fallback_remaining = 0
        return self._observation()

    def _diagnostic_features(self) -> np.ndarray:
        available = float(self.probe_count < self.config.max_probe_count and self.probe_remaining == 0)
        active = float(self.probe_remaining > 0)
        fallback_available = float(
            self.fallback_count < self.config.max_fallback_count and self.fallback_remaining == 0
        )
        fallback_active = float(self.fallback_remaining > 0)
        return np.asarray(
            [available, active, self.probe_ack_state, fallback_available, fallback_active],
            dtype=np.float32,
        )

    def action_masks(self) -> np.ndarray:
        masks = np.ones((self.num_agents, self.action_dim), dtype=np.float32)
        masks[:, self.probe_action :] = 0.0
        if self.probe_remaining > 0:
            masks[self.relay_id, :] = 0.0
            masks[self.relay_id, self.probe_action] = 1.0
        elif self.probe_count < self.config.max_probe_count:
            masks[self.relay_id, self.probe_action] = 1.0
        if self.fallback_remaining > 0:
            masks[self.attacker_id, :] = 0.0
            masks[self.attacker_id, self.fallback_action] = 1.0
        elif self.fallback_count < self.config.max_fallback_count:
            masks[self.attacker_id, self.fallback_action] = 1.0
        return masks

    def _fallback_flight_action(self) -> int:
        """Prior-guided search command using no latent or true target state."""
        attacker = self.attacker_id
        prior = np.asarray(self.base.config.target_prior_position, dtype=np.float32)
        rel = prior - self.base.blue_pos[attacker]
        desired_heading = np.arctan2(float(rel[1]), float(rel[0]))
        heading_error = angle_diff(float(desired_heading), float(self.base.blue_heading[attacker]))
        turn = float(np.sign(heading_error))
        altitude_error = float(rel[2])
        climb = float(np.sign(altitude_error)) if abs(altitude_error) > 100.0 else 0.0
        score = (
            np.abs(ACTION3D_TABLE[:, 0] - turn)
            + np.abs(ACTION3D_TABLE[:, 1] - climb)
            + 0.1 * np.abs(ACTION3D_TABLE[:, 2] - 1.0)
        )
        return int(np.argmin(score))

    def _observation(self) -> tuple[np.ndarray, np.ndarray, dict[str, np.ndarray]]:
        obs = self.base._get_obs()
        share = self.base._get_share_obs()
        features = self._diagnostic_features()
        obs = np.concatenate((obs, np.tile(features, (self.num_agents, 1))), axis=1).astype(np.float32)
        share = np.concatenate((share, np.tile(features, (self.num_agents, 1))), axis=1).astype(np.float32)
        graph = {
            "node_features": obs.copy(),
            "roles": np.asarray([typ.role for typ in self.base.config.blue_types], dtype=np.int64),
            "active_adj": self.base.comm_adj.copy().astype(np.float32),
            "action_masks": self.action_masks(),
        }
        return obs, share, graph

    def step(self, actions: np.ndarray | list[int]):
        if self.done:
            raise RuntimeError("Call reset() before stepping a finished episode")
        actions = np.asarray(actions, dtype=np.int64).reshape(self.num_agents)
        masks = self.action_masks()
        if np.any(actions < 0) or np.any(actions >= self.action_dim):
            raise ValueError("action outside active-diagnosis alphabet")
        if not np.all(masks[np.arange(self.num_agents), actions] > 0):
            raise ValueError("masked action is not executable")

        starting_probe = self.probe_remaining == 0 and int(actions[self.relay_id]) == self.probe_action
        if starting_probe:
            self.probe_count += 1
            self.probe_remaining = self.config.probe_duration_steps
            self.probe_ack_state = 0.0

        starting_fallback = (
            self.fallback_remaining == 0
            and int(actions[self.attacker_id]) == self.fallback_action
        )
        if starting_fallback:
            self.fallback_count += 1
            self.fallback_remaining = self.config.fallback_duration_steps

        base_actions = actions.copy()
        base_actions[base_actions == self.probe_action] = self.neutral_action
        base_actions[base_actions == self.fallback_action] = self.neutral_action
        if self.fallback_remaining > 0:
            base_actions[self.attacker_id] = self._fallback_flight_action()
        obs, share, _, rewards, dones, info = self.base.step(base_actions)
        del obs, share
        if starting_probe:
            rewards = rewards - np.float32(self.config.probe_utility_cost)

        if self.probe_remaining > 0:
            self.probe_remaining -= 1
            if self.probe_remaining == 0:
                ack = bool(
                    self.base.comm_adj[self.attacker_id, self.relay_id] > 0.5
                    and self.base.comm_adj[self.relay_id, self.attacker_id] > 0.5
                )
                self.probe_ack_state = 1.0 if ack else -1.0
        if self.fallback_remaining > 0:
            self.fallback_remaining -= 1

        info = dict(info)
        info.update(
            {
                "probe_started": bool(starting_probe),
                "probe_active": bool(self.probe_remaining > 0),
                "probe_count": int(self.probe_count),
                "probe_ack_state": float(self.probe_ack_state),
                "fallback_started": bool(starting_fallback),
                "fallback_active": bool(self.fallback_remaining > 0),
                "fallback_count": int(self.fallback_count),
                "latent_hypothesis_exposed_to_actor": False,
            }
        )
        next_obs, next_share, graph = self._observation()
        return next_obs, next_share, graph, rewards, dones, info

    def runtime_state_dict(self) -> dict:
        return {
            "format": self.runtime_format,
            "config": self.config,
            "probe_count": self.probe_count,
            "probe_remaining": self.probe_remaining,
            "probe_ack_state": self.probe_ack_state,
            "fallback_count": self.fallback_count,
            "fallback_remaining": self.fallback_remaining,
            "runtime_seed": self._runtime_seed,
            "base": self.base.runtime_state_dict(),
        }

    def load_runtime_state_dict(self, state: dict) -> None:
        if state.get("format") != self.runtime_format or state.get("config") != self.config:
            raise ValueError("incompatible active-diagnosis runtime state")
        self.probe_count = int(state["probe_count"])
        self.probe_remaining = int(state["probe_remaining"])
        self.probe_ack_state = float(state["probe_ack_state"])
        self.fallback_count = int(state["fallback_count"])
        self.fallback_remaining = int(state["fallback_remaining"])
        self._runtime_seed = int(state["runtime_seed"])
        self.base.load_runtime_state_dict(deepcopy(state["base"]))
