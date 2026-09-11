"""Opt-in non-adversarial environment for P39 pre-training qualification.

The environment models persistent observation of two moving civilian monitoring
events by a heterogeneous UAV team.  It is intentionally small: its only
purpose is to test whether asynchronous sensing plus reassignment costs create
a non-degenerate decision problem before any learning method is attached.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Tuple

import numpy as np


@dataclass(frozen=True)
class TrackingUAVType:
    speed: float
    sensing_range: float
    update_period: int


@dataclass
class AsyncRoleTrackingConfig:
    num_uavs: int = 3
    num_events: int = 2
    world_size: float = 20.0
    dt: float = 1.0
    max_steps: int = 40
    event_speed: float = 0.32
    cache_valid_steps: int = 3
    reassignment_blackout_steps: int = 1
    seed: int | None = None
    uav_types: Tuple[TrackingUAVType, ...] = field(
        default_factory=lambda: (
            TrackingUAVType(speed=0.55, sensing_range=6.0, update_period=1),
            TrackingUAVType(speed=0.85, sensing_range=4.0, update_period=2),
            TrackingUAVType(speed=0.75, sensing_range=4.5, update_period=3),
        )
    )


class AsyncRoleTrackingEnv:
    """Heterogeneous persistent-monitoring environment with standard interface.

    Actions are ``0=idle, 1=monitor event 0, 2=monitor event 1``.  Reassigning
    a UAV causes one sensing blackout step.  An event is covered while at
    least one UAV holds a fresh local estimate.  Thus reassignment changes
    future coverage by delaying the next refresh before a cache expires.
    """

    def __init__(self, config: AsyncRoleTrackingConfig | None = None):
        self.config = config or AsyncRoleTrackingConfig()
        if self.config.num_uavs != len(self.config.uav_types):
            raise ValueError("P39 qualification uses one declared type per UAV")
        if self.config.num_events != 2:
            raise ValueError("P39 Stage-0 is frozen to two events")
        self.num_agents = self.config.num_uavs
        self.action_dim = self.config.num_events + 1
        self.obs_dim = 5 + 4 * self.config.num_events
        self.share_obs_dim = 2 * self.config.num_uavs + 2 * self.config.num_events
        self.rng = np.random.default_rng(self.config.seed)
        self.reset()

    def seed(self, seed: int) -> None:
        self.rng = np.random.default_rng(seed)

    def reset(self) -> Tuple[np.ndarray, np.ndarray, Dict[str, np.ndarray]]:
        self.step_count = 0
        self.done = False
        self.assignments = np.zeros(self.num_agents, dtype=np.int64)
        self.blackout = np.zeros(self.num_agents, dtype=np.int64)
        self.uav_pos = np.asarray([[-6.0, -2.0], [-6.0, 0.0], [-6.0, 2.0]], dtype=np.float32)
        self.event_pos = np.asarray([[3.0, -3.5], [3.0, 3.5]], dtype=np.float32)
        self.event_heading = np.asarray([2.65, -2.65], dtype=np.float32)
        self.cache_age = np.full((self.num_agents, self.config.num_events), self.config.max_steps, dtype=np.int64)
        self.covered_steps = np.zeros(self.config.num_events, dtype=np.int64)
        self.switches = 0
        self._update_sensing()
        return self._get_obs(), self._get_share_obs(), self._get_graph_obs()

    def step(self, actions: np.ndarray) -> Tuple[np.ndarray, np.ndarray, Dict[str, np.ndarray], np.ndarray, np.ndarray, Dict[str, float]]:
        if self.done:
            raise RuntimeError("Call reset() before stepping a finished episode")
        actions = np.asarray(actions, dtype=np.int64).reshape(self.num_agents)
        if np.any((actions < 0) | (actions >= self.action_dim)):
            raise ValueError("action outside P39 action interface")
        changed = actions != self.assignments
        self.switches += int(np.sum(changed & (self.assignments != 0)))
        self.assignments = actions.copy()
        self.blackout = np.maximum(self.blackout - 1, 0)
        self.blackout[changed] = self.config.reassignment_blackout_steps
        self._move_uavs()
        self._move_events()
        self.step_count += 1
        self._update_sensing()
        covered = self._coverage()
        self.covered_steps += covered.astype(np.int64)
        timeout = self.step_count >= self.config.max_steps
        self.done = bool(timeout)
        rewards = np.full((self.num_agents, 1), float(np.mean(covered)) - 0.02 * float(np.any(changed)), dtype=np.float32)
        dones = np.full((self.num_agents, 1), self.done, dtype=np.float32)
        info = {
            "coverage": float(np.mean(covered)),
            "coverage_event_0": float(covered[0]),
            "coverage_event_1": float(covered[1]),
            "switches": float(self.switches),
            "timeout": float(timeout),
            "mean_cache_age": float(np.mean(self.cache_age)),
        }
        return self._get_obs(), self._get_share_obs(), self._get_graph_obs(), rewards, dones, info

    def _move_uavs(self) -> None:
        for i, assignment in enumerate(self.assignments):
            if assignment == 0:
                continue
            target = self.event_pos[assignment - 1]
            delta = target - self.uav_pos[i]
            distance = float(np.linalg.norm(delta))
            if distance > 1e-6:
                self.uav_pos[i] += delta / distance * min(distance, self.config.uav_types[i].speed * self.config.dt)

    def _move_events(self) -> None:
        velocity = np.stack((np.cos(self.event_heading), np.sin(self.event_heading)), axis=1) * self.config.event_speed
        self.event_pos += velocity.astype(np.float32) * self.config.dt
        limit = self.config.world_size / 2.0
        for event in range(self.config.num_events):
            for axis in range(2):
                if abs(float(self.event_pos[event, axis])) >= limit:
                    self.event_heading[event] = np.pi - self.event_heading[event] if axis == 0 else -self.event_heading[event]
                    self.event_pos[event, axis] = np.clip(self.event_pos[event, axis], -limit, limit)

    def _update_sensing(self) -> None:
        self.cache_age = np.minimum(self.cache_age + 1, self.config.max_steps)
        for i, typ in enumerate(self.config.uav_types):
            if self.blackout[i] > 0 or self.step_count % typ.update_period != 0:
                continue
            for event in range(self.config.num_events):
                if np.linalg.norm(self.uav_pos[i] - self.event_pos[event]) <= typ.sensing_range:
                    self.cache_age[i, event] = 0

    def _coverage(self) -> np.ndarray:
        covered = np.zeros(self.config.num_events, dtype=np.float32)
        for event in range(self.config.num_events):
            for i, typ in enumerate(self.config.uav_types):
                if self.cache_age[i, event] <= self.config.cache_valid_steps:
                    covered[event] = 1.0
        return covered

    def _get_obs(self) -> np.ndarray:
        obs = np.zeros((self.num_agents, self.obs_dim), dtype=np.float32)
        half = self.config.world_size / 2.0
        for i, typ in enumerate(self.config.uav_types):
            obs[i, 0:2] = self.uav_pos[i] / half
            obs[i, 2] = typ.sensing_range / half
            obs[i, 3] = typ.update_period / 3.0
            obs[i, 4] = self.assignments[i] / self.config.num_events
            offset = 5
            for event in range(self.config.num_events):
                rel = self.event_pos[event] - self.uav_pos[i]
                obs[i, offset:offset + 2] = rel / self.config.world_size
                obs[i, offset + 2] = min(self.cache_age[i, event], self.config.cache_valid_steps + 1) / (self.config.cache_valid_steps + 1)
                obs[i, offset + 3] = float(self.cache_age[i, event] <= self.config.cache_valid_steps)
                offset += 4
        return obs

    def _get_share_obs(self) -> np.ndarray:
        state = np.concatenate((self.uav_pos.flatten(), self.event_pos.flatten())).astype(np.float32) / self.config.world_size
        return np.tile(state, (self.num_agents, 1))

    def _get_graph_obs(self) -> Dict[str, np.ndarray]:
        nodes = self.num_agents + self.config.num_events
        node_feat = np.zeros((nodes, 4), dtype=np.float32)
        node_feat[:self.num_agents, :2] = self.uav_pos / self.config.world_size
        node_feat[:self.num_agents, 2] = self.assignments / self.config.num_events
        node_feat[:self.num_agents, 3] = np.asarray([typ.sensing_range for typ in self.config.uav_types]) / self.config.world_size
        node_feat[self.num_agents:, :2] = self.event_pos / self.config.world_size
        role = np.concatenate((np.zeros(self.num_agents, dtype=np.int64), np.ones(self.config.num_events, dtype=np.int64)))
        adj = np.ones((nodes, nodes), dtype=np.float32) - np.eye(nodes, dtype=np.float32)
        return {"node_feat": node_feat, "role": role, "node_mask": np.ones(nodes, dtype=np.float32), "adj": adj}
