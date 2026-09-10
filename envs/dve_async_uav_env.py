"""Minimal asynchronous UAV task for decision-validity identifiability audits.

This is deliberately a small deterministic environment.  It is not a performance
benchmark and does not contain a learned DVE method.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

import numpy as np


@dataclass(frozen=True)
class DVECase:
    latency_ms: float
    state_drift: float
    task_relevant: bool
    corridor_reserved: bool


class DVEAsyncUAVEnv:
    """Two-agent, one-decision environment with a standard repository interface."""

    n_agents = 2
    action_dim = 2  # 0=fallback/hold, 1=accept stale corridor-entry command

    def __init__(self, case: DVECase | None = None) -> None:
        self.case = case or DVECase(80.0, 1.0, True, False)
        self._done = False

    def _obs(self) -> Tuple[np.ndarray, np.ndarray, Dict[str, np.ndarray]]:
        local = np.asarray(
            [
                self.case.latency_ms / 100.0,
                self.case.state_drift / 4.0,
                float(self.case.task_relevant),
                float(self.case.corridor_reserved),
            ],
            dtype=np.float32,
        )
        obs = np.stack([local, local], axis=0)
        share_obs = obs.reshape(-1).copy()
        graph_obs = {
            "node_features": obs.copy(),
            "edge_index": np.asarray([[0, 1], [1, 0]], dtype=np.int64),
        }
        return obs, share_obs, graph_obs

    def reset(self) -> Tuple[np.ndarray, np.ndarray, Dict[str, np.ndarray]]:
        self._done = False
        return self._obs()

    @property
    def hard_safe(self) -> bool:
        return self.case.state_drift <= 3.0

    @property
    def stale_action_valid(self) -> bool:
        return (
            self.case.state_drift <= 2.0
            and self.case.task_relevant
            and not self.case.corridor_reserved
        )

    def step(self, actions: np.ndarray):
        if self._done:
            raise RuntimeError("reset must be called before another step")
        actions = np.asarray(actions, dtype=np.int64).reshape(self.n_agents)
        if np.any((actions < 0) | (actions >= self.action_dim)):
            raise ValueError("actions must be 0 (fallback) or 1 (accept)")

        accept_count = int(actions.sum())
        joint_conflict = accept_count > 1 or (accept_count > 0 and self.case.corridor_reserved)
        stale_accept = accept_count > 0 and not self.stale_action_valid

        if joint_conflict:
            team_value = -10.0
        elif accept_count == 1 and self.stale_action_valid:
            team_value = 8.0
        elif accept_count == 0:
            team_value = 3.0 if self.case.task_relevant else 5.0
        else:
            team_value = 0.0

        self._done = True
        obs, share_obs, graph_obs = self._obs()
        rewards = np.full(self.n_agents, team_value, dtype=np.float32)
        dones = np.ones(self.n_agents, dtype=bool)
        infos = [
            {
                "team_value": team_value,
                "stale_action_valid": self.stale_action_valid,
                "stale_accept": stale_accept,
                "joint_conflict": joint_conflict,
                "hard_safe": self.hard_safe,
            }
            for _ in range(self.n_agents)
        ]
        return obs, share_obs, graph_obs, rewards, dones, infos

