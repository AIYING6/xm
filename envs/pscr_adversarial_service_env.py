"""3DOF predictive service-chain reconfiguration environment.

This environment reuses the repository's heterogeneous flight dynamics,
energy accounting, collision checks and range-limited communication graph.  A
request earns service only when the scout, relay and executor simultaneously
form a physical service chain.  A future request is announced through a public
but imperfect forecast and arrives later under a bounded adversarial profile.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from envs.uav_intercept_3d_env import ACTION3D_TABLE, UAVIntercept3DConfig, UAVIntercept3DEnv


@dataclass(frozen=True)
class PSCRConfig:
    horizon: int = 220
    future_arrival_step: int = 58
    primary_deadline_step: int = 142
    future_deadline_urgent_step: int = 154
    future_deadline_routine_step: int = 202
    chain_hold_steps: int = 5
    forecast_reliability: float = 0.75
    # Optional public reliability band sampled independently at each reset.
    # Empty preserves the single-reliability protocols used before P4.
    forecast_reliability_choices: tuple[float, ...] = ()
    geometry_scale: float = 1.0
    service_quality_reward_weight: float = 0.01
    # Public task geometry. Defaults preserve the completed PSCR P1--P3
    # interface exactly; P4 calibration may vary these only in a new root.
    primary_forward_distance: float = 8_500.0
    future_forward_distance: float = 11_000.0
    future_lateral_distance: float = 11_000.0
    contingency_forward_distance: float = 10_000.0
    adversary_profile: str = "bounded_mixture"  # bounded_mixture | urgent_opposite | routine_aligned
    seed: int = 0


class PredictiveServiceChainReconfigurationEnv:
    """Three-role UAV service task with no unrevealed-request actor leakage."""

    num_agents = 3
    action_dim = len(ACTION3D_TABLE)
    scout, relay, executor = 0, 1, 2
    # Public, task-level interaction radii.  The relay requirement is still
    # constrained by the underlying physical communication graph/ranges.
    sensing_radius = 9_000.0
    execution_radius = 4_800.0

    def __init__(self, config: PSCRConfig | None = None):
        self.config = config or PSCRConfig()
        if self.config.adversary_profile not in {"bounded_mixture", "urgent_opposite", "routine_aligned"}:
            raise ValueError("unsupported adversary profile")
        if not 0.25 <= self.config.geometry_scale <= 1.0:
            raise ValueError("geometry_scale must lie in [0.25, 1.0]")
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

    def _sample_future_profile(self, forecast_sector: int) -> tuple[int, bool]:
        """Return (sector sign, urgent) within the frozen adversary budget."""
        if self.config.adversary_profile == "urgent_opposite":
            return -forecast_sector, True
        if self.config.adversary_profile == "routine_aligned":
            return forecast_sector, False
        aligned = self.rng.random() < self.public_forecast_reliability
        urgent = bool(self.rng.random() < 0.55)
        return (forecast_sector if aligned else -forecast_sector), urgent

    def reset(self) -> tuple[np.ndarray, np.ndarray, dict[str, np.ndarray]]:
        self.base.seed(int(self.rng.integers(0, 2**31 - 1)))
        self.base.reset()
        self.step_count = 0
        self.done = False
        centroid = self.base.blue_pos.mean(axis=0)
        canonical_primary = np.asarray((self.config.primary_forward_distance, 0.0, 5_000.0), dtype=np.float32)
        self.primary_position = centroid + self.config.geometry_scale * (canonical_primary - centroid)
        choices = self.config.forecast_reliability_choices
        self.public_forecast_reliability = float(self.rng.choice(choices)) if choices else self.config.forecast_reliability
        self.forecast_sector = 1 if self.rng.random() < 0.5 else -1
        actual_sector, self.future_urgent = self._sample_future_profile(self.forecast_sector)
        # A request remains inside the announced sector but its exact geometry
        # is unavailable until arrival.
        canonical_future = np.asarray(
            (self.config.future_forward_distance + float(self.rng.uniform(-1_000.0, 1_000.0)), actual_sector * self.config.future_lateral_distance, 5_000.0),
            dtype=np.float32,
        )
        self.future_position = centroid + self.config.geometry_scale * (canonical_future - centroid)
        self.future_active = False
        self.primary_completed = False
        self.future_completed = False
        self.primary_expired = False
        self.future_expired = False
        self.primary_hold = 0
        self.future_hold = 0
        self.reconfiguration_events = 0
        self._last_service_target = "none"
        self._energy_at_reset = self.base.blue_energy.copy()
        self._chain_steps = {"primary": 0, "future": 0}
        return self.actor_observation(), self.critic_observation(), self.graph_observation()

    def _request_active(self, name: str) -> bool:
        if name == "primary":
            return not self.primary_completed and not self.primary_expired
        return self.future_active and not self.future_completed and not self.future_expired

    def _deadline(self, name: str) -> int:
        if name == "primary":
            return self.config.primary_deadline_step
        return self.config.future_deadline_urgent_step if self.future_urgent else self.config.future_deadline_routine_step

    def _position(self, name: str) -> np.ndarray:
        return self.primary_position if name == "primary" else self.future_position

    def _chain_effective(self, name: str) -> bool:
        if not self._request_active(name):
            return False
        target = self._position(name)
        scout_ok = float(np.linalg.norm(self.base.blue_pos[self.scout] - target)) <= self.sensing_radius
        executor_ok = float(np.linalg.norm(self.base.blue_pos[self.executor] - target)) <= self.execution_radius
        # The relay must be in active two-hop physical communication with the
        # scout and executor. comm_adj[receiver, sender] follows the base env.
        adjacency = self.base.comm_adj
        relay_ok = bool(adjacency[self.relay, self.scout] > 0.5 and adjacency[self.executor, self.relay] > 0.5)
        return bool(scout_ok and executor_ok and relay_ok)

    def _service_quality(self, name: str) -> float:
        """Continuous, observable quality of a physical service chain.

        This is task quality, not an oracle label: it is derived solely from
        physical distance and the currently active communication graph.  The
        completion event still requires the stricter simultaneous chain in
        :meth:`_chain_effective`.
        """
        if not self._request_active(name):
            return 0.0
        target = self._position(name)
        scout_distance = float(np.linalg.norm(self.base.blue_pos[self.scout] - target))
        executor_distance = float(np.linalg.norm(self.base.blue_pos[self.executor] - target))
        scout_quality = max(0.0, 1.0 - scout_distance / self.sensing_radius)
        executor_quality = max(0.0, 1.0 - executor_distance / self.execution_radius)
        # A binary link flag is retained for the completion condition, but is
        # too discontinuous to express whether the relay is moving toward a
        # viable two-hop service chain.  The shaping term below is computed
        # only from physical separations and the same communication ranges.
        types = self.base.config.blue_types
        scale = self.base.config.communication_range_scale
        scout_range = scale * min(types[self.relay].comm_range, types[self.scout].comm_range)
        executor_range = scale * min(types[self.relay].comm_range, types[self.executor].comm_range)
        relay_scout = max(0.0, 1.0 - float(np.linalg.norm(self.base.blue_pos[self.relay] - self.base.blue_pos[self.scout])) / scout_range)
        relay_executor = max(0.0, 1.0 - float(np.linalg.norm(self.base.blue_pos[self.relay] - self.base.blue_pos[self.executor])) / executor_range)
        relay_quality = relay_scout * relay_executor
        return float(0.40 * scout_quality + 0.50 * executor_quality + 0.10 * relay_quality)

    def _update_service(self, name: str) -> tuple[float, bool]:
        if not self._request_active(name):
            return 0.0, False
        if self.step_count > self._deadline(name):
            if name == "primary":
                self.primary_expired = True
            else:
                self.future_expired = True
            return 0.0, False
        effective = self._chain_effective(name)
        hold_name = f"{name}_hold"
        setattr(self, hold_name, getattr(self, hold_name) + 1 if effective else 0)
        if effective:
            self._chain_steps[name] += 1
        if getattr(self, hold_name) < self.config.chain_hold_steps:
            return 0.012 if effective else 0.0, False
        if name == "primary":
            self.primary_completed = True
            return 1.0, True
        self.future_completed = True
        return (1.35 if self.future_urgent else 1.10), True

    def _public_request_vector(self, agent: int) -> np.ndarray:
        pos = self.base.blue_pos[agent]
        primary_rel = (self.primary_position - pos) / self.base.config.world_radius
        future_rel = ((self.future_position - pos) / self.base.config.world_radius) if self.future_active else np.zeros(3, dtype=np.float32)
        return np.asarray(
            [
                float(self._request_active("primary")), float(self.primary_completed),
                *primary_rel.tolist(),
                self.public_forecast_reliability, float(self.forecast_sector),
                max(0, self.config.future_arrival_step - self.step_count) / self.config.horizon,
                float(self.future_active), float(self.future_urgent) if self.future_active else 0.0,
                *future_rel.tolist(),
            ],
            dtype=np.float32,
        )

    def actor_observation(self) -> np.ndarray:
        rows = []
        for agent in range(self.num_agents):
            role = np.zeros(3, dtype=np.float32)
            role[agent] = 1.0
            inbound = float(np.sum(self.base.comm_adj[agent]) - 1.0) / 2.0
            # Turn and climb commands act on heading and flight-path angle.
            # These are each vehicle's own physical states, not hidden task
            # truth.  Omitting them makes the same visible position require
            # different actions depending on an unobserved orientation.
            attitude = np.asarray(
                (
                    np.sin(self.base.blue_heading[agent]),
                    np.cos(self.base.blue_heading[agent]),
                    np.sin(self.base.blue_gamma[agent]),
                    np.cos(self.base.blue_gamma[agent]),
                ),
                dtype=np.float32,
            )
            row = np.concatenate(
                (
                    self.base.blue_pos[agent] / self.base.config.world_radius,
                    np.asarray((self.base.blue_speed[agent] / 300.0, self.base.blue_energy[agent], inbound, self.step_count / self.config.horizon), dtype=np.float32),
                    attitude,
                    role,
                    self._public_request_vector(agent),
                )
            )
            rows.append(row.astype(np.float32))
        return np.stack(rows)

    def critic_observation(self) -> np.ndarray:
        # The centralized critic receives only the same public future-request
        # fields as the actors. It never receives the unrevealed exact position
        # or actual urgency before arrival.
        public = self._public_request_vector(0)
        return np.concatenate(
            (
                self.base.blue_pos.reshape(-1) / self.base.config.world_radius,
                self.base.blue_energy,
                np.column_stack(
                    (
                        np.sin(self.base.blue_heading),
                        np.cos(self.base.blue_heading),
                        np.sin(self.base.blue_gamma),
                        np.cos(self.base.blue_gamma),
                    )
                ).reshape(-1),
                self.base.comm_adj.reshape(-1),
                public,
                np.asarray((self.step_count / self.config.horizon,), dtype=np.float32),
            )
        ).astype(np.float32)

    def graph_observation(self) -> dict[str, np.ndarray]:
        return {
            "node_features": self.actor_observation(),
            "active_adj": self.base.comm_adj.astype(np.int8),
            "roles": np.asarray((self.scout, self.relay, self.executor), dtype=np.int64),
            "action_masks": np.ones((self.num_agents, self.action_dim), dtype=np.int8),
        }

    def step(self, actions: np.ndarray | list[int]):
        if self.done:
            raise RuntimeError("reset required after a terminal SQR episode")
        actions = np.asarray(actions, dtype=np.int64).reshape(self.num_agents)
        # ``self.action_dim`` may be replaced by a high-level wrapper.  This
        # base environment always executes the original 3DOF primitive table.
        actions = np.clip(actions, 0, len(ACTION3D_TABLE) - 1)
        before_energy = self.base.blue_energy.copy()
        self.step_count += 1
        self.base.step_count = self.step_count
        self.base._move_blue(actions)
        self.base._update_sensing_and_comm()
        if not self.future_active and self.step_count >= self.config.future_arrival_step:
            self.future_active = True
        quality = {"primary": self._service_quality("primary"), "future": self._service_quality("future")}
        active_quality = sum(quality.values())
        primary_reward, primary_complete = self._update_service("primary")
        future_reward, future_complete = self._update_service("future")
        active_target = "future" if self._chain_effective("future") else ("primary" if self._chain_effective("primary") else "none")
        if self._last_service_target not in {"none", active_target} and active_target != "none":
            self.reconfiguration_events += 1
        self._last_service_target = active_target
        collision = self.base._has_collision()
        constraint = self.base._has_constraint_violation()
        energy_cost = float(np.maximum(0.0, before_energy - self.base.blue_energy).sum())
        timeout = self.step_count >= self.config.horizon
        # Completing the primary request early is not terminal: the public
        # forecast refers to a scheduled future request that must still be
        # allowed to arrive.  Ending here would erase the reconfiguration
        # decision that defines PSCR.
        all_resolved = (
            self.step_count >= self.config.future_arrival_step
            and (self.primary_completed or self.primary_expired)
            and (self.future_completed or self.future_expired)
        )
        self.done = bool(collision or constraint or timeout or all_resolved)
        # The task utility is a persistent, physically measurable service
        # quality, rather than only its one-step difference.  Completion still
        # requires the stricter simultaneous chain and hold-time condition.
        reward = primary_reward + future_reward + self.config.service_quality_reward_weight * active_quality - 0.025 * energy_cost - 0.8 * float(collision or constraint)
        dones = np.full((self.num_agents, 1), self.done, dtype=np.float32)
        info: dict[str, Any] = {
            "primary_chain_effective": float(self._chain_effective("primary")),
            "future_chain_effective": float(self._chain_effective("future")),
            "primary_completed": float(self.primary_completed),
            "future_completed": float(self.future_completed),
            "primary_expired": float(self.primary_expired),
            "future_expired": float(self.future_expired),
            "future_request_active": float(self.future_active),
            "future_request_truth_exposed_to_actor": False,
            "primary_service_quality": quality["primary"],
            "future_service_quality": quality["future"],
            "active_service_quality": active_quality,
            "energy_cost_step": energy_cost,
            "collision": float(collision),
            "constraint_violation": float(constraint),
            "reconfiguration_events": self.reconfiguration_events,
            "primary_completion_event": float(primary_complete),
            "future_completion_event": float(future_complete),
        }
        rewards = np.full((self.num_agents, 1), reward, dtype=np.float32)
        return self.actor_observation(), self.critic_observation(), self.graph_observation(), rewards, dones, info

    def terminal_summary(self) -> dict[str, float | int | str]:
        return {
            "primary_completed": float(self.primary_completed),
            "future_completed": float(self.future_completed),
            "primary_expired": float(self.primary_expired),
            "future_expired": float(self.future_expired),
            "weighted_service_value": float(self.primary_completed) + (1.35 if self.future_urgent else 1.10) * float(self.future_completed),
            "service_chain_steps_primary": self._chain_steps["primary"],
            "service_chain_steps_future": self._chain_steps["future"],
            "reconfiguration_events": self.reconfiguration_events,
            "energy_used": float(np.maximum(0.0, self._energy_at_reset - self.base.blue_energy).sum()),
            "adversary_profile": self.config.adversary_profile,
        }
