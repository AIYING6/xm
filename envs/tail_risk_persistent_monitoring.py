"""Deterministic zero-training audit model for tail-risk persistent monitoring."""
from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Iterable

import numpy as np


REGIONS = np.asarray(((-2.0, -2.0), (2.0, -2.0), (-2.0, 2.0), (2.0, 2.0)), dtype=np.float64)
DEPOT = np.asarray((0.0, 0.0), dtype=np.float64)
SPEED = np.asarray((1.15, 0.90, 0.75), dtype=np.float64)
SENSE = np.asarray((0.58, 0.72, 0.88), dtype=np.float64)
ENERGY_MAX = np.asarray((11.0, 10.0, 12.0), dtype=np.float64)
THRESHOLD = np.asarray((5.0, 9.0, 9.0, 9.0), dtype=np.float64)


@dataclass
class MonitoringState:
    positions: np.ndarray
    energy: np.ndarray
    age: np.ndarray
    step: int
    reward: float = 0.0
    critical_failure_steps: int = 0

    def clone(self) -> "MonitoringState":
        return MonitoringState(self.positions.copy(), self.energy.copy(), self.age.copy(), self.step, self.reward, self.critical_failure_steps)


class TailRiskPersistentMonitoringAudit:
    """A compact, deterministic mission model used only for Q0 rule/oracle checks."""

    action_count = 5  # four regions plus depot

    def __init__(self, criticality: np.ndarray, horizon: int = 24) -> None:
        if criticality.shape != (horizon, 4):
            raise ValueError("criticality must be [horizon, four regions]")
        self.criticality, self.horizon = criticality, horizon

    def initial_state(self) -> MonitoringState:
        return MonitoringState(
            positions=np.asarray(((-1.7, -1.6), (1.7, -1.6), (0.0, 1.7)), dtype=np.float64),
            energy=ENERGY_MAX.copy(), age=np.asarray((2.0, 2.0, 2.0, 2.0)), step=0,
        )

    def _goal(self, action: int) -> np.ndarray:
        return DEPOT if action == 4 else REGIONS[action]

    def step(self, state: MonitoringState, actions: Iterable[int]) -> MonitoringState:
        actions = tuple(int(action) for action in actions)
        if len(actions) != 3 or any(action < 0 or action >= self.action_count for action in actions):
            raise ValueError("invalid joint action")
        next_state = state.clone()
        weights = self.criticality[state.step]
        age_before = state.age.copy()
        move_cost = 0.0
        for agent, action in enumerate(actions):
            goal = self._goal(action)
            delta = goal - next_state.positions[agent]
            distance = float(np.linalg.norm(delta))
            travel = min(distance, float(SPEED[agent]), float(next_state.energy[agent]))
            if distance > 1e-9:
                next_state.positions[agent] += delta * travel / distance
            next_state.energy[agent] -= travel
            move_cost += 0.08 * travel
            if action == 4 and float(np.linalg.norm(next_state.positions[agent] - DEPOT)) <= 0.72:
                next_state.energy[agent] = ENERGY_MAX[agent]
        next_state.age += 1.0
        for region in range(4):
            covered = any(float(np.linalg.norm(next_state.positions[agent] - REGIONS[region])) <= SENSE[agent] for agent in range(3))
            if covered:
                next_state.age[region] = 0.0
        service_gain = float(np.sum(weights * (age_before + 1.0 - next_state.age)))
        critical_breach = bool(next_state.age[0] > THRESHOLD[0])
        next_state.critical_failure_steps += int(critical_breach)
        next_state.reward += service_gain - move_cost - 1.6 * float(critical_breach)
        next_state.step += 1
        return next_state

    def action_for_rule(self, state: MonitoringState, rule: str) -> tuple[int, int, int]:
        weights = self.criticality[state.step]
        actions: list[int] = []
        for agent in range(3):
            distance = np.linalg.norm(REGIONS - state.positions[agent], axis=1)
            if state.energy[agent] < 2.2:
                actions.append(4); continue
            if rule == "age":
                score = weights * state.age / np.maximum(distance, 0.25)
            elif rule == "tail":
                score = weights * (state.age / THRESHOLD) ** 2 / np.maximum(distance, 0.25)
            elif rule == "reserve":
                score = weights * (state.age / THRESHOLD) ** 1.35 / np.maximum(distance, 0.25)
                if state.energy[agent] < 3.8:
                    actions.append(4); continue
            else:
                raise ValueError(rule)
            actions.append(int(np.argmax(score)))
        return tuple(actions)  # type: ignore[return-value]

    def rollout_rule(self, rule: str) -> MonitoringState:
        state = self.initial_state()
        while state.step < self.horizon:
            state = self.step(state, self.action_for_rule(state, rule))
        return state

    def rollout_beam_oracle(self, width: int = 72) -> MonitoringState:
        beam = [self.initial_state()]
        actions = tuple(product(range(self.action_count), repeat=3))
        for _ in range(self.horizon):
            candidates = [self.step(state, joint) for state in beam for joint in actions]
            candidates.sort(key=lambda state: state.reward, reverse=True)
            beam = candidates[:width]
        return max(beam, key=lambda state: state.reward)
