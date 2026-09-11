"""Multi-stage civilian escort task with forecast-contingent commitments.

The task models three UAVs supporting a vehicle that will take one of two
route branches.  Before the fork, the branch is hidden but a public forecast
is available.  UAVs can commit to a left/right support corridor, remain in a
central fallback corridor, or reconfigure.  Reconfiguration takes time, so
the correct decision is contingent on forecast reliability rather than merely
on the eventual branch identity.

This environment is deliberately a transparent task substrate.  It contains
no learned method and no paper-performance claim.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


LEFT, CENTER, RIGHT = 0, 1, 2
WAIT, COMMIT_LEFT, COMMIT_CENTER, COMMIT_RIGHT = 0, 1, 2, 3


@dataclass(frozen=True)
class ForecastCommitmentScenario:
    """Frozen pre-fork forecast regime."""

    name: str
    early_right_probability: float


M2_COMMITMENT_SCENARIOS: tuple[ForecastCommitmentScenario, ...] = (
    ForecastCommitmentScenario("reliable_right_forecast", 0.90),
    ForecastCommitmentScenario("ambiguous_forecast", 0.50),
)


class ForecastCommitmentEscortEnv:
    """Three-UAV route-escort task with a delayed, irreversible commitment.

    The standard repository interface is preserved.  Pre-fork actor
    observations expose only the forecast and public clock; the true branch
    is not visible until the route actually diverges.  At the final pre-fork
    step, a reliable public cue arrives.  A new commitment takes two steps,
    hence waiting is safer under ambiguity but too late to give uninterrupted
    post-fork support.
    """

    num_agents = 3
    action_dim = 4
    horizon = 14
    fork_step = 6
    reveal_step = 5
    reconfiguration_lag = 2

    def __init__(self, scenario: ForecastCommitmentScenario, *, seed: int = 0):
        self.scenario = scenario
        self._rng = np.random.default_rng(seed)
        self.reset()

    def reset(self) -> tuple[np.ndarray, np.ndarray, dict[str, np.ndarray]]:
        self.step_count = 0
        self.done = False
        self._branch = int(self._rng.random() < self.scenario.early_right_probability)
        self._corridors = np.full(self.num_agents, CENTER, dtype=np.int64)
        self._pending_corridors = self._corridors.copy()
        self._lag_remaining = np.zeros(self.num_agents, dtype=np.int64)
        self._reconfigurations = 0
        self._branch_support_steps = 0
        self._wrong_corridor_steps = 0
        self._central_fallback_steps = 0
        return self.actor_observation(), self.critic_observation(), self.graph_observation()

    @property
    def _branch_corridor(self) -> int:
        return RIGHT if self._branch else LEFT

    def _visible_right_probability(self) -> float:
        if self.step_count < self.reveal_step:
            return self.scenario.early_right_probability
        if self.step_count < self.fork_step:
            return 0.97 if self._branch else 0.03
        return float(self._branch)

    def actor_observation(self) -> np.ndarray:
        """Actor state with no pre-fork branch leakage."""
        probability = self._visible_right_probability()
        rows = np.zeros((self.num_agents, 8), dtype=np.float32)
        for agent in range(self.num_agents):
            rows[agent, 0] = probability
            rows[agent, 1] = self.step_count / self.horizon
            rows[agent, 2] = max(0, self.fork_step - self.step_count) / self.fork_step
            rows[agent, 3 + self._corridors[agent]] = 1.0
            rows[agent, 6] = self._lag_remaining[agent] / self.reconfiguration_lag
            rows[agent, 7] = float(self.step_count >= self.fork_step)
        return rows

    def critic_observation(self) -> np.ndarray:
        """Centralized public state; branch remains hidden before the fork."""
        return np.concatenate((
            np.asarray((self._visible_right_probability(), self.step_count / self.horizon), dtype=np.float32),
            self._corridors.astype(np.float32) / 2.0,
            self._lag_remaining.astype(np.float32) / self.reconfiguration_lag,
        ))

    def graph_observation(self) -> dict[str, np.ndarray]:
        adjacency = np.ones((self.num_agents, self.num_agents), dtype=np.int8)
        np.fill_diagonal(adjacency, 0)
        return {
            "node_features": self.actor_observation(),
            "active_adj": adjacency,
            "roles": np.asarray((0, 1, 2), dtype=np.int64),
            "action_masks": np.ones((self.num_agents, self.action_dim), dtype=np.int8),
        }

    @staticmethod
    def _action_to_corridor(action: int, current: int) -> int:
        return current if action == WAIT else int(action - 1)

    def _apply_actions(self, actions: np.ndarray) -> None:
        for agent, action in enumerate(actions):
            if self._lag_remaining[agent] > 0:
                self._lag_remaining[agent] -= 1
                if self._lag_remaining[agent] == 0:
                    self._corridors[agent] = self._pending_corridors[agent]
                continue
            requested = self._action_to_corridor(int(action), int(self._corridors[agent]))
            if requested != self._corridors[agent]:
                self._pending_corridors[agent] = requested
                self._lag_remaining[agent] = self.reconfiguration_lag
                self._reconfigurations += 1

    def step(self, actions: np.ndarray | list[int]) -> tuple[np.ndarray, np.ndarray, dict[str, np.ndarray], np.ndarray, np.ndarray, dict[str, Any]]:
        if self.done:
            raise RuntimeError("reset required after terminal episode")
        actions = np.asarray(actions, dtype=np.int64).reshape(self.num_agents)
        actions = np.clip(actions, 0, self.action_dim - 1)
        self._apply_actions(actions)

        reward = -0.02 * float(np.count_nonzero(self._lag_remaining))
        correct_support = 0
        if self.step_count >= self.fork_step:
            correct_support = int(np.count_nonzero(self._corridors == self._branch_corridor))
            central_support = int(np.count_nonzero(self._corridors == CENTER))
            wrong_support = self.num_agents - correct_support - central_support
            # Two correct escorts protect the branch; the centre is a weaker,
            # but safe fallback.  The joint term makes independent greedy
            # commitment insufficient.
            reward += 1.0 * correct_support + 0.25 * central_support
            reward += 1.5 if correct_support >= 2 else -0.8
            self._branch_support_steps += correct_support
            self._central_fallback_steps += central_support
            self._wrong_corridor_steps += wrong_support

        self.step_count += 1
        self.done = self.step_count >= self.horizon
        rewards = np.full((self.num_agents, 1), reward, dtype=np.float32)
        dones = np.full((self.num_agents, 1), self.done, dtype=np.float32)
        info = {
            "forecast_right_probability": self._visible_right_probability(),
            "fork_has_occurred": bool(self.step_count >= self.fork_step),
            "pre_fork_branch_exposed": False,
            "reconfigurations": self._reconfigurations,
            "supporting_branch_agents": correct_support,
            "lagged_agents": int(np.count_nonzero(self._lag_remaining)),
        }
        return self.actor_observation(), self.critic_observation(), self.graph_observation(), rewards, dones, info

    def terminal_summary(self) -> dict[str, Any]:
        return {
            "scenario": self.scenario.name,
            "branch": "right" if self._branch else "left",
            "reconfigurations": int(self._reconfigurations),
            "branch_support_steps": int(self._branch_support_steps),
            "central_fallback_steps": int(self._central_fallback_steps),
            "wrong_corridor_steps": int(self._wrong_corridor_steps),
        }


class ForecastCommitmentEscortV2Env(ForecastCommitmentEscortEnv):
    """A commitment-sensitive variant with an explicit redeployment cost.

    Version 1 allowed a UAV that had already entered a branch corridor to
    reverse course after the late cue at the same cost as an uncommitted UAV
    leaving the central holding corridor.  That made an early, incorrect
    commitment cheaply reversible and erased the intended distinction between
    acting on a reliable forecast and waiting for information.

    In this version, first dispatch from the central holding corridor retains
    the two-step setup delay, whereas moving an already deployed UAV to a
    different corridor incurs a longer redeployment delay.  The distinction is
    an environment property, not an observation or training-side advantage:
    all policies observe the same public forecast and late cue.
    """

    initial_dispatch_lag = 2
    redeployment_lag = 6

    def _apply_actions(self, actions: np.ndarray) -> None:
        for agent, action in enumerate(actions):
            if self._lag_remaining[agent] > 0:
                self._lag_remaining[agent] -= 1
                if self._lag_remaining[agent] == 0:
                    self._corridors[agent] = self._pending_corridors[agent]
                continue

            current = int(self._corridors[agent])
            requested = self._action_to_corridor(int(action), current)
            if requested == current:
                continue

            self._pending_corridors[agent] = requested
            # A UAV staged in the holding corridor can be dispatched quickly.
            # Any subsequent corridor change represents redeployment from an
            # active support position and therefore costs more time.
            lag = self.initial_dispatch_lag if current == CENTER else self.redeployment_lag
            self._lag_remaining[agent] = lag
            self._reconfigurations += 1


class ForecastCommitmentEscortV3Env(ForecastCommitmentEscortV2Env):
    """Commitment-v2 with a one-step forecast decision window.

    The initial forecast is a time-stamped dispatch advisory, rather than a
    continuously refreshed signal.  It is public at reset only; during the
    holding interval the policy receives an uninformative value until the
    near-fork cue arrives.  This prevents a policy from postponing the same
    forecast-based commitment until immediately before the cue while preserving
    identical information for every compared policy.
    """

    def _visible_right_probability(self) -> float:
        if self.step_count == 0:
            return self.scenario.early_right_probability
        if self.step_count < self.reveal_step:
            return 0.5
        if self.step_count < self.fork_step:
            return 0.97 if self._branch else 0.03
        return float(self._branch)
