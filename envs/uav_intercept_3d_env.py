from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

import math
import numpy as np


ROLE_SCOUT = 0
ROLE_RELAY = 1
ROLE_ATTACKER = 2
ROLE_INTERCEPTOR = 3
ROLE_TARGET = 4

EDGE3D_FEAT_DIM = 18
RELATION3D_COUNT = 3
RELATION_PERCEPTION = 0
RELATION_COMMUNICATION = 1
RELATION_TASK_SUPPORT = 2

ACTION3D_TABLE = np.asarray(
    [
        [turn, climb, accel]
        for turn in (-1.0, 0.0, 1.0)
        for climb in (-1.0, 0.0, 1.0)
        for accel in (-1.0, 0.0, 1.0)
    ],
    dtype=np.float32,
)


@dataclass(frozen=True)
class UAV3DType:
    role: int
    max_speed: float
    min_speed: float
    max_accel: float
    max_turn_rate: float
    max_climb_rate: float
    max_gamma: float
    max_load: float
    radar_range: float
    radar_fov_h: float
    radar_fov_v: float
    comm_range: float
    attack_range_min: float
    attack_range_max: float
    attack_cone: float
    energy_coef: float


@dataclass
class UAVIntercept3DConfig:
    world_radius: float = 50_000.0
    min_altitude: float = 1_000.0
    max_altitude: float = 9_000.0
    altitude_protection_margin: float = 750.0
    boundary_protection_margin: float = 12_000.0
    dt: float = 1.0
    max_steps: int = 260
    num_blue: int = 3
    num_red: int = 1
    communication_range_scale: float = 1.0
    communication_dropout_prob: float = 0.0
    message_delay_steps: int = 0
    radar_dropout_prob: float = 0.0
    strict_target_sensing: bool = False
    target_prior_position: Tuple[float, float, float] = (10_000.0, 0.0, 5_000.0)
    failed_blue_agent: int = -1
    node_failure_start_step: int = 0
    node_failure_duration_steps: int = 0
    graph_relation_ablation: str = "none"
    target_policy: str = "evasive"
    seed: int | None = None
    attack_hold_steps: int = 4
    collision_radius: float = 120.0
    blue_types: List[UAV3DType] = field(
        default_factory=lambda: [
            UAV3DType(ROLE_SCOUT, 245.0, 120.0, 18.0, 0.035, 42.0, 0.26, 4.5, 17_500.0, math.radians(130), math.radians(55), 9_500.0, 1_800.0, 6_500.0, math.radians(42), 0.90),
            UAV3DType(ROLE_RELAY, 220.0, 115.0, 14.0, 0.030, 35.0, 0.22, 4.0, 12_000.0, math.radians(100), math.radians(45), 15_500.0, 2_000.0, 5_800.0, math.radians(35), 0.75),
            UAV3DType(ROLE_ATTACKER, 270.0, 135.0, 22.0, 0.052, 50.0, 0.31, 7.0, 11_000.0, math.radians(95), math.radians(42), 8_500.0, 1_400.0, 5_200.0, math.radians(50), 1.15),
        ]
    )
    target_type: UAV3DType = field(
        default_factory=lambda: UAV3DType(ROLE_TARGET, 255.0, 130.0, 18.0, 0.046, 42.0, 0.28, 6.0, 10_000.0, math.radians(100), math.radians(42), 0.0, 0.0, 0.0, 0.0, 1.00)
    )


class UAVIntercept3DEnv:
    """Lightweight 3DOF heterogeneous UAV cooperative interception environment.

    The environment is intentionally tactical rather than flight-control level:
    each blue UAV outputs turn, climb, and speed commands through a discrete
    action table. The state includes enough aviation constraints to support the
    next paper stage without forcing full 6DOF training.
    """

    def __init__(self, config: UAVIntercept3DConfig | None = None):
        self.config = config or UAVIntercept3DConfig()
        if self.config.num_blue != len(self.config.blue_types):
            raise ValueError("num_blue must match blue_types length in the first 3DOF implementation")
        if self.config.graph_relation_ablation not in {"none", "no_task_support"}:
            raise ValueError(f"Unsupported graph_relation_ablation: {self.config.graph_relation_ablation}")
        self.rng = np.random.default_rng(self.config.seed)
        self.dropout_rng = np.random.default_rng(None if self.config.seed is None else self.config.seed + 10_007)
        self.num_agents = self.config.num_blue
        self.action_dim = len(ACTION3D_TABLE)
        self.obs_dim = 34
        self.node_feat_dim = 20
        self.edge_feat_dim = EDGE3D_FEAT_DIM
        self.relation_count = RELATION3D_COUNT
        self.share_obs_dim = self.config.num_blue * 10 + self.config.num_red * 9 + 8
        self.reset()

    def seed(self, seed: int) -> None:
        self.rng = np.random.default_rng(seed)
        self.dropout_rng = np.random.default_rng(seed + 10_007)

    def reset(self) -> Tuple[np.ndarray, np.ndarray, Dict[str, np.ndarray]]:
        cfg = self.config
        self.step_count = 0
        self.done = False
        self.success = False
        self.collision = False
        self.constraint_violation = False
        self.attack_hold = 0
        self.last_detected_target_pos: np.ndarray | None = None
        self.last_detected_target_vel: np.ndarray | None = None
        self.last_detection_step = -1

        self.blue_pos = np.asarray(
            [
                [-14_000.0, -5_500.0, 4_800.0],
                [-16_000.0, 0.0, 5_200.0],
                [-14_000.0, 5_500.0, 4_600.0],
            ],
            dtype=np.float32,
        )
        self.blue_speed = np.asarray([185.0, 175.0, 205.0], dtype=np.float32)
        self.blue_heading = np.asarray([0.10, 0.0, -0.10], dtype=np.float32)
        self.blue_gamma = np.asarray([0.02, 0.0, -0.02], dtype=np.float32)
        self.blue_energy = np.ones(cfg.num_blue, dtype=np.float32)

        target_y = float(self.rng.uniform(-2_000.0, 2_000.0))
        self.red_pos = np.asarray([[10_000.0, target_y, 5_000.0]], dtype=np.float32)
        self.red_speed = np.asarray([210.0], dtype=np.float32)
        self.red_heading = np.asarray([math.pi + float(self.rng.uniform(-0.12, 0.12))], dtype=np.float32)
        self.red_gamma = np.asarray([float(self.rng.uniform(-0.03, 0.03))], dtype=np.float32)

        self.message_age = np.full((cfg.num_blue, cfg.num_blue), cfg.max_steps, dtype=np.float32)
        self.message_age[np.eye(cfg.num_blue, dtype=bool)] = 0.0
        self.comm_adj = np.eye(cfg.num_blue, dtype=np.float32)
        self.detected_by = np.zeros(cfg.num_blue, dtype=np.float32)
        self.attack_window = np.zeros(cfg.num_blue, dtype=np.float32)
        self._update_sensing_and_comm()

        self.history = {
            "blue_pos": [self.blue_pos.copy()],
            "red_pos": [self.red_pos.copy()],
            "detected_by": [self.detected_by.copy()],
            "attack_window": [self.attack_window.copy()],
        }
        return self._get_obs(), self._get_share_obs(), self._get_graph_obs()

    def step(
        self, actions: np.ndarray | List[int]
    ) -> Tuple[np.ndarray, np.ndarray, Dict[str, np.ndarray], np.ndarray, np.ndarray, Dict[str, float]]:
        if self.done:
            raise RuntimeError("Call reset() before stepping a finished episode.")

        actions = np.asarray(actions, dtype=np.int64).reshape(self.config.num_blue)
        actions = np.clip(actions, 0, self.action_dim - 1)
        prev_range = self._mean_target_range()
        prev_tracking = float(np.mean(self.detected_by))
        prev_window = float(np.max(self.attack_window))

        self._move_blue(actions)
        self._move_red()
        self._update_sensing_and_comm()
        self.step_count += 1

        cur_range = self._mean_target_range()
        tracking = float(np.mean(self.detected_by))
        window = float(np.max(self.attack_window))
        if window > 0.5 and tracking > 0.0 and self._comm_has_chain_to_attacker():
            self.attack_hold += 1
        else:
            self.attack_hold = 0

        self.success = self.attack_hold >= self.config.attack_hold_steps
        self.collision = self._has_collision()
        self.constraint_violation = self._has_constraint_violation()
        timeout = self.step_count >= self.config.max_steps
        self.done = bool(self.success or self.collision or self.constraint_violation or timeout)

        self.history["blue_pos"].append(self.blue_pos.copy())
        self.history["red_pos"].append(self.red_pos.copy())
        self.history["detected_by"].append(self.detected_by.copy())
        self.history["attack_window"].append(self.attack_window.copy())

        rewards = self._compute_rewards(prev_range, cur_range, prev_tracking, tracking, prev_window, window)
        dones = np.full((self.config.num_blue, 1), self.done, dtype=np.float32)
        infos = self._info(timeout)
        return self._get_obs(), self._get_share_obs(), self._get_graph_obs(), rewards, dones, infos

    def _move_blue(self, actions: np.ndarray) -> None:
        cfg = self.config
        for i, action in enumerate(actions):
            turn_cmd, climb_cmd, accel_cmd = ACTION3D_TABLE[int(action)]
            typ = cfg.blue_types[i]
            self.blue_heading[i] = wrap_angle(self.blue_heading[i] + turn_cmd * typ.max_turn_rate * cfg.dt)
            xy_radius = float(np.linalg.norm(self.blue_pos[i, :2]))
            if xy_radius >= cfg.world_radius - cfg.boundary_protection_margin:
                desired_heading = math.atan2(float(-self.blue_pos[i, 1]), float(-self.blue_pos[i, 0]))
                heading_error = angle_diff(desired_heading, float(self.blue_heading[i]))
                self.blue_heading[i] = wrap_angle(
                    self.blue_heading[i] + float(np.clip(heading_error, -typ.max_turn_rate * cfg.dt, typ.max_turn_rate * cfg.dt))
                )
                accel_cmd = -1.0
            self.blue_gamma[i] = float(np.clip(self.blue_gamma[i] + climb_cmd * 0.35 * typ.max_gamma * cfg.dt, -typ.max_gamma, typ.max_gamma))
            if self.blue_pos[i, 2] <= cfg.min_altitude + cfg.altitude_protection_margin and self.blue_gamma[i] < 0.0:
                self.blue_gamma[i] = 0.25 * typ.max_gamma
            elif self.blue_pos[i, 2] >= cfg.max_altitude - cfg.altitude_protection_margin and self.blue_gamma[i] > 0.0:
                self.blue_gamma[i] = -0.25 * typ.max_gamma
            self.blue_speed[i] = float(np.clip(self.blue_speed[i] + accel_cmd * typ.max_accel * cfg.dt, typ.min_speed, typ.max_speed))
            self.blue_pos[i] += velocity_from_state(self.blue_speed[i], self.blue_heading[i], self.blue_gamma[i]) * cfg.dt
            self.blue_energy[i] = max(0.0, self.blue_energy[i] - typ.energy_coef * (0.0005 + abs(turn_cmd) * 0.0008 + abs(climb_cmd) * 0.0008 + abs(accel_cmd) * 0.0005))

    def _move_red(self) -> None:
        target = self.config.target_type
        if self.config.target_policy == "straight":
            turn = 0.0
            climb = 0.0
        else:
            center_blue = np.mean(self.blue_pos, axis=0)
            away = self.red_pos[0, :2] - center_blue[:2]
            desired_heading = math.atan2(float(away[1]), float(away[0]))
            turn = float(np.clip(angle_diff(desired_heading, self.red_heading[0]), -target.max_turn_rate, target.max_turn_rate))
            desired_alt = 5_600.0 if center_blue[2] < self.red_pos[0, 2] else 4_400.0
            climb = float(np.clip((desired_alt - self.red_pos[0, 2]) / 2_000.0, -1.0, 1.0))
            if self.config.target_policy == "break_turn":
                rel = self.red_pos[0] - self.blue_pos
                dists = np.linalg.norm(rel, axis=1)
                nearest = int(np.argmin(dists))
                nearest_dist = float(dists[nearest])
                if nearest_dist < 9_000.0:
                    los_heading = math.atan2(float(rel[nearest, 1]), float(rel[nearest, 0]))
                    side = 1.0 if math.sin(0.045 * self.step_count + nearest) >= 0.0 else -1.0
                    desired_heading = wrap_angle(los_heading + side * math.pi * 0.5)
                    turn = float(
                        np.clip(
                            angle_diff(desired_heading, self.red_heading[0]),
                            -target.max_turn_rate,
                            target.max_turn_rate,
                        )
                    )
                    desired_alt = 5_900.0 if self.red_pos[0, 2] < center_blue[2] else 4_100.0
                    climb = float(np.clip((desired_alt - self.red_pos[0, 2]) / 1_500.0, -1.0, 1.0))
            elif self.config.target_policy in {"weaving", "weaving_mild"}:
                weave_amp = 0.45 if self.config.target_policy == "weaving" else 0.20
                alt_amp = 850.0 if self.config.target_policy == "weaving" else 350.0
                desired_heading = wrap_angle(desired_heading + weave_amp * math.sin(0.07 * self.step_count))
                turn = float(np.clip(angle_diff(desired_heading, self.red_heading[0]), -target.max_turn_rate, target.max_turn_rate))
                desired_alt = 5_000.0 + alt_amp * math.sin(0.045 * self.step_count + 0.7)
                climb = float(np.clip((desired_alt - self.red_pos[0, 2]) / 1_800.0, -1.0, 1.0))
        self.red_heading[0] = wrap_angle(self.red_heading[0] + turn * self.config.dt)
        self.red_gamma[0] = float(np.clip(self.red_gamma[0] + climb * 0.25 * target.max_gamma * self.config.dt, -target.max_gamma, target.max_gamma))
        xy_radius = float(np.linalg.norm(self.red_pos[0, :2]))
        if xy_radius >= self.config.world_radius - self.config.boundary_protection_margin:
            desired_heading = math.atan2(float(-self.red_pos[0, 1]), float(-self.red_pos[0, 0]))
            self.red_heading[0] = wrap_angle(
                self.red_heading[0]
                + float(np.clip(angle_diff(desired_heading, float(self.red_heading[0])), -target.max_turn_rate, target.max_turn_rate))
            )
        if self.red_pos[0, 2] <= self.config.min_altitude + self.config.altitude_protection_margin and self.red_gamma[0] < 0.0:
            self.red_gamma[0] = 0.25 * target.max_gamma
        elif self.red_pos[0, 2] >= self.config.max_altitude - self.config.altitude_protection_margin and self.red_gamma[0] > 0.0:
            self.red_gamma[0] = -0.25 * target.max_gamma
        self.red_pos[0] += velocity_from_state(self.red_speed[0], self.red_heading[0], self.red_gamma[0]) * self.config.dt

    def _update_sensing_and_comm(self) -> None:
        cfg = self.config
        self.detected_by = np.zeros(cfg.num_blue, dtype=np.float32)
        self.attack_window = np.zeros(cfg.num_blue, dtype=np.float32)
        for i, typ in enumerate(cfg.blue_types):
            visible = self._radar_visible(i, typ)
            if visible and self.dropout_rng.random() >= cfg.radar_dropout_prob:
                self.detected_by[i] = 1.0
        if np.any(self.detected_by > 0.5):
            self.last_detected_target_pos = self.red_pos[0].copy()
            self.last_detected_target_vel = velocity_from_state(self.red_speed[0], self.red_heading[0], self.red_gamma[0]).copy()
            self.last_detection_step = self.step_count

        self.comm_adj = np.eye(cfg.num_blue, dtype=np.float32)
        for i in range(cfg.num_blue):
            for j in range(cfg.num_blue):
                if i == j:
                    self.message_age[i, j] = 0.0
                    continue
                if self._is_comm_failed(i) or self._is_comm_failed(j):
                    self.message_age[i, j] = min(float(cfg.max_steps), self.message_age[i, j] + 1.0)
                    continue
                dist = float(np.linalg.norm(self.blue_pos[j] - self.blue_pos[i]))
                effective_range = cfg.communication_range_scale * min(cfg.blue_types[i].comm_range, cfg.blue_types[j].comm_range)
                reachable = dist <= effective_range
                reachable = reachable and self.dropout_rng.random() >= cfg.communication_dropout_prob
                if reachable:
                    self.comm_adj[i, j] = 1.0
                    self.message_age[i, j] = float(cfg.message_delay_steps)
                else:
                    self.message_age[i, j] = min(float(cfg.max_steps), self.message_age[i, j] + 1.0)

        for i, typ in enumerate(cfg.blue_types):
            self.attack_window[i] = float(self._in_attack_window(i, typ))

    def _is_comm_failed(self, agent_id: int) -> bool:
        cfg = self.config
        if cfg.failed_blue_agent < 0 or agent_id != cfg.failed_blue_agent:
            return False
        if cfg.node_failure_duration_steps <= 0:
            return False
        return cfg.node_failure_start_step <= self.step_count < cfg.node_failure_start_step + cfg.node_failure_duration_steps

    def _radar_visible(self, i: int, typ: UAV3DType) -> bool:
        rel = self.red_pos[0] - self.blue_pos[i]
        dist = float(np.linalg.norm(rel))
        if dist > typ.radar_range:
            return False
        horizontal = math.atan2(float(rel[1]), float(rel[0]))
        az_err = abs(angle_diff(horizontal, self.blue_heading[i]))
        elev = math.atan2(float(rel[2]), float(np.linalg.norm(rel[:2]) + 1e-6))
        el_err = abs(elev - float(self.blue_gamma[i]))
        return az_err <= typ.radar_fov_h * 0.5 and el_err <= typ.radar_fov_v * 0.5

    def _in_attack_window(self, i: int, typ: UAV3DType) -> bool:
        if typ.role not in {ROLE_ATTACKER, ROLE_INTERCEPTOR}:
            return False
        rel = self.red_pos[0] - self.blue_pos[i]
        dist = float(np.linalg.norm(rel))
        if dist < typ.attack_range_min or dist > typ.attack_range_max:
            return False
        los_heading = math.atan2(float(rel[1]), float(rel[0]))
        heading_err = abs(angle_diff(los_heading, self.blue_heading[i]))
        alt_err = abs(float(rel[2]))
        closure = float(np.dot(velocity_from_state(self.blue_speed[i], self.blue_heading[i], self.blue_gamma[i]) - velocity_from_state(self.red_speed[0], self.red_heading[0], self.red_gamma[0]), unit(rel)))
        return heading_err <= typ.attack_cone and alt_err <= 1_600.0 and closure > -30.0

    def _comm_has_chain_to_attacker(self) -> bool:
        attacker_ids = [i for i, typ in enumerate(self.config.blue_types) if typ.role in {ROLE_ATTACKER, ROLE_INTERCEPTOR}]
        sensing_ids = [i for i, value in enumerate(self.detected_by) if value > 0.5]
        if not attacker_ids or not sensing_ids:
            return False
        reach = self._transitive_comm()
        return any(reach[src, dst] > 0.5 for src in sensing_ids for dst in attacker_ids)

    def _transitive_comm(self) -> np.ndarray:
        reach = self.comm_adj.copy()
        n = reach.shape[0]
        for k in range(n):
            for i in range(n):
                for j in range(n):
                    reach[i, j] = max(reach[i, j], reach[i, k] * reach[k, j])
        return reach

    def _mean_target_range(self) -> float:
        return float(np.mean(np.linalg.norm(self.blue_pos - self.red_pos[0], axis=1)))

    def _has_collision(self) -> bool:
        for i in range(self.config.num_blue):
            if np.linalg.norm(self.blue_pos[i] - self.red_pos[0]) < self.config.collision_radius:
                return True
            for j in range(i + 1, self.config.num_blue):
                if np.linalg.norm(self.blue_pos[i] - self.blue_pos[j]) < self.config.collision_radius:
                    return True
        return False

    def _has_constraint_violation(self) -> bool:
        cfg = self.config
        if np.any(self.blue_pos[:, 2] < cfg.min_altitude) or np.any(self.blue_pos[:, 2] > cfg.max_altitude):
            return True
        if np.any(np.linalg.norm(self.blue_pos[:, :2], axis=1) > cfg.world_radius):
            return True
        return False

    def _compute_rewards(self, prev_range: float, cur_range: float, prev_tracking: float, tracking: float, prev_window: float, window: float) -> np.ndarray:
        progress = np.clip((prev_range - cur_range) / 1_000.0, -1.0, 1.0)
        connectivity = self._comm_connectivity()
        age_penalty = min(1.0, self._mean_message_age() / 80.0)
        base = 0.25 * progress + 0.12 * tracking + 0.18 * window + 0.05 * connectivity - 0.03 * age_penalty
        base += 0.05 * max(0.0, tracking - prev_tracking) + 0.08 * max(0.0, window - prev_window)
        if self.success:
            base += 2.0
        if self.collision:
            base -= 2.0
        if self.constraint_violation:
            base -= 1.5
        rewards = np.full((self.config.num_blue, 1), base, dtype=np.float32)
        for i, typ in enumerate(self.config.blue_types):
            if typ.role == ROLE_SCOUT:
                rewards[i, 0] += 0.08 * self.detected_by[i]
            if typ.role == ROLE_RELAY:
                rewards[i, 0] += 0.05 * connectivity
            if typ.role in {ROLE_ATTACKER, ROLE_INTERCEPTOR}:
                rewards[i, 0] += 0.12 * self.attack_window[i]
            rewards[i, 0] -= 0.02 * (1.0 - self.blue_energy[i])
        return rewards

    def _comm_connectivity(self) -> float:
        reach = self._transitive_comm()
        off_diag = reach[~np.eye(self.config.num_blue, dtype=bool)]
        return float(np.mean(off_diag)) if off_diag.size else 1.0

    def _mean_message_age(self) -> float:
        off_diag = self.message_age[~np.eye(self.config.num_blue, dtype=bool)]
        return float(np.mean(off_diag)) if off_diag.size else 0.0

    def _info(self, timeout: bool) -> Dict[str, float]:
        return {
            "success": float(self.success),
            "timeout": float(timeout and not self.success and not self.collision and not self.constraint_violation),
            "collision": float(self.collision),
            "constraint_violation": float(self.constraint_violation),
            "mean_range": self._mean_target_range(),
            "tracking_rate": float(np.mean(self.detected_by)),
            "attack_window_rate": float(np.mean(self.attack_window)),
            "chain_closed": float(self.attack_hold >= self.config.attack_hold_steps),
            "comm_connectivity": self._comm_connectivity(),
            "mean_message_age": self._mean_message_age(),
            "communication_range_scale": float(self.config.communication_range_scale),
            "strict_target_sensing": float(self.config.strict_target_sensing),
            "target_estimate_age": float(self.step_count - self.last_detection_step) if self.last_detection_step >= 0 else float(self.config.max_steps),
            "target_estimate_is_prior": float(self.config.strict_target_sensing and self.last_detected_target_pos is None),
            "node_failure_active": float(any(self._is_comm_failed(i) for i in range(self.config.num_blue))),
            "failed_blue_agent": float(self.config.failed_blue_agent),
            "step": float(self.step_count),
        }

    def _target_state_for_observation(self) -> tuple[np.ndarray, float, float, float, np.ndarray]:
        if not self.config.strict_target_sensing:
            vel = velocity_from_state(self.red_speed[0], self.red_heading[0], self.red_gamma[0])
            return self.red_pos[0], float(self.red_speed[0]), float(self.red_heading[0]), float(self.red_gamma[0]), vel
        if self.last_detected_target_pos is None:
            pos = np.asarray(self.config.target_prior_position, dtype=np.float32)
            vel = np.zeros(3, dtype=np.float32)
            return pos, 0.0, 0.0, 0.0, vel
        vel = self.last_detected_target_vel if self.last_detected_target_vel is not None else np.zeros(3, dtype=np.float32)
        speed = float(np.linalg.norm(vel))
        if speed <= 1e-6:
            return self.last_detected_target_pos, 0.0, 0.0, 0.0, vel.astype(np.float32)
        heading = math.atan2(float(vel[1]), float(vel[0]))
        gamma = math.atan2(float(vel[2]), float(np.linalg.norm(vel[:2]) + 1e-6))
        return self.last_detected_target_pos, speed, heading, gamma, vel.astype(np.float32)

    def _get_obs(self) -> np.ndarray:
        obs = np.zeros((self.config.num_blue, self.obs_dim), dtype=np.float32)
        target_est, _, _, _, red_vel = self._target_state_for_observation()
        for i, typ in enumerate(self.config.blue_types):
            rel = target_est - self.blue_pos[i]
            vel = velocity_from_state(self.blue_speed[i], self.blue_heading[i], self.blue_gamma[i])
            obs[i] = np.asarray(
                [
                    self.blue_pos[i, 0] / self.config.world_radius,
                    self.blue_pos[i, 1] / self.config.world_radius,
                    self.blue_pos[i, 2] / self.config.max_altitude,
                    self.blue_speed[i] / typ.max_speed,
                    math.sin(float(self.blue_heading[i])),
                    math.cos(float(self.blue_heading[i])),
                    math.sin(float(self.blue_gamma[i])),
                    math.cos(float(self.blue_gamma[i])),
                    rel[0] / self.config.world_radius,
                    rel[1] / self.config.world_radius,
                    rel[2] / self.config.max_altitude,
                    float(np.linalg.norm(rel)) / self.config.world_radius,
                    red_vel[0] / typ.max_speed,
                    red_vel[1] / typ.max_speed,
                    red_vel[2] / typ.max_speed,
                    vel[0] / typ.max_speed,
                    vel[1] / typ.max_speed,
                    vel[2] / typ.max_speed,
                    self.detected_by[i],
                    self.attack_window[i],
                    self.blue_energy[i],
                    typ.radar_range / self.config.world_radius,
                    typ.comm_range * self.config.communication_range_scale / self.config.world_radius,
                    typ.attack_range_max / self.config.world_radius,
                    float(typ.role == ROLE_SCOUT),
                    float(typ.role == ROLE_RELAY),
                    float(typ.role == ROLE_ATTACKER),
                    float(typ.role == ROLE_INTERCEPTOR),
                    self._comm_connectivity(),
                    self._mean_message_age() / self.config.max_steps,
                    float(self.step_count - self.last_detection_step) / self.config.max_steps if self.last_detection_step >= 0 else 1.0,
                    float(self.attack_hold) / max(1, self.config.attack_hold_steps),
                    self.config.communication_dropout_prob,
                    float(self.config.message_delay_steps) / 10.0,
                ],
                dtype=np.float32,
            )
        return obs

    def _get_share_obs(self) -> np.ndarray:
        global_vec: list[float] = []
        for i, typ in enumerate(self.config.blue_types):
            global_vec.extend(
                [
                    self.blue_pos[i, 0] / self.config.world_radius,
                    self.blue_pos[i, 1] / self.config.world_radius,
                    self.blue_pos[i, 2] / self.config.max_altitude,
                    self.blue_speed[i] / typ.max_speed,
                    math.sin(float(self.blue_heading[i])),
                    math.cos(float(self.blue_heading[i])),
                    math.sin(float(self.blue_gamma[i])),
                    math.cos(float(self.blue_gamma[i])),
                    self.detected_by[i],
                    self.attack_window[i],
                ]
            )
        target_pos, target_speed, target_heading, _, red_vel = self._target_state_for_observation()
        global_vec.extend(
            [
                target_pos[0] / self.config.world_radius,
                target_pos[1] / self.config.world_radius,
                target_pos[2] / self.config.max_altitude,
                target_speed / self.config.target_type.max_speed,
                math.sin(float(target_heading)),
                math.cos(float(target_heading)),
                red_vel[0] / self.config.target_type.max_speed,
                red_vel[1] / self.config.target_type.max_speed,
                red_vel[2] / self.config.target_type.max_speed,
                self._comm_connectivity(),
                self._mean_message_age() / self.config.max_steps,
                float(np.mean(self.detected_by)),
                float(np.mean(self.attack_window)),
                float(self.attack_hold) / max(1, self.config.attack_hold_steps),
                self.config.communication_dropout_prob,
                float(self.config.message_delay_steps) / 10.0,
                float(self.step_count) / self.config.max_steps,
            ]
        )
        arr = np.asarray(global_vec[: self.share_obs_dim], dtype=np.float32)
        if arr.size < self.share_obs_dim:
            arr = np.pad(arr, (0, self.share_obs_dim - arr.size))
        return np.tile(arr, (self.config.num_blue, 1)).astype(np.float32)

    def _get_graph_obs(self) -> Dict[str, np.ndarray]:
        n_blue = self.config.num_blue
        n = n_blue + self.config.num_red
        node = np.zeros((n, self.node_feat_dim), dtype=np.float32)
        edge = np.zeros((n, n, EDGE3D_FEAT_DIM), dtype=np.float32)
        adj = np.eye(n, dtype=np.float32)
        relation_adj = np.zeros((self.relation_count, n, n), dtype=np.float32)
        role = np.zeros(n, dtype=np.int64)

        target_pos, target_speed, target_heading, target_gamma, target_vel = self._target_state_for_observation()
        positions = np.vstack([self.blue_pos, target_pos[None, :]])
        speeds = np.concatenate([self.blue_speed, np.asarray([target_speed], dtype=np.float32)])
        headings = np.concatenate([self.blue_heading, np.asarray([target_heading], dtype=np.float32)])
        gammas = np.concatenate([self.blue_gamma, np.asarray([target_gamma], dtype=np.float32)])
        roles = [typ.role for typ in self.config.blue_types] + [ROLE_TARGET]
        max_speeds = [typ.max_speed for typ in self.config.blue_types] + [self.config.target_type.max_speed]

        for i in range(n):
            vel = velocity_from_state(speeds[i], headings[i], gammas[i])
            role[i] = roles[i]
            node[i] = np.asarray(
                [
                    positions[i, 0] / self.config.world_radius,
                    positions[i, 1] / self.config.world_radius,
                    positions[i, 2] / self.config.max_altitude,
                    speeds[i] / max_speeds[i],
                    math.sin(float(headings[i])),
                    math.cos(float(headings[i])),
                    math.sin(float(gammas[i])),
                    math.cos(float(gammas[i])),
                    vel[0] / max_speeds[i],
                    vel[1] / max_speeds[i],
                    vel[2] / max_speeds[i],
                    float(roles[i] == ROLE_SCOUT),
                    float(roles[i] == ROLE_RELAY),
                    float(roles[i] == ROLE_ATTACKER),
                    float(roles[i] == ROLE_INTERCEPTOR),
                    float(roles[i] == ROLE_TARGET),
                    self.detected_by[i] if i < n_blue else float(np.any(self.detected_by)),
                    self.attack_window[i] if i < n_blue else 0.0,
                    self.blue_energy[i] if i < n_blue else 1.0,
                    float(i < n_blue),
                ],
                dtype=np.float32,
            )

        velocities = np.asarray(
            [velocity_from_state(speeds[i], headings[i], gammas[i]) for i in range(n_blue)] + [target_vel],
            dtype=np.float32,
        )
        for i in range(n):
            for j in range(n):
                rel = positions[j] - positions[i]
                rel_vel = velocities[j] - velocities[i]
                dist = float(np.linalg.norm(rel))
                los = unit(rel)
                same_team = float((i < n_blue and j < n_blue) or (i >= n_blue and j >= n_blue))
                sensing = float(i < n_blue and j >= n_blue and self.detected_by[i] > 0.5)
                comm = float(i < n_blue and j < n_blue and self.comm_adj[i, j] > 0.5)
                support = float(i < n_blue and j < n_blue and self._support_edge(i, j))
                active_support = float(i < n_blue and j < n_blue and self._active_support_edge(i, j))
                if self.config.graph_relation_ablation == "no_task_support":
                    support = 0.0
                    active_support = 0.0
                attack = float(i < n_blue and j >= n_blue and self.attack_window[i] > 0.5)
                age = 0.0
                if i < n_blue and j < n_blue:
                    age = self.message_age[i, j] / self.config.max_steps
                confidence = max(sensing, max(0.0, 1.0 - age))
                adj[i, j] = max(adj[i, j], sensing, comm, support, attack)
                relation_adj[RELATION_PERCEPTION, i, j] = sensing
                relation_adj[RELATION_COMMUNICATION, i, j] = comm
                relation_adj[RELATION_TASK_SUPPORT, i, j] = active_support
                edge[i, j] = np.asarray(
                    [
                        rel[0] / self.config.world_radius,
                        rel[1] / self.config.world_radius,
                        rel[2] / self.config.max_altitude,
                        dist / self.config.world_radius,
                        los[0],
                        los[1],
                        los[2],
                        rel_vel[0] / 300.0,
                        rel_vel[1] / 300.0,
                        rel_vel[2] / 300.0,
                        same_team,
                        sensing,
                        comm,
                        support,
                        attack,
                        age,
                        confidence,
                        float(self.attack_hold) / max(1, self.config.attack_hold_steps),
                    ],
                    dtype=np.float32,
                )
        return {
            "node_feat": node,
            "edge_feat": edge,
            "adj": adj,
            "relation_adj": relation_adj,
            "role": role,
            "intent_label": np.asarray([4], dtype=np.int64),
            "has_intent_label": False,
        }

    def _support_edge(self, src: int, dst: int) -> bool:
        src_role = self.config.blue_types[src].role
        dst_role = self.config.blue_types[dst].role
        if src_role == ROLE_SCOUT and dst_role in {ROLE_ATTACKER, ROLE_INTERCEPTOR}:
            return True
        if src_role == ROLE_RELAY and dst_role in {ROLE_SCOUT, ROLE_ATTACKER, ROLE_INTERCEPTOR}:
            return True
        if src_role in {ROLE_ATTACKER, ROLE_INTERCEPTOR} and dst_role == ROLE_RELAY:
            return True
        return False

    def _has_target_information(self, agent_id: int) -> bool:
        if self.detected_by[agent_id] > 0.5:
            return True
        for source in range(self.config.num_blue):
            if self.detected_by[source] <= 0.5:
                continue
            if self.comm_adj[source, agent_id] > 0.5:
                return True
        return False

    def _active_support_edge(self, src: int, dst: int) -> bool:
        """Return whether a role-compatible edge currently serves the kill chain."""
        if not self._support_edge(src, dst):
            return False
        src_role = self.config.blue_types[src].role
        if src_role == ROLE_SCOUT:
            return self._has_target_information(src)
        if src_role == ROLE_RELAY:
            return self._has_target_information(src) or any(
                self.comm_adj[src, teammate] > 0.5 and self._has_target_information(teammate)
                for teammate in range(self.config.num_blue)
                if teammate != src
            )
        if src_role in {ROLE_ATTACKER, ROLE_INTERCEPTOR}:
            return bool(self.attack_window[src] > 0.5)
        return False


def velocity_from_state(speed: float, heading: float, gamma: float) -> np.ndarray:
    horizontal = float(speed) * math.cos(float(gamma))
    return np.asarray(
        [
            horizontal * math.cos(float(heading)),
            horizontal * math.sin(float(heading)),
            float(speed) * math.sin(float(gamma)),
        ],
        dtype=np.float32,
    )


def unit(v: np.ndarray, eps: float = 1e-8) -> np.ndarray:
    norm = float(np.linalg.norm(v))
    if norm < eps:
        return np.zeros_like(v, dtype=np.float32)
    return (v / norm).astype(np.float32)


def wrap_angle(angle: float) -> float:
    return (float(angle) + math.pi) % (2 * math.pi) - math.pi


def angle_diff(target: float, source: float) -> float:
    return wrap_angle(float(target) - float(source))
