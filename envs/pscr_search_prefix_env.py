"""P8 search--localize--intercept task over the existing 3DOF UAV plant.

The environment exposes a public forecast sector and reliability before a
future request appears.  A Scout/Relay pair may reserve the forecast sector
while the Executor remains on current service.  After arrival, exact future
geometry is available only through the normal active-request observation; a
physical scout--relay--executor chain must localize it before future service
can accrue.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from envs.pscr_adversarial_service_env import PSCRConfig
from envs.pscr_role_commitment_env import PSCRRoleCommitmentEnv
from envs.pscr_service_reconfiguration_env import FORECAST_STAGE, FUTURE_SERVICE, PRIMARY_SERVICE


@dataclass(frozen=True)
class P8SearchPrefixConfig(PSCRConfig):
    """Frozen P8 task defaults; all positions use absolute world coordinates."""

    horizon: int = 160
    future_arrival_step: int = 84
    primary_deadline_step: int = 116
    future_deadline_urgent_step: int = 116
    future_deadline_routine_step: int = 150
    commitment_start_step: int = 36
    commitment_lock_steps: int = 48
    primary_position: tuple[float, float, float] = (10_000.0, -3_000.0, 5_000.0)
    forecast_x: float = 11_000.0
    forecast_y: float = 5_000.0
    future_x_offsets: tuple[float, ...] = (-750.0, 0.0, 750.0)
    localization_radius: float = 4_000.0


class PSCRSearchPrefixEnv(PSCRRoleCommitmentEnv):
    """Standard environment interface for the P8 physical task contract."""

    def __init__(self, config: P8SearchPrefixConfig | None = None):
        super().__init__(config or P8SearchPrefixConfig())

    @property
    def p8(self) -> P8SearchPrefixConfig:
        if not isinstance(self.config, P8SearchPrefixConfig):
            raise TypeError("PSCRSearchPrefixEnv requires P8SearchPrefixConfig")
        return self.config

    def reset(self):
        result = super().reset()
        cfg = self.p8
        self.primary_position = np.asarray(cfg.primary_position, dtype=np.float32)
        self._forecast_position = np.asarray((cfg.forecast_x, float(self.forecast_sector) * cfg.forecast_y, 5_000.0), dtype=np.float32)
        aligned = bool(self.rng.random() < self.public_forecast_reliability)
        actual_sector = self.forecast_sector if aligned else -self.forecast_sector
        x_offset = float(self.rng.choice(cfg.future_x_offsets))
        self.future_position = np.asarray((cfg.forecast_x + x_offset, float(actual_sector) * cfg.forecast_y, 5_000.0), dtype=np.float32)
        self.future_localized = False
        self.future_localization_step = -1
        self.search_prefix_ready_steps = 0
        return self.actor_observation(), self.critic_observation(), self.graph_observation()

    def _localization_chain_effective(self) -> bool:
        if not self.future_active:
            return False
        scout_ok = float(np.linalg.norm(self.base.blue_pos[self.scout] - self.future_position)) <= self.p8.localization_radius
        adjacency = self.base.comm_adj
        relay_ok = bool(adjacency[self.relay, self.scout] > 0.5 and adjacency[self.executor, self.relay] > 0.5)
        return bool(scout_ok and relay_ok)

    def _chain_effective(self, name: str) -> bool:
        if name == "future" and not self.future_localized:
            return False
        return super()._chain_effective(name)

    def actor_observation(self) -> np.ndarray:
        base = super().actor_observation()
        # These are public runtime facts: the commitment phase and the
        # localization event after request arrival.  Exact future geometry is
        # deliberately absent before arrival and becomes a normal public task
        # request only after activation.
        public = np.asarray(
            (
                float(self._commitment_active()),
                float(self.future_active),
                float(getattr(self, "future_localized", False)) if self.future_active else 0.0,
            ),
            dtype=np.float32,
        )
        return np.concatenate((base, np.repeat(public[None, :], self.num_agents, axis=0)), axis=1)

    def critic_observation(self) -> np.ndarray:
        base = super().critic_observation()
        return np.concatenate((base, np.asarray((float(getattr(self, "future_localized", False)) if self.future_active else 0.0,), dtype=np.float32)))

    def public_commitment_context(self) -> np.ndarray:
        """Return the common, pre-arrival information legal for a team plan.

        This deliberately excludes the sampled future position, realized
        sector and urgency before request activation.  It is included in the
        graph payload so a structured policy need not reconstruct common
        public facts from role-specific local observations.
        """
        return np.asarray(
            (
                self.public_forecast_reliability,
                float(self.forecast_sector),
                max(0, self.config.future_arrival_step - self.step_count) / self.config.horizon,
                float(self._commitment_active()),
                float(self._request_active("primary")),
            ),
            dtype=np.float32,
        )

    def graph_observation(self) -> dict[str, np.ndarray]:
        graph = super().graph_observation()
        graph["team_public_context"] = self.public_commitment_context()
        return graph

    def step(self, actions: np.ndarray | list[int]):
        if self.done:
            raise RuntimeError("reset required after a terminal P8 episode")
        requested = np.asarray(actions, dtype=np.int64).reshape(self.num_agents)
        requested = np.clip(requested, 0, self.action_dim - 1)
        if self._commitment_active():
            if self._committed_intents is None:
                self._committed_intents = requested.copy()
            intents = self._committed_intents
        else:
            intents = requested
        intents = np.where((intents == FUTURE_SERVICE) & (not self.future_active), FORECAST_STAGE, intents)
        primitive = np.asarray(
            [self._autopilot_action(agent, self._role_goal(agent, int(intent))) for agent, intent in enumerate(intents)],
            dtype=np.int64,
        )
        self._last_macro_actions = intents.copy()
        before_energy = self.base.blue_energy.copy()
        self.step_count += 1
        self.base.step_count = self.step_count
        self.base._move_blue(primitive)
        self.base._update_sensing_and_comm()
        if not self.future_active and self.step_count >= self.config.future_arrival_step:
            self.future_active = True
        if self.future_active and self._localization_chain_effective():
            self.future_localized = True
            if self.future_localization_step < 0:
                self.future_localization_step = self.step_count
        if not self.future_active and np.all(intents[[self.scout, self.relay]] == FORECAST_STAGE):
            self.search_prefix_ready_steps += 1

        quality = {"primary": self._service_quality("primary"), "future": self._service_quality("future") if self.future_localized else 0.0}
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
        all_resolved = self.step_count >= self.config.future_arrival_step and (self.primary_completed or self.primary_expired) and (self.future_completed or self.future_expired)
        self.done = bool(collision or constraint or timeout or all_resolved)
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
            "future_request_truth_exposed_before_arrival": False,
            "future_request_geometry_public_after_arrival": float(self.future_active),
            "future_localized": float(self.future_localized),
            "future_localization_step": self.future_localization_step,
            "search_prefix_ready_steps": self.search_prefix_ready_steps,
            "primary_service_quality": quality["primary"],
            "future_service_quality": quality["future"],
            "active_service_quality": active_quality,
            "energy_cost_step": energy_cost,
            "collision": float(collision),
            "constraint_violation": float(constraint),
            "reconfiguration_events": self.reconfiguration_events,
            "primary_completion_event": float(primary_complete),
            "future_completion_event": float(future_complete),
            "macro_interface": "p8_public_search_prefix_role_commitment_v1",
        }
        rewards = np.full((self.num_agents, 1), reward, dtype=np.float32)
        return self.actor_observation(), self.critic_observation(), self.graph_observation(), rewards, dones, info

    def terminal_summary(self) -> dict[str, float | int | str]:
        result = super().terminal_summary()
        result.update(
            {
                "future_localized": float(self.future_localized),
                "future_localization_step": self.future_localization_step,
                "search_prefix_ready_steps": self.search_prefix_ready_steps,
                "p8_interface": "public_search_prefix_role_commitment_v1",
            }
        )
        return result
