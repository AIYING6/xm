"""P10 capacity-coupled persistent and deadline service environment.

The unchanged 3DOF plant, energy model and communication graph serve two
physically exclusive service demands.  The primary demand is persistent: its
unserved workload accumulates whenever the team cannot form its service chain.
The future demand is a publicly announced high-priority job with an uncertain
location and a fixed public deadline.  No plan label changes reward; workload
changes only through the corresponding physical chain.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from envs.pscr_full_team_commitment_env import PSCRFullTeamCommitmentEnv
from envs.pscr_search_prefix_env import P8SearchPrefixConfig


@dataclass(frozen=True)
class P10CapacityCoupledConfig(P8SearchPrefixConfig):
    """Public task-workload contract; defaults are subject to a G0 audit."""

    future_deadline_step: int = 100
    primary_backlog_growth: float = 0.030
    primary_service_rate: float = 0.060
    primary_backlog_loss_weight: float = 0.020
    future_workload: float = 1.0
    future_service_rate: float = 0.100
    future_priority_value: float = 3.0


class PSCRCapacityCoupledServiceEnv(PSCRFullTeamCommitmentEnv):
    """Standard P10 interface with workload driven only by physical service."""

    def __init__(self, config: P10CapacityCoupledConfig | None = None):
        super().__init__(config or P10CapacityCoupledConfig())

    @property
    def p10(self) -> P10CapacityCoupledConfig:
        if not isinstance(self.config, P10CapacityCoupledConfig):
            raise TypeError("PSCRCapacityCoupledServiceEnv requires P10CapacityCoupledConfig")
        return self.config

    def reset(self):
        result = super().reset()
        self.primary_backlog = 0.0
        self.primary_backlog_area = 0.0
        self.future_work_remaining = float(self.p10.future_workload)
        self.future_service_steps = 0
        return result

    def _deadline(self, name: str) -> int:
        return self.p10.future_deadline_step if name == "future" else self.config.horizon

    def _request_active(self, name: str) -> bool:
        if name == "primary":
            return True
        return self.future_active and not self.future_completed and not self.future_expired

    def _update_workloads(self, primary_effective: bool, future_effective: bool) -> tuple[float, float, bool]:
        cfg = self.p10
        before_primary = self.primary_backlog
        self.primary_backlog = max(0.0, self.primary_backlog + cfg.primary_backlog_growth - cfg.primary_service_rate * float(primary_effective))
        self.primary_backlog_area += self.primary_backlog
        future_progress = 0.0
        completed = False
        if self.future_active and not self.future_completed and not self.future_expired:
            if self.step_count > cfg.future_deadline_step:
                self.future_expired = True
            elif future_effective:
                future_progress = min(cfg.future_service_rate, self.future_work_remaining)
                self.future_work_remaining -= future_progress
                self.future_service_steps += 1
                if self.future_work_remaining <= 1e-9:
                    self.future_work_remaining = 0.0
                    self.future_completed = True
                    completed = True
        primary_cost_increment = cfg.primary_backlog_loss_weight * self.primary_backlog
        # Dense service-progress is physical accounting, not a plan-specific shaping term.
        reward = -primary_cost_increment + cfg.future_priority_value * future_progress
        return reward, before_primary, completed

    def step(self, actions: np.ndarray | list[int]):
        if self.done:
            raise RuntimeError("reset required after a terminal P10 episode")
        requested = np.asarray(actions, dtype=np.int64).reshape(self.num_agents)
        requested = np.clip(requested, 0, self.action_dim - 1)
        if self._commitment_active():
            if self._committed_intents is None:
                self._committed_intents = requested.copy()
            intents = self._committed_intents
        else:
            intents = requested
        # Before the public request appears, future-service is an ordinary
        # forecast-stage request; no future truth is exposed to this mapping.
        from envs.pscr_service_reconfiguration_env import FORECAST_STAGE, FUTURE_SERVICE
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
        if not self.future_active and np.all(intents == FORECAST_STAGE):
            self.search_prefix_ready_steps += 1

        primary_effective = self._chain_effective("primary")
        future_effective = self._chain_effective("future")
        workload_reward, _, future_completed_now = self._update_workloads(primary_effective, future_effective)
        collision = self.base._has_collision()
        constraint = self.base._has_constraint_violation()
        energy_cost = float(np.maximum(0.0, before_energy - self.base.blue_energy).sum())
        timeout = self.step_count >= self.config.horizon
        self.done = bool(collision or constraint or timeout)
        reward = workload_reward - 0.025 * energy_cost - 0.8 * float(collision or constraint)
        dones = np.full((self.num_agents, 1), self.done, dtype=np.float32)
        info: dict[str, Any] = {
            "primary_chain_effective": float(primary_effective),
            "future_chain_effective": float(future_effective),
            "future_request_active": float(self.future_active),
            "future_request_truth_exposed_before_arrival": False,
            "future_request_geometry_public_after_arrival": float(self.future_active),
            "future_localized": float(self.future_localized),
            "future_completed": float(self.future_completed),
            "future_expired": float(self.future_expired),
            "primary_backlog": self.primary_backlog,
            "primary_backlog_area": self.primary_backlog_area,
            "future_work_remaining": self.future_work_remaining,
            "future_completion_event": float(future_completed_now),
            "energy_cost_step": energy_cost,
            "collision": float(collision),
            "constraint_violation": float(constraint),
            "macro_interface": "p10_capacity_coupled_service_v1",
        }
        rewards = np.full((self.num_agents, 1), reward, dtype=np.float32)
        return self.actor_observation(), self.critic_observation(), self.graph_observation(), rewards, dones, info

    def terminal_summary(self) -> dict[str, float | int | str]:
        return {
            "primary_backlog_final": self.primary_backlog,
            "primary_backlog_area": self.primary_backlog_area,
            "future_completed": float(self.future_completed),
            "future_expired": float(self.future_expired),
            "future_localized": float(self.future_localized),
            "future_work_remaining": self.future_work_remaining,
            "future_service_steps": self.future_service_steps,
            "mission_utility": self.p10.future_priority_value * float(self.future_completed) - self.p10.primary_backlog_loss_weight * self.primary_backlog_area,
            "energy_used": float(np.maximum(0.0, self._energy_at_reset - self.base.blue_energy).sum()),
            "task_contract": "p10_capacity_coupled_service_v1",
        }


__all__ = ("P10CapacityCoupledConfig", "PSCRCapacityCoupledServiceEnv")
