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

from envs.active_diagnosis_semantic_env import (
    FAILURE_HYPOTHESES,
    HARD_RELAY_FAILURE,
    RECOVERABLE_RANGE_LOSS,
)
from envs.uav_intercept_3d_env import ACTION3D_TABLE, UAVIntercept3DConfig, UAVIntercept3DEnv


@dataclass(frozen=True)
class ActiveDiagnosisTrainableConfig:
    hypothesis: str = RECOVERABLE_RANGE_LOSS
    seed: int = 0
    probe_duration_steps: int = 12
    max_probe_count: int = 1

    def __post_init__(self) -> None:
        if self.hypothesis not in FAILURE_HYPOTHESES:
            raise ValueError(f"unknown hypothesis: {self.hypothesis}")
        if self.probe_duration_steps != 12:
            raise ValueError("P3A freezes the P1C-validated 12-step physical probe")
        if self.max_probe_count != 1:
            raise ValueError("P3A permits exactly one probe per episode")


class ActiveDiagnosisTrainableUAVEnv:
    """Standard reset/step environment with one relay-only diagnostic option."""

    runtime_format = "active_diagnosis_trainable_uav_state_v1"
    relay_id = 1
    attacker_id = 2

    def __init__(self, config: ActiveDiagnosisTrainableConfig | None = None) -> None:
        self.config = config or ActiveDiagnosisTrainableConfig()
        failed_agent = self.relay_id if self.config.hypothesis == HARD_RELAY_FAILURE else -1
        self.base = UAVIntercept3DEnv(
            UAVIntercept3DConfig(
                business_grounded_geometry=True,
                communication_range_scale=0.5,
                communication_dropout_prob=0.0,
                strict_target_sensing=True,
                agent_target_info_bottleneck=True,
                relay_dependent_task=True,
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
        self.action_dim = self.flight_action_dim + 1
        self.num_agents = int(self.base.num_agents)
        self.n = self.num_agents
        self.obs_dim = int(self.base.obs_dim + 3)
        self.share_obs_dim = int(self.base.share_obs_dim + 3)
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
        return self._observation()

    def _diagnostic_features(self) -> np.ndarray:
        available = float(self.probe_count < self.config.max_probe_count and self.probe_remaining == 0)
        active = float(self.probe_remaining > 0)
        return np.asarray([available, active, self.probe_ack_state], dtype=np.float32)

    def action_masks(self) -> np.ndarray:
        masks = np.ones((self.num_agents, self.action_dim), dtype=np.float32)
        masks[:, self.probe_action] = 0.0
        if self.probe_remaining > 0:
            masks[self.relay_id, :] = 0.0
            masks[self.relay_id, self.probe_action] = 1.0
        elif self.probe_count < self.config.max_probe_count:
            masks[self.relay_id, self.probe_action] = 1.0
        return masks

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

        base_actions = actions.copy()
        base_actions[base_actions == self.probe_action] = self.neutral_action
        obs, share, _, rewards, dones, info = self.base.step(base_actions)
        del obs, share

        if self.probe_remaining > 0:
            self.probe_remaining -= 1
            if self.probe_remaining == 0:
                ack = bool(
                    self.base.comm_adj[self.attacker_id, self.relay_id] > 0.5
                    and self.base.comm_adj[self.relay_id, self.attacker_id] > 0.5
                )
                self.probe_ack_state = 1.0 if ack else -1.0

        info = dict(info)
        info.update(
            {
                "probe_started": bool(starting_probe),
                "probe_active": bool(self.probe_remaining > 0),
                "probe_count": int(self.probe_count),
                "probe_ack_state": float(self.probe_ack_state),
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
            "runtime_seed": self._runtime_seed,
            "base": self.base.runtime_state_dict(),
        }

    def load_runtime_state_dict(self, state: dict) -> None:
        if state.get("format") != self.runtime_format or state.get("config") != self.config:
            raise ValueError("incompatible active-diagnosis runtime state")
        self.probe_count = int(state["probe_count"])
        self.probe_remaining = int(state["probe_remaining"])
        self.probe_ack_state = float(state["probe_ack_state"])
        self._runtime_seed = int(state["runtime_seed"])
        self.base.load_runtime_state_dict(deepcopy(state["base"]))
