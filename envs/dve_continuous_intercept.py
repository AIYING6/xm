"""Continuous kinematic audit model for stale multi-UAV maneuver validity."""

from __future__ import annotations

from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class InterceptCase:
    latency: float
    agent_positions: np.ndarray
    target_position: np.ndarray
    target_velocity: np.ndarray
    target_maneuver: np.ndarray


def unit(vector: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(vector, axis=-1, keepdims=True)
    return vector / np.maximum(norm, 1e-8)


class ContinuousInterceptAudit:
    speed = 1.5
    horizon = 2.5
    dt = 0.05
    collision_radius = 0.35

    def __init__(self, case: InterceptCase) -> None:
        self.case = case
        self.snapshot_target = case.target_position.copy()
        self.stale_actions = self.speed * unit(
            self.snapshot_target[None, :] - case.agent_positions
        )
        self.completion_agents = case.agent_positions + self.stale_actions * case.latency
        self.completion_target = (
            case.target_position
            + case.target_velocity * case.latency
            + case.target_maneuver * case.latency**2
        )

    def fallback_actions(self) -> np.ndarray:
        offsets = np.asarray([[0.0, -0.8], [0.0, 0.8]])
        goals = self.completion_target[None, :] + offsets
        return self.speed * unit(goals - self.completion_agents)

    def rollout(self, actions: np.ndarray) -> dict:
        agents = self.completion_agents.copy()
        target = self.completion_target.copy()
        min_separation = float(np.linalg.norm(agents[0] - agents[1]))
        steps = int(self.horizon / self.dt)
        for _ in range(steps):
            agents += actions * self.dt
            target += (self.case.target_velocity + 2.0 * self.case.target_maneuver * self.case.latency) * self.dt
            min_separation = min(min_separation, float(np.linalg.norm(agents[0] - agents[1])))
        mean_distance = float(np.linalg.norm(agents - target[None, :], axis=1).mean())
        safe = min_separation >= self.collision_radius
        value = -mean_distance - (8.0 if not safe else 0.0)
        return {
            "value": value,
            "mean_distance": mean_distance,
            "min_separation": min_separation,
            "safe": safe,
        }

    def evaluate(self) -> dict:
        fallback = self.fallback_actions()
        both_stale = self.rollout(self.stale_actions)
        both_fallback = self.rollout(fallback)
        first_stale = self.rollout(np.stack([self.stale_actions[0], fallback[1]]))
        second_stale = self.rollout(np.stack([fallback[0], self.stale_actions[1]]))
        stale_task_valid = (
            both_stale["safe"]
            and both_stale["value"] >= both_fallback["value"] - 0.25
        )
        individually_safe_jointly_unsafe = (
            first_stale["safe"] and second_stale["safe"] and not both_stale["safe"]
        )
        return {
            "both_stale": both_stale,
            "both_fallback": both_fallback,
            "first_stale": first_stale,
            "second_stale": second_stale,
            "stale_task_valid": stale_task_valid,
            "individually_safe_jointly_unsafe": individually_safe_jointly_unsafe,
        }
