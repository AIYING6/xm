"""Minimal dynamic cooperative active-perception environment for A0.

The task is a benign civilian monitoring scenario: three heterogeneous UAVs
track a moving environmental event through noisy bearing-only measurements.
The target truth is used exclusively inside the transition and measurement
model.  Execution observations contain the public Gaussian belief, each UAV's
own position and sensor specification, but never the target truth.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from envs.observability_active_perception import log_determinant, marginal_bearing_contributions


HOLD, EAST, WEST, NORTH, SOUTH = range(5)


@dataclass(frozen=True)
class ActivePerceptionUAV:
    speed: float
    sensing_range: float
    bearing_variance: float


class ActivePerceptionTrackingEnv:
    """Three-UAV bearing-only tracking with the repository's standard API."""

    num_agents = 3
    action_dim = 5
    horizon = 40
    world_radius = 12.0
    safety_radius = 0.8
    target_velocity = np.asarray((0.27, 0.16), dtype=np.float64)
    process_covariance = np.diag((0.10, 0.10))
    uav_types = (
        ActivePerceptionUAV(0.80, 10.0, 0.035),
        ActivePerceptionUAV(0.70, 9.0, 0.055),
        ActivePerceptionUAV(0.60, 8.0, 0.080),
    )

    def __init__(self, *, seed: int = 0):
        self._rng = np.random.default_rng(seed)
        self.reset()

    def reset(self) -> tuple[np.ndarray, np.ndarray, dict[str, np.ndarray]]:
        self.step_count = 0
        self.done = False
        self.uav_positions = np.asarray(((-6.0, 0.0), (-4.0, -3.5), (-4.0, 3.5)), dtype=np.float64)
        self._target_truth = np.asarray((0.0, 0.0), dtype=np.float64)
        self._target_velocity = self.target_velocity.copy()
        self.belief_mean = np.asarray((0.0, 0.0), dtype=np.float64)
        self.belief_covariance = np.diag((9.0, 9.0)).astype(np.float64)
        self.total_distance = 0.0
        self.near_collision_steps = 0
        self.measurement_count = 0
        self._error_history: list[float] = []
        return self.actor_observation(), self.critic_observation(), self.graph_observation()

    @staticmethod
    def _action_delta(action: int, speed: float) -> np.ndarray:
        directions = {
            HOLD: (0.0, 0.0), EAST: (1.0, 0.0), WEST: (-1.0, 0.0),
            NORTH: (0.0, 1.0), SOUTH: (0.0, -1.0),
        }
        return np.asarray(directions[int(action)], dtype=np.float64) * speed

    def _advance_target(self) -> None:
        self._target_truth = self._target_truth + self._target_velocity
        for axis in range(2):
            if abs(self._target_truth[axis]) > self.world_radius * 0.75:
                self._target_velocity[axis] *= -1.0
                self._target_truth[axis] = np.clip(self._target_truth[axis], -self.world_radius * 0.75, self.world_radius * 0.75)

    def _predict_belief(self) -> None:
        self.belief_mean = self.belief_mean + self._target_velocity
        self.belief_covariance = self.belief_covariance + self.process_covariance

    def _assimilate_bearings(self) -> int:
        used = 0
        for position, spec in zip(self.uav_positions, self.uav_types):
            delta_truth = self._target_truth - position
            if float(delta_truth @ delta_truth) > spec.sensing_range ** 2:
                continue
            delta_belief = self.belief_mean - position
            squared_range = float(delta_belief @ delta_belief)
            if squared_range <= 1e-10:
                continue
            expected = float(np.arctan2(delta_belief[1], delta_belief[0]))
            observed = float(np.arctan2(delta_truth[1], delta_truth[0]) + self._rng.normal(0.0, np.sqrt(spec.bearing_variance)))
            innovation = (observed - expected + np.pi) % (2.0 * np.pi) - np.pi
            h = np.asarray(((-delta_belief[1] / squared_range), (delta_belief[0] / squared_range)), dtype=np.float64)[None, :]
            innovation_variance = float(h @ self.belief_covariance @ h.T + spec.bearing_variance)
            gain = self.belief_covariance @ h.T / innovation_variance
            self.belief_mean = self.belief_mean + gain[:, 0] * innovation
            identity = np.eye(2)
            # Joseph form preserves positive semidefiniteness under finite precision.
            residual = identity - gain @ h
            self.belief_covariance = residual @ self.belief_covariance @ residual.T + gain * spec.bearing_variance @ gain.T
            used += 1
        return used

    def _safety_violation(self) -> bool:
        for first in range(self.num_agents):
            for second in range(first + 1, self.num_agents):
                if np.linalg.norm(self.uav_positions[first] - self.uav_positions[second]) < self.safety_radius:
                    return True
        return False

    def actor_observation(self) -> np.ndarray:
        covariance = self.belief_covariance / 9.0
        shared = np.asarray((
            self.belief_mean[0] / self.world_radius,
            self.belief_mean[1] / self.world_radius,
            covariance[0, 0], covariance[0, 1], covariance[1, 1],
            self.step_count / self.horizon,
        ), dtype=np.float32)
        rows = np.zeros((self.num_agents, 10), dtype=np.float32)
        for index, spec in enumerate(self.uav_types):
            rows[index, :6] = shared
            rows[index, 6:8] = self.uav_positions[index] / self.world_radius
            rows[index, 8] = spec.sensing_range / self.world_radius
            rows[index, 9] = spec.bearing_variance / 0.1
        return rows

    def critic_observation(self) -> np.ndarray:
        return np.concatenate((
            self.belief_mean / self.world_radius,
            (self.belief_covariance / 9.0).reshape(-1),
            (self.uav_positions / self.world_radius).reshape(-1),
            np.asarray((self.step_count / self.horizon,), dtype=np.float64),
        )).astype(np.float32)

    def graph_observation(self) -> dict[str, np.ndarray]:
        adjacency = np.ones((self.num_agents, self.num_agents), dtype=np.int8)
        np.fill_diagonal(adjacency, 0)
        return {
            "node_features": self.actor_observation(),
            "active_adj": adjacency,
            "roles": np.arange(self.num_agents, dtype=np.int64),
            "action_masks": np.ones((self.num_agents, self.action_dim), dtype=np.int8),
        }

    def step(self, actions: np.ndarray | list[int]) -> tuple[np.ndarray, np.ndarray, dict[str, np.ndarray], np.ndarray, np.ndarray, dict[str, Any]]:
        if self.done:
            raise RuntimeError("reset required after terminal episode")
        actions = np.asarray(actions, dtype=np.int64).reshape(self.num_agents)
        if np.any((actions < 0) | (actions >= self.action_dim)):
            raise ValueError("action outside active-perception interface")
        previous_logdet = log_determinant(self.belief_covariance)
        for index, (action, spec) in enumerate(zip(actions, self.uav_types)):
            delta = self._action_delta(int(action), spec.speed)
            candidate = np.clip(self.uav_positions[index] + delta, -self.world_radius, self.world_radius)
            self.total_distance += float(np.linalg.norm(candidate - self.uav_positions[index]))
            self.uav_positions[index] = candidate
        self._advance_target()
        self._predict_belief()
        # This is a public-belief geometric quantity computed after the joint
        # movement decision but before assimilating noisy measurements.  It is
        # logged for training-time credit assignment only; actor observations
        # remain unchanged.
        marginal_contributions = marginal_bearing_contributions(
            self.belief_covariance,
            self.belief_mean,
            self.uav_positions,
            [item.sensing_range for item in self.uav_types],
            [item.bearing_variance for item in self.uav_types],
        )
        measurements = self._assimilate_bearings()
        posterior_logdet = log_determinant(self.belief_covariance)
        unsafe = self._safety_violation()
        self.near_collision_steps += int(unsafe)
        self.measurement_count += measurements
        estimation_error = float(np.linalg.norm(self.belief_mean - self._target_truth))
        self._error_history.append(estimation_error)
        self.step_count += 1
        self.done = self.step_count >= self.horizon
        reward = previous_logdet - posterior_logdet - 0.01 * float(np.count_nonzero(actions != HOLD)) - 0.50 * float(unsafe)
        rewards = np.full((self.num_agents, 1), reward, dtype=np.float32)
        dones = np.full((self.num_agents, 1), self.done, dtype=np.float32)
        info = {
            "public_posterior_logdet": posterior_logdet,
            "measurement_count_step": measurements,
            "near_collision": float(unsafe),
            "target_truth_exposed_to_actor": False,
            "evaluation_estimation_error": estimation_error,
            "marginal_observability_contributions": marginal_contributions.astype(np.float32),
        }
        return self.actor_observation(), self.critic_observation(), self.graph_observation(), rewards, dones, info

    def terminal_summary(self) -> dict[str, float | int]:
        return {
            "mean_evaluation_estimation_error": float(np.mean(self._error_history)) if self._error_history else float("nan"),
            "final_public_posterior_logdet": log_determinant(self.belief_covariance),
            "total_distance": self.total_distance,
            "near_collision_steps": self.near_collision_steps,
            "measurement_count": self.measurement_count,
        }
