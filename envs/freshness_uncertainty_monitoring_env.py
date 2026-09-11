"""M1: dynamic multi-UAV active monitoring environment.

The environment is intentionally small and transparent before a learner is
connected.  UAVs monitor a latent, time-varying environmental field.  Actors
never observe that latent field: they receive only the shared posterior
uncertainty, information age, public urgency rate and their own position and
energy.  Ground truth is retained solely for evaluation diagnostics.

This is a benign monitoring task (for example, environmental anomaly or
infrastructure-condition surveillance), not a target-selection environment.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass(frozen=True)
class MonitoringScenario:
    """Frozen, publicly visible pressure band for the M1 task."""

    name: str
    initial_variance: tuple[float, float, float, float]
    urgency_rate: tuple[float, float, float, float]
    sensor_noise: tuple[float, float, float]


M1_SCENARIOS: tuple[MonitoringScenario, ...] = (
    MonitoringScenario(
        "uncertainty_dominant",
        initial_variance=(0.95, 0.20, 0.20, 0.20),
        urgency_rate=(0.04, 0.04, 0.04, 0.04),
        sensor_noise=(0.08, 0.14, 0.20),
    ),
    MonitoringScenario(
        "freshness_dominant",
        initial_variance=(0.30, 0.30, 0.30, 0.30),
        urgency_rate=(0.04, 0.04, 0.04, 0.25),
        sensor_noise=(0.08, 0.14, 0.20),
    ),
    MonitoringScenario(
        "conflict_band",
        initial_variance=(0.95, 0.20, 0.20, 0.20),
        urgency_rate=(0.04, 0.04, 0.04, 0.25),
        sensor_noise=(0.08, 0.14, 0.20),
    ),
)


class FreshnessUncertaintyMonitoringEnv:
    """Three-UAV, four-region active-monitoring task.

    Interface follows the repository convention:
    ``reset() -> obs, share_obs, graph_obs`` and
    ``step(actions) -> obs, share_obs, graph_obs, rewards, dones, infos``.

    Actions are ``0=hold`` and ``1..4=move toward / sense a region``.  A UAV
    needs one step to travel between neighbouring regions and senses only when
    it is already at the selected region.  This creates a real opportunity cost
    without adding a second hidden decision process.
    """

    num_agents = 3
    num_regions = 4
    action_dim = 5
    horizon = 24
    max_energy = 24.0
    # Square graph: 0--1
    #               |  |
    #               2--3
    _region_xy = np.asarray(((0.0, 0.0), (1.0, 0.0), (0.0, 1.0), (1.0, 1.0)), dtype=np.float32)

    def __init__(self, scenario: MonitoringScenario, *, seed: int = 0):
        self.scenario = scenario
        self._rng = np.random.default_rng(seed)
        self.reset()

    def reset(self) -> tuple[np.ndarray, np.ndarray, dict[str, np.ndarray]]:
        self.step_count = 0
        self.done = False
        self.positions = np.asarray((0, 1, 2), dtype=np.int64)
        self.energy = np.full(self.num_agents, self.max_energy, dtype=np.float32)
        self.posterior_mean = np.zeros(self.num_regions, dtype=np.float32)
        self.posterior_variance = np.asarray(self.scenario.initial_variance, dtype=np.float32).copy()
        self.age = np.zeros(self.num_regions, dtype=np.float32)
        # Latent state is deliberately not exposed by actor_observation().
        self._truth = self._rng.normal(0.0, 0.35, size=self.num_regions).astype(np.float32)
        self._sensed_counts = np.zeros(self.num_regions, dtype=np.int64)
        self._distance = 0.0
        self._duplicate_sensing = 0
        self._detection_delay: list[int] = []
        self._threshold_crossed_at = np.full(self.num_regions, -1, dtype=np.int64)
        self._detected_at = np.full(self.num_regions, -1, dtype=np.int64)
        self._advance_truth()  # deterministic model transition, not an observation
        return self.actor_observation(), self.critic_observation(), self.graph_observation()

    @staticmethod
    def _adjacent_or_same(source: int, destination: int) -> bool:
        return source == destination or int(bin(source ^ destination).count("1")) == 1

    def _advance_truth(self) -> None:
        """Evolve hidden field and record evaluation-only anomaly onset."""
        innovation = self._rng.normal(0.0, 0.10, size=self.num_regions).astype(np.float32)
        self._truth = (0.88 * self._truth + innovation).astype(np.float32)
        for region, value in enumerate(self._truth):
            if abs(float(value)) >= 0.45 and self._threshold_crossed_at[region] < 0:
                self._threshold_crossed_at[region] = self.step_count

    def actor_observation(self) -> np.ndarray:
        """Legal execution-time state; never contains ``self._truth``."""
        shared = np.concatenate((
            self.posterior_mean,
            self.posterior_variance,
            np.clip(self.age / self.horizon, 0.0, 1.0),
            np.asarray(self.scenario.urgency_rate, dtype=np.float32),
        )).astype(np.float32)
        rows = np.zeros((self.num_agents, shared.size + 6), dtype=np.float32)
        for agent in range(self.num_agents):
            rows[agent, : shared.size] = shared
            rows[agent, shared.size + int(self.positions[agent])] = 1.0
            rows[agent, -2] = self.energy[agent] / self.max_energy
            rows[agent, -1] = self.step_count / self.horizon
        return rows

    def critic_observation(self) -> np.ndarray:
        """Centralized state uses public belief and team resources, not truth."""
        return np.concatenate((
            self.posterior_mean,
            self.posterior_variance,
            self.age / self.horizon,
            np.asarray(self.scenario.urgency_rate, dtype=np.float32),
            self.positions.astype(np.float32) / (self.num_regions - 1),
            self.energy / self.max_energy,
            np.asarray((self.step_count / self.horizon,), dtype=np.float32),
        )).astype(np.float32)

    def graph_observation(self) -> dict[str, np.ndarray]:
        active = np.ones((self.num_agents, self.num_agents), dtype=np.int8)
        np.fill_diagonal(active, 0)
        masks = np.ones((self.num_agents, self.action_dim), dtype=np.int8)
        for agent, energy in enumerate(self.energy):
            if energy < 1.0:
                masks[agent, 1:] = 0
        return {
            "node_features": self.actor_observation(),
            "active_adj": active,
            "roles": np.asarray((0, 1, 2), dtype=np.int64),
            "action_masks": masks,
        }

    def _sense(self, agent: int, region: int) -> tuple[float, float]:
        """Return public belief gain and freshness-risk reduction."""
        prior_var = float(self.posterior_variance[region])
        prior_age = float(self.age[region])
        noise = float(self.scenario.sensor_noise[agent])
        measurement = float(self._truth[region] + self._rng.normal(0.0, noise))
        precision = 1.0 / max(prior_var, 1e-6) + 1.0 / max(noise * noise, 1e-6)
        posterior_var = 1.0 / precision
        gain = prior_var - posterior_var
        # Standard scalar Gaussian update; latent truth remains unobserved.
        kalman = prior_var / (prior_var + noise * noise)
        self.posterior_mean[region] += kalman * (measurement - self.posterior_mean[region])
        self.posterior_variance[region] = posterior_var
        self.age[region] = 0.0
        self._sensed_counts[region] += 1
        if self._detected_at[region] < 0 and abs(float(self.posterior_mean[region])) >= 0.45:
            self._detected_at[region] = self.step_count
            if self._threshold_crossed_at[region] >= 0:
                self._detection_delay.append(max(0, self.step_count - int(self._threshold_crossed_at[region])))
        freshness_gain = prior_age * float(self.scenario.urgency_rate[region])
        return gain, freshness_gain

    def step(self, actions: np.ndarray | list[int]) -> tuple[np.ndarray, np.ndarray, dict[str, np.ndarray], np.ndarray, np.ndarray, dict[str, Any]]:
        if self.done:
            raise RuntimeError("reset required after terminal episode")
        actions = np.asarray(actions, dtype=np.int64).reshape(self.num_agents)
        actions = np.clip(actions, 0, self.action_dim - 1)
        self.age += 1.0
        self.posterior_variance = np.minimum(1.0, self.posterior_variance + 0.025)
        information_gain = 0.0
        freshness_gain = 0.0
        sensed_this_step: list[int] = []

        for agent, action in enumerate(actions):
            if action == 0 or self.energy[agent] < 1.0:
                continue
            destination = int(action - 1)
            source = int(self.positions[agent])
            if not self._adjacent_or_same(source, destination):
                # A diagonal target requires an intermediate move; choose the
                # lowest-indexed adjacent waypoint deterministically.
                candidates = [r for r in range(self.num_regions) if self._adjacent_or_same(source, r) and self._adjacent_or_same(r, destination)]
                destination = min(candidates)
            if destination != source:
                self._distance += float(np.linalg.norm(self._region_xy[source] - self._region_xy[destination]))
                self.positions[agent] = destination
                self.energy[agent] -= 1.0
            else:
                gain, fresh = self._sense(agent, destination)
                information_gain += gain
                freshness_gain += fresh
                sensed_this_step.append(destination)
                self.energy[agent] -= 0.35

        self._duplicate_sensing += len(sensed_this_step) - len(set(sensed_this_step))
        duplicate_this_step = len(sensed_this_step) - len(set(sensed_this_step))
        error_before = float(np.mean((self.posterior_mean - self._truth) ** 2))
        self._advance_truth()
        error_after = float(np.mean((self.posterior_mean - self._truth) ** 2))
        self.step_count += 1
        self.done = self.step_count >= self.horizon or bool(np.all(self.energy < 0.35))
        # Reward uses the same public belief components available to every arm.
        # Ground-truth error is logged for evaluation only and is not rewarded.
        # Monitoring is a team objective: repeatedly measuring one already
        # covered region must not dominate a policy that maintains useful
        # information over the whole field.  Both terms below are public
        # belief-state quantities and are therefore identical for every arm.
        global_staleness_risk = float(np.sum(self.age * np.asarray(self.scenario.urgency_rate, dtype=np.float32)))
        reward = (
            information_gain
            + freshness_gain
            - 0.02 * self._distance / max(1, self.step_count)
            - 0.10 * global_staleness_risk
            - 0.15 * float(duplicate_this_step)
        )
        rewards = np.full((self.num_agents, 1), reward, dtype=np.float32)
        dones = np.full((self.num_agents, 1), self.done, dtype=np.float32)
        info = {
            "information_gain": information_gain,
            "freshness_gain": freshness_gain,
            "evaluation_mse_before": error_before,
            "evaluation_mse_after": error_after,
            "max_information_age": float(np.max(self.age)),
            "duplicate_sensing": int(self._duplicate_sensing),
            "duplicate_sensing_this_step": int(duplicate_this_step),
            "global_staleness_risk": global_staleness_risk,
            "distance": float(self._distance),
            "truth_exposed_to_actor": False,
        }
        return self.actor_observation(), self.critic_observation(), self.graph_observation(), rewards, dones, info

    def terminal_summary(self) -> dict[str, Any]:
        undetected = int(np.sum((self._threshold_crossed_at >= 0) & (self._detected_at < 0)))
        return {
            "scenario": self.scenario.name,
            "evaluation_mse": float(np.mean((self.posterior_mean - self._truth) ** 2)),
            "max_information_age": float(np.max(self.age)),
            "mean_detection_delay": float(np.mean(self._detection_delay)) if self._detection_delay else None,
            "missed_events": undetected,
            "duplicate_sensing": int(self._duplicate_sensing),
            "distance": float(self._distance),
            "sensed_counts": self._sensed_counts.tolist(),
        }
