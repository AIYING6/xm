from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

import math
import numpy as np


ACTION_TABLE = np.array(
    [
        [0.0, 0.0],    # keep
        [-1.0, 0.0],   # left
        [1.0, 0.0],    # right
        [0.0, 1.0],    # accelerate
        [0.0, -1.0],   # decelerate
        [-1.0, 1.0],   # left + accelerate
        [-1.0, -1.0],  # left + decelerate
        [1.0, 1.0],    # right + accelerate
        [1.0, -1.0],   # right + decelerate
    ],
    dtype=np.float32,
)

INTENT_STRAIGHT = 0
INTENT_ESCAPE_NEAREST = 1
INTENT_TURN_LEFT = 2
INTENT_TURN_RIGHT = 3
INTENT_UNKNOWN = 4
NUM_INTENTS = 5
EDGE_FEAT_DIM = 10


@dataclass
class UAVType:
    max_speed: float
    min_speed: float
    max_accel: float
    turn_rate: float
    sense_range: float
    energy_coef: float


@dataclass
class UAVPursuitConfig:
    num_pursuers: int = 3
    num_targets: int = 1
    world_size: float = 20.0
    dt: float = 0.2
    max_steps: int = 200
    capture_radius: float = 1.0
    surround_radius: float = 3.0
    communication_radius: float = 8.0
    communication_dropout_prob: float = 0.0
    target_policy: str = "nearest_escape"
    target_speed: float = 0.75
    seed: int | None = None
    pursuer_types: List[UAVType] = field(
        default_factory=lambda: [
            UAVType(1.20, 0.20, 0.45, 0.90, 8.0, 1.00),
            UAVType(1.00, 0.20, 0.40, 1.05, 7.0, 0.85),
            UAVType(0.85, 0.15, 0.35, 1.25, 6.5, 0.70),
        ]
    )


class UAVPursuitEnv:
    """A lightweight 2D cooperative pursuit environment.

    The interface is intentionally close to the MAPPO runner style:

        obs, share_obs, graph_obs = env.reset()
        obs, share_obs, graph_obs, rewards, dones, infos = env.step(actions)

    Actor execution uses local observations. The centralized critic can use
    share_obs. Graph observations are prepared for the later RI-GMAPPO encoder.
    """

    def __init__(self, config: UAVPursuitConfig | None = None):
        self.config = config or UAVPursuitConfig()
        self.rng = np.random.default_rng(self.config.seed)
        dropout_seed = None if self.config.seed is None else self.config.seed + 1_000_003
        self.dropout_rng = np.random.default_rng(dropout_seed)
        self.num_agents = self.config.num_pursuers
        self.action_dim = len(ACTION_TABLE)
        self.obs_dim = 19
        self.share_obs_dim = self.config.num_pursuers * 6 + self.config.num_targets * 5
        self.reset()

    def seed(self, seed: int) -> None:
        self.rng = np.random.default_rng(seed)
        self.dropout_rng = np.random.default_rng(seed + 1_000_003)

    def reset(self) -> Tuple[np.ndarray, np.ndarray, Dict[str, np.ndarray]]:
        cfg = self.config
        self.step_count = 0
        self.done = False
        self.success = False
        self.collision = False

        angles = np.linspace(0, 2 * math.pi, cfg.num_pursuers, endpoint=False)
        center = np.zeros(2, dtype=np.float32)
        radius = cfg.world_size * 0.35
        self.p_pos = np.stack(
            [center + radius * np.array([math.cos(a), math.sin(a)], dtype=np.float32) for a in angles]
        )
        self.p_heading = angles + math.pi
        self.p_speed = np.array(
            [0.5 * cfg.pursuer_types[i % len(cfg.pursuer_types)].max_speed for i in range(cfg.num_pursuers)],
            dtype=np.float32,
        )
        self.p_energy = np.ones(cfg.num_pursuers, dtype=np.float32)

        self.t_pos = self.rng.uniform(-2.0, 2.0, size=(cfg.num_targets, 2)).astype(np.float32)
        self.t_heading = self.rng.uniform(-math.pi, math.pi, size=cfg.num_targets).astype(np.float32)
        self.t_speed = np.full(cfg.num_targets, cfg.target_speed, dtype=np.float32)
        self.t_intent = np.full(cfg.num_targets, self._initial_intent_label(), dtype=np.int64)
        self._refresh_comm_dropout_mask()

        self.history = {
            "p_pos": [self.p_pos.copy()],
            "t_pos": [self.t_pos.copy()],
            "actions": [],
        }
        return self._get_obs(), self._get_share_obs(), self._get_graph_obs()

    def step(
        self, actions: np.ndarray | List[int]
    ) -> Tuple[np.ndarray, np.ndarray, Dict[str, np.ndarray], np.ndarray, np.ndarray, Dict[str, float]]:
        if self.done:
            raise RuntimeError("Call reset() before stepping a finished episode.")

        actions = np.asarray(actions, dtype=np.int64).reshape(self.config.num_pursuers)
        actions = np.clip(actions, 0, self.action_dim - 1)
        prev_dist = self._mean_target_distance()
        prev_agent_dist = self._agent_target_distances()

        self._move_pursuers(actions)
        self._move_targets()
        self._clip_positions()

        self.step_count += 1
        self.history["p_pos"].append(self.p_pos.copy())
        self.history["t_pos"].append(self.t_pos.copy())
        self.history["actions"].append(actions.copy())

        cur_dist = self._mean_target_distance()
        cur_agent_dist = self._agent_target_distances()
        captured = self._is_captured()
        collision = self._has_collision()
        timeout = self.step_count >= self.config.max_steps
        self._refresh_comm_dropout_mask()

        self.success = bool(captured)
        self.collision = bool(collision)
        self.done = bool(captured or collision or timeout)

        rewards = self._compute_rewards(prev_dist, cur_dist, prev_agent_dist, cur_agent_dist, captured, collision)
        dones = np.full((self.config.num_pursuers, 1), self.done, dtype=np.float32)
        infos = {
            "success": float(self.success),
            "collision": float(self.collision),
            "timeout": float(timeout and not captured and not collision),
            "mean_distance": float(cur_dist),
            "step": float(self.step_count),
        }
        return self._get_obs(), self._get_share_obs(), self._get_graph_obs(), rewards, dones, infos

    def _move_pursuers(self, actions: np.ndarray) -> None:
        for i, a in enumerate(actions):
            turn_cmd, accel_cmd = ACTION_TABLE[a]
            typ = self.config.pursuer_types[i % len(self.config.pursuer_types)]
            self.p_heading[i] = wrap_angle(self.p_heading[i] + turn_cmd * typ.turn_rate * self.config.dt)
            self.p_speed[i] = np.clip(
                self.p_speed[i] + accel_cmd * typ.max_accel * self.config.dt,
                typ.min_speed,
                typ.max_speed,
            )
            vel = self.p_speed[i] * np.array([math.cos(self.p_heading[i]), math.sin(self.p_heading[i])])
            self.p_pos[i] += vel.astype(np.float32) * self.config.dt
            self.p_energy[i] = max(
                0.0,
                self.p_energy[i] - typ.energy_coef * (0.002 + abs(accel_cmd) * 0.001 + abs(turn_cmd) * 0.0005),
            )

    def _move_targets(self) -> None:
        for j in range(self.config.num_targets):
            if self.config.target_policy == "straight":
                turn = 0.0
                intent = INTENT_STRAIGHT
            elif self.config.target_policy == "random":
                turn = float(self.rng.normal(0.0, 0.35))
                intent = self._turn_intent_label(turn)
            elif self.config.target_policy == "nearest_escape":
                d = self.p_pos - self.t_pos[j]
                nearest = d[np.argmin(np.linalg.norm(d, axis=1))]
                escape_heading = math.atan2(-nearest[1], -nearest[0])
                turn = angle_diff(escape_heading, self.t_heading[j])
                turn = float(np.clip(turn, -0.8, 0.8))
                intent = INTENT_ESCAPE_NEAREST
            else:
                if self.rng.random() < 0.6:
                    d = self.p_pos - self.t_pos[j]
                    nearest = d[np.argmin(np.linalg.norm(d, axis=1))]
                    escape_heading = math.atan2(-nearest[1], -nearest[0])
                    turn = float(np.clip(angle_diff(escape_heading, self.t_heading[j]), -0.8, 0.8))
                    intent = INTENT_ESCAPE_NEAREST
                else:
                    turn = float(self.rng.normal(0.0, 0.35))
                    intent = self._turn_intent_label(turn)

            self.t_intent[j] = intent
            self.t_heading[j] = wrap_angle(self.t_heading[j] + turn * self.config.dt)
            vel = self.t_speed[j] * np.array([math.cos(self.t_heading[j]), math.sin(self.t_heading[j])])
            self.t_pos[j] += vel.astype(np.float32) * self.config.dt

    def _initial_intent_label(self) -> int:
        if self.config.target_policy == "straight":
            return INTENT_STRAIGHT
        if self.config.target_policy == "nearest_escape":
            return INTENT_ESCAPE_NEAREST
        return INTENT_UNKNOWN

    @staticmethod
    def _turn_intent_label(turn: float) -> int:
        if turn > 0.05:
            return INTENT_TURN_RIGHT
        if turn < -0.05:
            return INTENT_TURN_LEFT
        return INTENT_STRAIGHT

    def _clip_positions(self) -> None:
        limit = self.config.world_size / 2
        self.p_pos = np.clip(self.p_pos, -limit, limit)
        self.t_pos = np.clip(self.t_pos, -limit, limit)

    def _get_obs(self) -> np.ndarray:
        obs = np.zeros((self.config.num_pursuers, self.obs_dim), dtype=np.float32)
        for i in range(self.config.num_pursuers):
            typ = self.config.pursuer_types[i % len(self.config.pursuer_types)]
            obs[i, 0:2] = self.p_pos[i] / (self.config.world_size / 2)
            obs[i, 2] = math.sin(self.p_heading[i])
            obs[i, 3] = math.cos(self.p_heading[i])
            obs[i, 4] = self.p_speed[i] / typ.max_speed
            obs[i, 5] = self.p_energy[i]
            obs[i, 6] = typ.max_speed / 1.5
            obs[i, 7] = typ.sense_range / 10.0

            nearest_target = self._nearest_target(i)
            rel_t = self.t_pos[nearest_target] - self.p_pos[i]
            obs[i, 8:10] = rel_t / self.config.world_size
            obs[i, 10] = np.linalg.norm(rel_t) / self.config.world_size
            obs[i, 11] = float(np.linalg.norm(rel_t) <= typ.sense_range)

            neighbors = self._nearest_neighbors(i, k=2)
            offset = 12
            for nb in neighbors:
                rel = self.p_pos[nb] - self.p_pos[i]
                obs[i, offset : offset + 2] = rel / self.config.world_size
                obs[i, offset + 2] = np.linalg.norm(rel) / self.config.communication_radius
                offset += 3
            obs[i] = np.clip(obs[i], -10.0, 10.0)
        return obs

    def _get_share_obs(self) -> np.ndarray:
        vals: List[float] = []
        for i in range(self.config.num_pursuers):
            typ = self.config.pursuer_types[i % len(self.config.pursuer_types)]
            vals.extend(
                [
                    self.p_pos[i, 0] / self.config.world_size,
                    self.p_pos[i, 1] / self.config.world_size,
                    math.sin(self.p_heading[i]),
                    math.cos(self.p_heading[i]),
                    self.p_speed[i] / typ.max_speed,
                    self.p_energy[i],
                ]
            )
        for j in range(self.config.num_targets):
            vals.extend(
                [
                    self.t_pos[j, 0] / self.config.world_size,
                    self.t_pos[j, 1] / self.config.world_size,
                    math.sin(self.t_heading[j]),
                    math.cos(self.t_heading[j]),
                    self.t_speed[j],
                ]
            )
        state = np.asarray(vals, dtype=np.float32)
        return np.tile(state, (self.config.num_pursuers, 1))

    def _get_graph_obs(self) -> Dict[str, np.ndarray]:
        num_nodes = self.config.num_pursuers + self.config.num_targets
        node_feat = np.zeros((num_nodes, 8), dtype=np.float32)
        role = np.zeros(num_nodes, dtype=np.int64)
        node_mask = np.ones(num_nodes, dtype=np.float32)

        for i in range(self.config.num_pursuers):
            typ = self.config.pursuer_types[i % len(self.config.pursuer_types)]
            node_feat[i, 0:2] = self.p_pos[i] / self.config.world_size
            node_feat[i, 2] = math.sin(self.p_heading[i])
            node_feat[i, 3] = math.cos(self.p_heading[i])
            node_feat[i, 4] = self.p_speed[i] / typ.max_speed
            node_feat[i, 5] = self.p_energy[i]
            node_feat[i, 6] = typ.max_speed / 1.5
            node_feat[i, 7] = typ.sense_range / 10.0
            role[i] = 0

        for j in range(self.config.num_targets):
            idx = self.config.num_pursuers + j
            node_feat[idx, 0:2] = self.t_pos[j] / self.config.world_size
            node_feat[idx, 2] = math.sin(self.t_heading[j])
            node_feat[idx, 3] = math.cos(self.t_heading[j])
            node_feat[idx, 4] = self.t_speed[j]
            role[idx] = 1

        adj = np.zeros((num_nodes, num_nodes), dtype=np.float32)
        edge_feat = np.zeros((num_nodes, num_nodes, EDGE_FEAT_DIM), dtype=np.float32)
        for i in range(num_nodes):
            for j in range(num_nodes):
                if i == j:
                    continue
                pi = self._node_pos(i)
                pj = self._node_pos(j)
                rel = pj - pi
                dist = float(np.linalg.norm(rel))
                bearing = math.atan2(float(rel[1]), float(rel[0]))
                rel_vel = self._node_velocity(j) - self._node_velocity(i)
                comm_reachable = self._is_comm_reachable(i, j, dist)
                edge_feat[i, j] = np.asarray(
                    [
                        rel[0] / self.config.world_size,
                        rel[1] / self.config.world_size,
                        dist / self.config.world_size,
                        dist / max(self.config.communication_radius, 1e-6),
                        math.cos(bearing),
                        math.sin(bearing),
                        rel_vel[0] / 1.5,
                        rel_vel[1] / 1.5,
                        float(comm_reachable),
                        float(role[j] == 1),
                    ],
                    dtype=np.float32,
                )
                if comm_reachable or role[j] == 1:
                    adj[i, j] = 1.0

        return {
            "node_feat": node_feat,
            "role": role,
            "node_mask": node_mask,
            "adj": adj,
            "edge_feat": edge_feat,
            "intent_label": self.t_intent.copy(),
        }

    def _compute_rewards(
        self,
        prev_dist: float,
        cur_dist: float,
        prev_agent_dist: np.ndarray,
        cur_agent_dist: np.ndarray,
        captured: bool,
        collision: bool,
    ) -> np.ndarray:
        team_progress = prev_dist - cur_dist
        agent_progress = prev_agent_dist - cur_agent_dist
        rewards = (0.10 * team_progress + 0.35 * agent_progress - 0.01).reshape(self.config.num_pursuers, 1)
        rewards = rewards.astype(np.float32)
        rewards[:, 0] += 0.03 * (1.0 - np.clip(cur_agent_dist / self.config.world_size, 0.0, 1.0))
        rewards[:, 0] += 0.02 * self._target_heading_alignment()
        rewards[:, 0] -= 0.005 * (1.0 - self.p_energy)
        rewards[:, 0] -= self._proximity_penalty()
        if captured:
            rewards[:, 0] += 10.0
        if collision:
            rewards[:, 0] -= 8.0
        return rewards

    def _is_captured(self) -> bool:
        for target in self.t_pos:
            dists = np.linalg.norm(self.p_pos - target, axis=1)
            if np.min(dists) <= self.config.capture_radius:
                return True
            if np.sum(dists <= self.config.surround_radius) >= min(3, self.config.num_pursuers):
                return True
        return False

    def _has_collision(self) -> bool:
        for i in range(self.config.num_pursuers):
            for j in range(i + 1, self.config.num_pursuers):
                if np.linalg.norm(self.p_pos[i] - self.p_pos[j]) < 0.25:
                    return True
        return False

    def _mean_target_distance(self) -> float:
        d = []
        for target in self.t_pos:
            d.extend(np.linalg.norm(self.p_pos - target, axis=1).tolist())
        return float(np.mean(d))

    def _agent_target_distances(self) -> np.ndarray:
        dists = []
        for i in range(self.config.num_pursuers):
            nearest_target = self._nearest_target(i)
            dists.append(np.linalg.norm(self.t_pos[nearest_target] - self.p_pos[i]))
        return np.asarray(dists, dtype=np.float32)

    def _proximity_penalty(self) -> np.ndarray:
        penalties = np.zeros(self.config.num_pursuers, dtype=np.float32)
        for i in range(self.config.num_pursuers):
            for j in range(i + 1, self.config.num_pursuers):
                d = np.linalg.norm(self.p_pos[i] - self.p_pos[j])
                if d < 1.0:
                    penalty = (1.0 - d) * 0.08
                    penalties[i] += penalty
                    penalties[j] += penalty
        return penalties

    def _target_heading_alignment(self) -> np.ndarray:
        align = np.zeros(self.config.num_pursuers, dtype=np.float32)
        for i in range(self.config.num_pursuers):
            nearest_target = self._nearest_target(i)
            rel = self.t_pos[nearest_target] - self.p_pos[i]
            desired = math.atan2(rel[1], rel[0])
            align[i] = math.cos(angle_diff(desired, self.p_heading[i]))
        return align

    def _nearest_target(self, pursuer_idx: int) -> int:
        return int(np.argmin(np.linalg.norm(self.t_pos - self.p_pos[pursuer_idx], axis=1)))

    def _nearest_neighbors(self, pursuer_idx: int, k: int) -> List[int]:
        d = np.linalg.norm(self.p_pos - self.p_pos[pursuer_idx], axis=1)
        order = np.argsort(d)
        return [
            int(x)
            for x in order
            if x != pursuer_idx and self._is_comm_reachable(pursuer_idx, int(x), float(d[x]))
        ][:k]

    def _refresh_comm_dropout_mask(self) -> None:
        n = self.config.num_pursuers
        self._comm_dropout_mask = np.ones((n, n), dtype=np.float32)
        p = float(np.clip(self.config.communication_dropout_prob, 0.0, 1.0))
        if p <= 0.0:
            return
        for i in range(n):
            for j in range(i + 1, n):
                keep = float(self.dropout_rng.random() >= p)
                self._comm_dropout_mask[i, j] = keep
                self._comm_dropout_mask[j, i] = keep

    def _is_comm_reachable(self, i: int, j: int, dist: float) -> bool:
        if i >= self.config.num_pursuers or j >= self.config.num_pursuers:
            return dist <= self.config.communication_radius
        if dist > self.config.communication_radius:
            return False
        return bool(self._comm_dropout_mask[i, j] > 0.5)

    def _node_pos(self, idx: int) -> np.ndarray:
        if idx < self.config.num_pursuers:
            return self.p_pos[idx]
        return self.t_pos[idx - self.config.num_pursuers]

    def _node_velocity(self, idx: int) -> np.ndarray:
        if idx < self.config.num_pursuers:
            return self.p_speed[idx] * np.array(
                [math.cos(self.p_heading[idx]), math.sin(self.p_heading[idx])],
                dtype=np.float32,
            )
        t_idx = idx - self.config.num_pursuers
        return self.t_speed[t_idx] * np.array(
            [math.cos(self.t_heading[t_idx]), math.sin(self.t_heading[t_idx])],
            dtype=np.float32,
        )


def wrap_angle(x: float) -> float:
    return (x + math.pi) % (2 * math.pi) - math.pi


def angle_diff(target: float, current: float) -> float:
    return wrap_angle(target - current)
