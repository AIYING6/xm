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

OBS3D_FIELD_NAMES = (
    "blue_x_norm",
    "blue_y_norm",
    "blue_z_norm",
    "blue_speed_norm",
    "blue_heading_sin",
    "blue_heading_cos",
    "blue_gamma_sin",
    "blue_gamma_cos",
    "target_rel_x_norm",
    "target_rel_y_norm",
    "target_rel_z_norm",
    "target_range_norm",
    "target_vel_x_norm",
    "target_vel_y_norm",
    "target_vel_z_norm",
    "blue_vel_x_norm",
    "blue_vel_y_norm",
    "blue_vel_z_norm",
    "direct_target_detected",
    "local_attack_window",
    "blue_energy",
    "radar_range_norm",
    "comm_range_norm",
    "attack_range_max_norm",
    "role_scout",
    "role_relay",
    "role_attacker",
    "role_interceptor",
    "local_inbound_connectivity",
    "local_inbound_message_age_norm",
    "local_target_cache_age_norm",
    "local_target_cache_confidence",
    "communication_dropout_prob",
    "message_delay_norm",
)
OBS3D_ROLE_IDENTITY_SLICE = slice(24, 28)
NODE3D_ROLE_IDENTITY_SLICE = slice(11, 16)
EDGE3D_FEAT_DIM = 17
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
    agent_target_info_bottleneck: bool = False
    max_target_message_age_steps: int = 80
    min_target_confidence: float = 0.2
    # --- P3-A OOD eval-side extensions (default no-op; do not change prior behavior) ---
    blue_init_rotation_deg: float = 0.0
    blue_init_spacing_scale: float = 1.0
    target_init_range_scale: float = 1.0
    target_init_bearing_offset_deg: float = 0.0
    comm_topology_mode: str = "none"
    target_prior_position: Tuple[float, float, float] = (10_000.0, 0.0, 5_000.0)
    failed_blue_agent: int = -1
    node_failure_start_step: int = 0
    node_failure_duration_steps: int = 0
    graph_relation_ablation: str = "none"
    target_policy: str = "evasive"
    # --- P3-B parameterized target policies (default no-op; legacy paths unchanged) ---
    target_heading_amp: float = 0.45  # used only by target_policy="weaving_param"
    target_break_turn_amp_rad: float = 0.5 * math.pi  # used only by target_policy="break_turn_param"
    seed: int | None = None
    attack_hold_steps: int = 4
    v16r_mission_mode: bool = False
    collision_radius: float = 120.0
    safety_proximity_distance: float = 0.0
    safety_proximity_penalty_weight: float = 0.0
    attack_geometry_reward_weight: float = 0.0
    min_success_step: int = 0
    post_loss_chain_reclosure_reward_weight: float = 0.0
    post_loss_chain_reclosure_min_step: int = 0
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
        self.neutralization_hold = 0
        self.neutralized = False
        self.post_loss_chain_lost = False
        self.post_loss_chain_reclosure_rewarded = False
        self.post_loss_chain_reclosure_bonus = 0.0
        self.last_detected_target_pos: np.ndarray | None = None
        self.last_detected_target_vel: np.ndarray | None = None
        self.last_detection_step = -1
        self.pending_messages: list[tuple[int, int, int]] = []
        self.pending_target_messages: list[dict[str, object]] = []

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

        # --- G1: blue formation spacing/rotation about centroid (default no-op) ---
        if cfg.blue_init_spacing_scale != 1.0 or cfg.blue_init_rotation_deg != 0.0:
            centroid = self.blue_pos.mean(axis=0)
            xy = self.blue_pos[:, :2] - centroid[:2]
            if cfg.blue_init_spacing_scale != 1.0:
                xy = xy * cfg.blue_init_spacing_scale
            if cfg.blue_init_rotation_deg != 0.0:
                th = math.radians(cfg.blue_init_rotation_deg)
                rot = np.asarray([[math.cos(th), -math.sin(th)],
                                  [math.sin(th), math.cos(th)]], dtype=np.float32)
                xy = xy @ rot.T
            self.blue_pos = np.concatenate([xy + centroid[:2], self.blue_pos[:, 2:3]],
                                           axis=1).astype(np.float32)

        target_y = float(self.rng.uniform(-2_000.0, 2_000.0))
        self.red_pos = np.asarray([[10_000.0, target_y, 5_000.0]], dtype=np.float32)
        # --- G2: target relative range/bearing from blue centroid (default no-op) ---
        if cfg.target_init_range_scale != 1.0 or cfg.target_init_bearing_offset_deg != 0.0:
            centroid = self.blue_pos.mean(axis=0)
            rel = self.red_pos[0, :2] - centroid[:2]
            r = float(np.linalg.norm(rel))
            ang = math.atan2(float(rel[1]), float(rel[0]))
            if cfg.target_init_range_scale != 1.0:
                r = r * cfg.target_init_range_scale
            if cfg.target_init_bearing_offset_deg != 0.0:
                ang = ang + math.radians(cfg.target_init_bearing_offset_deg)
            self.red_pos = np.asarray([[centroid[0] + r * math.cos(ang),
                                        centroid[1] + r * math.sin(ang),
                                        float(self.red_pos[0, 2])]], dtype=np.float32)
        self.red_speed = np.asarray([210.0], dtype=np.float32)
        self.red_heading = np.asarray([math.pi + float(self.rng.uniform(-0.12, 0.12))], dtype=np.float32)
        self.red_gamma = np.asarray([float(self.rng.uniform(-0.03, 0.03))], dtype=np.float32)

        # --- C1/C2: longest blue-blue XY pair (deterministic at reset) ---
        self._ood_prune_links: list[tuple[int, int]] = []
        if cfg.comm_topology_mode in ("symmetric_longest_prune", "directed_longest_prune"):
            xy = self.blue_pos[:, :2]
            dists = np.linalg.norm(xy[:, None, :] - xy[None, :, :], axis=-1)
            np.fill_diagonal(dists, -np.inf)
            a, b = np.unravel_index(int(np.argmax(dists)), dists.shape)
            lo = a if float(self.blue_pos[a, 1]) <= float(self.blue_pos[b, 1]) else b
            hi = b if lo == a else a
            if cfg.comm_topology_mode == "symmetric_longest_prune":
                self._ood_prune_links = [(lo, hi), (hi, lo)]
            else:  # directed: only lower-y -> higher-y
                self._ood_prune_links = [(lo, hi)]

        self.message_age = np.full((cfg.num_blue, cfg.num_blue), cfg.max_steps, dtype=np.float32)
        self.message_age[np.eye(cfg.num_blue, dtype=bool)] = 0.0
        self.comm_adj = np.eye(cfg.num_blue, dtype=np.float32)
        self.target_cache_valid = np.zeros(cfg.num_blue, dtype=np.float32)
        self.target_cache_pos = np.tile(np.asarray(cfg.target_prior_position, dtype=np.float32), (cfg.num_blue, 1))
        self.target_cache_vel = np.zeros((cfg.num_blue, 3), dtype=np.float32)
        self.target_cache_source = np.full(cfg.num_blue, -1, dtype=np.int64)
        self.target_cache_generation_step = np.full(cfg.num_blue, -1, dtype=np.int64)
        self.target_cache_delivery_step = np.full(cfg.num_blue, -1, dtype=np.int64)
        self.target_cache_hop_count = np.full(cfg.num_blue, -1, dtype=np.int64)
        self.target_cache_confidence = np.zeros(cfg.num_blue, dtype=np.float32)
        self.target_cache_path: list[list[int]] = [[] for _ in range(cfg.num_blue)]
        self.detected_by = np.zeros(cfg.num_blue, dtype=np.float32)
        self.attack_window = np.zeros(cfg.num_blue, dtype=np.float32)
        self.local_attack_window = np.zeros(cfg.num_blue, dtype=np.float32)
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

        self.step_count += 1
        self._move_blue(actions)
        self._move_red()
        self._update_sensing_and_comm()

        cur_range = self._mean_target_range()
        tracking = float(np.mean(self.detected_by))
        window = float(np.max(self.attack_window))
        if self.config.v16r_mission_mode:
            physical_window = any(
                typ.role in {ROLE_ATTACKER, ROLE_INTERCEPTOR} and self._in_attack_window(i, typ)
                for i, typ in enumerate(self.config.blue_types)
            )
            self.neutralization_hold = self.neutralization_hold + 1 if physical_window else 0
            self.neutralized = self.neutralization_hold >= self.config.attack_hold_steps
        else:
            if window > 0.5 and tracking > 0.0 and self._comm_has_chain_to_attacker():
                self.attack_hold += 1
            else:
                self.attack_hold = 0

        chain_closed = self.attack_hold >= self.config.attack_hold_steps
        failure_active = any(self._is_comm_failed(i) for i in range(self.config.num_blue))
        self.post_loss_chain_reclosure_bonus = 0.0
        if failure_active and not chain_closed:
            self.post_loss_chain_lost = True
        if (
            failure_active
            and chain_closed
            and self.post_loss_chain_lost
            and not self.post_loss_chain_reclosure_rewarded
            and self.step_count >= self.config.post_loss_chain_reclosure_min_step
        ):
            self.post_loss_chain_reclosure_bonus = float(self.config.post_loss_chain_reclosure_reward_weight)
            self.post_loss_chain_reclosure_rewarded = True

        self.success = (self.neutralized if self.config.v16r_mission_mode else chain_closed) and self.step_count >= self.config.min_success_step
        self.collision = self._has_collision()
        self.constraint_violation = self._has_constraint_violation()
        if self.config.v16r_mission_mode and (self.collision or self.constraint_violation):
            self.success = False
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

    def step_guidance(
        self, guidance: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, Dict[str, np.ndarray], np.ndarray, np.ndarray, Dict[str, float]]:
        """Advance with continuous normalized ``[turn, climb]`` guidance.

        This is an additive v1.6R interface; legacy ``step(int_actions)`` is
        intentionally unchanged.  Acceleration is supplied by the fixed
        deterministic closure controller (currently ``accel_cmd=1.0`` away
        from the boundary), so it cannot silently become a third learned
        control head.
        """
        if self.done:
            raise RuntimeError("Call reset() before stepping a finished episode.")
        guidance = np.asarray(guidance, dtype=np.float32)
        expected = (self.config.num_blue, 2)
        if guidance.shape != expected:
            raise ValueError(f"guidance must have shape {expected}, got {guidance.shape}")
        if not np.isfinite(guidance).all():
            raise ValueError("guidance contains NaN/Inf")
        guidance = np.clip(guidance, -1.0, 1.0)
        prev_range = self._mean_target_range()
        prev_tracking = float(np.mean(self.detected_by))
        prev_window = float(np.max(self.attack_window))
        self.step_count += 1
        self._move_blue_guidance(guidance)
        self._move_red()
        self._update_sensing_and_comm()

        cur_range = self._mean_target_range()
        tracking = float(np.mean(self.detected_by))
        window = float(np.max(self.attack_window))
        if self.config.v16r_mission_mode:
            physical_window = any(
                typ.role in {ROLE_ATTACKER, ROLE_INTERCEPTOR} and self._in_attack_window(i, typ)
                for i, typ in enumerate(self.config.blue_types)
            )
            self.neutralization_hold = self.neutralization_hold + 1 if physical_window else 0
            self.neutralized = self.neutralization_hold >= self.config.attack_hold_steps
        else:
            if window > 0.5 and tracking > 0.0 and self._comm_has_chain_to_attacker():
                self.attack_hold += 1
            else:
                self.attack_hold = 0
        chain_closed = self.attack_hold >= self.config.attack_hold_steps
        failure_active = any(self._is_comm_failed(i) for i in range(self.config.num_blue))
        self.post_loss_chain_reclosure_bonus = 0.0
        if failure_active and not chain_closed:
            self.post_loss_chain_lost = True
        if failure_active and chain_closed and self.post_loss_chain_lost and not self.post_loss_chain_reclosure_rewarded and self.step_count >= self.config.post_loss_chain_reclosure_min_step:
            self.post_loss_chain_reclosure_bonus = float(self.config.post_loss_chain_reclosure_reward_weight)
            self.post_loss_chain_reclosure_rewarded = True
        self.success = (self.neutralized if self.config.v16r_mission_mode else chain_closed) and self.step_count >= self.config.min_success_step
        self.collision = self._has_collision()
        self.constraint_violation = self._has_constraint_violation()
        if self.config.v16r_mission_mode and (self.collision or self.constraint_violation):
            self.success = False
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

    def _move_blue_guidance(self, guidance: np.ndarray) -> None:
        """Continuous turn/climb execution with the same deterministic dynamics."""
        cfg = self.config
        for i, (turn_cmd, climb_cmd) in enumerate(guidance):
            typ = cfg.blue_types[i]
            # The v1.6R guidance head controls turn/climb only.  The fixed
            # low-level controller supplies a deterministic closure policy so
            # the interface does not make the attacker slower than the target.
            accel_cmd = 1.0
            self.blue_heading[i] = wrap_angle(self.blue_heading[i] + float(turn_cmd) * typ.max_turn_rate * cfg.dt)
            xy_radius = float(np.linalg.norm(self.blue_pos[i, :2]))
            if xy_radius >= cfg.world_radius - cfg.boundary_protection_margin:
                desired_heading = math.atan2(float(-self.blue_pos[i, 1]), float(-self.blue_pos[i, 0]))
                heading_error = angle_diff(desired_heading, float(self.blue_heading[i]))
                self.blue_heading[i] = wrap_angle(self.blue_heading[i] + float(np.clip(heading_error, -typ.max_turn_rate * cfg.dt, typ.max_turn_rate * cfg.dt)))
                accel_cmd = -1.0
            self.blue_gamma[i] = float(np.clip(self.blue_gamma[i] + float(climb_cmd) * 0.35 * typ.max_gamma * cfg.dt, -typ.max_gamma, typ.max_gamma))
            if self.blue_pos[i, 2] <= cfg.min_altitude + cfg.altitude_protection_margin and self.blue_gamma[i] < 0.0:
                self.blue_gamma[i] = 0.25 * typ.max_gamma
            elif self.blue_pos[i, 2] >= cfg.max_altitude - cfg.altitude_protection_margin and self.blue_gamma[i] > 0.0:
                self.blue_gamma[i] = -0.25 * typ.max_gamma
            self.blue_speed[i] = float(np.clip(self.blue_speed[i] + accel_cmd * typ.max_accel * cfg.dt, typ.min_speed, typ.max_speed))
            self.blue_pos[i] += velocity_from_state(self.blue_speed[i], self.blue_heading[i], self.blue_gamma[i]) * cfg.dt
            self.blue_energy[i] = max(0.0, self.blue_energy[i] - typ.energy_coef * (0.0005 + abs(float(turn_cmd)) * 0.0008 + abs(float(climb_cmd)) * 0.0008 + abs(accel_cmd) * 0.0005))

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
            elif self.config.target_policy in {"weaving", "weaving_mild", "weaving_tiny"}:
                weave_params = {
                    "weaving": (0.45, 850.0),
                    "weaving_mild": (0.20, 350.0),
                    "weaving_tiny": (0.06, 120.0),
                }
                weave_amp, alt_amp = weave_params[self.config.target_policy]
                desired_heading = wrap_angle(desired_heading + weave_amp * math.sin(0.07 * self.step_count))
                turn = float(np.clip(angle_diff(desired_heading, self.red_heading[0]), -target.max_turn_rate, target.max_turn_rate))
                desired_alt = 5_000.0 + alt_amp * math.sin(0.045 * self.step_count + 0.7)
                climb = float(np.clip((desired_alt - self.red_pos[0, 2]) / 1_800.0, -1.0, 1.0))
            elif self.config.target_policy == "weaving_param":
                # P3-B single-axis weaving: only heading amplitude varies.
                # altitude amplitude fixed at 350 m (mild level); frequencies fixed.
                weave_amp = self.config.target_heading_amp
                alt_amp = 350.0
                desired_heading = wrap_angle(desired_heading + weave_amp * math.sin(0.07 * self.step_count))
                turn = float(np.clip(angle_diff(desired_heading, self.red_heading[0]), -target.max_turn_rate, target.max_turn_rate))
                desired_alt = 5_000.0 + alt_amp * math.sin(0.045 * self.step_count + 0.7)
                climb = float(np.clip((desired_alt - self.red_pos[0, 2]) / 1_800.0, -1.0, 1.0))
            elif self.config.target_policy == "break_turn_param":
                # P3-B single-axis break-turn: only the DESIRED break-heading
                # offset (relative to LOS) varies; trigger, phase, speed fixed.
                rel = self.red_pos[0] - self.blue_pos
                dists = np.linalg.norm(rel, axis=1)
                nearest = int(np.argmin(dists))
                nearest_dist = float(dists[nearest])
                if nearest_dist < 9_000.0:
                    los_heading = math.atan2(float(rel[nearest, 1]), float(rel[nearest, 0]))
                    side = 1.0 if math.sin(0.045 * self.step_count + nearest) >= 0.0 else -1.0
                    desired_heading = wrap_angle(los_heading + side * self.config.target_break_turn_amp_rad)
                    turn = float(
                        np.clip(
                            angle_diff(desired_heading, self.red_heading[0]),
                            -target.max_turn_rate,
                            target.max_turn_rate,
                        )
                    )
                    desired_alt = 5_900.0 if self.red_pos[0, 2] < center_blue[2] else 4_100.0
                    climb = float(np.clip((desired_alt - self.red_pos[0, 2]) / 1_500.0, -1.0, 1.0))
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
        self.local_attack_window = np.zeros(cfg.num_blue, dtype=np.float32)
        for i, typ in enumerate(cfg.blue_types):
            visible = self._radar_visible(i, typ)
            if visible and self.dropout_rng.random() >= cfg.radar_dropout_prob:
                self.detected_by[i] = 1.0
        if np.any(self.detected_by > 0.5):
            self.last_detected_target_pos = self.red_pos[0].copy()
            self.last_detected_target_vel = velocity_from_state(self.red_speed[0], self.red_heading[0], self.red_gamma[0]).copy()
            self.last_detection_step = self.step_count
            for detector in np.flatnonzero(self.detected_by > 0.5):
                self._write_target_cache(
                    int(detector),
                    pos=self.last_detected_target_pos,
                    vel=self.last_detected_target_vel,
                    source=int(detector),
                    generation_step=self.step_count,
                    delivery_step=self.step_count,
                    hop_count=0,
                    confidence=1.0,
                    path=[int(detector)],
                )

        eligible_valid = self.target_cache_valid.copy()
        eligible_pos = self.target_cache_pos.copy()
        eligible_vel = self.target_cache_vel.copy()
        eligible_source = self.target_cache_source.copy()
        eligible_generation_step = self.target_cache_generation_step.copy()
        eligible_hop_count = self.target_cache_hop_count.copy()
        eligible_confidence = self.target_cache_confidence.copy()
        eligible_path = [list(path) for path in self.target_cache_path]

        self.comm_adj = np.eye(cfg.num_blue, dtype=np.float32)
        delivered_comm = np.eye(cfg.num_blue, dtype=np.float32)
        retained_messages: list[tuple[int, int, int]] = []
        for deliver_step, receiver, sender in self.pending_messages:
            if deliver_step <= self.step_count:
                if not self._is_comm_failed(receiver) and not self._is_comm_failed(sender):
                    delivered_comm[receiver, sender] = 1.0
                    self.message_age[receiver, sender] = 0.0
            else:
                retained_messages.append((deliver_step, receiver, sender))
        self.pending_messages = retained_messages

        retained_target_messages: list[dict[str, object]] = []
        for message in self.pending_target_messages:
            deliver_step = int(message["deliver_step"])
            receiver = int(message["receiver"])
            sender = int(message["sender"])
            if deliver_step <= self.step_count:
                if not self._is_comm_failed(receiver) and not self._is_comm_failed(sender):
                    self._write_target_cache(
                        receiver,
                        pos=np.asarray(message["pos"], dtype=np.float32),
                        vel=np.asarray(message["vel"], dtype=np.float32),
                        source=int(message["source"]),
                        generation_step=int(message["generation_step"]),
                        delivery_step=deliver_step,
                        hop_count=int(message["hop_count"]),
                        confidence=float(message["confidence"]),
                        path=list(message["path"]),
                    )
            else:
                retained_target_messages.append(message)
        self.pending_target_messages = retained_target_messages

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
                    if cfg.message_delay_steps <= 0:
                        delivered_comm[i, j] = 1.0
                        self.message_age[i, j] = 0.0
                        if eligible_valid[j] > 0.5:
                            self._write_target_cache(
                                i,
                                pos=eligible_pos[j],
                                vel=eligible_vel[j],
                                source=int(eligible_source[j]),
                                generation_step=int(eligible_generation_step[j]),
                                delivery_step=self.step_count,
                                hop_count=int(eligible_hop_count[j] + 1),
                                confidence=float(eligible_confidence[j] * 0.95),
                                path=[*eligible_path[j], i],
                            )
                    else:
                        deliver_step = self.step_count + cfg.message_delay_steps
                        self.pending_messages.append((deliver_step, i, j))
                        if eligible_valid[j] > 0.5:
                            self.pending_target_messages.append(
                                {
                                    "deliver_step": deliver_step,
                                    "receiver": i,
                                    "sender": j,
                                    "pos": eligible_pos[j].copy(),
                                    "vel": eligible_vel[j].copy(),
                                    "source": int(eligible_source[j]),
                                    "generation_step": int(eligible_generation_step[j]),
                                    "hop_count": int(eligible_hop_count[j] + 1),
                                    "confidence": float(eligible_confidence[j] * 0.95),
                                    "path": [*eligible_path[j], i],
                                }
                            )
                else:
                    self.message_age[i, j] = min(float(cfg.max_steps), self.message_age[i, j] + 1.0)
        self.comm_adj = delivered_comm

        # --- C1/C2: apply topology pruning after comm-adjacency formation ---
        # link list stores directed (sender, receiver) pairs: lower-y -> higher-y for C2,
        # both directions for C1.
        for (src, dst) in self._ood_prune_links:
            if src != dst and 0 <= src < cfg.num_blue and 0 <= dst < cfg.num_blue:
                self.comm_adj[dst, src] = 0.0

        for i, typ in enumerate(cfg.blue_types):
            self.attack_window[i] = float(self._in_attack_window(i, typ))
            self.local_attack_window[i] = float(self._in_local_attack_window(i, typ))

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

    def _in_local_attack_window(self, i: int, typ: UAV3DType) -> bool:
        """Actor-visible attack-window proxy computed from legal target estimates."""
        if typ.role not in {ROLE_ATTACKER, ROLE_INTERCEPTOR}:
            return False
        if (
            self.config.strict_target_sensing
            and self.config.agent_target_info_bottleneck
            and not self._has_target_information(i)
        ):
            return False
        target_pos, _, _, _, target_vel = self._target_state_for_agent_observation(i)
        rel = target_pos - self.blue_pos[i]
        dist = float(np.linalg.norm(rel))
        if dist < typ.attack_range_min or dist > typ.attack_range_max:
            return False
        los_heading = math.atan2(float(rel[1]), float(rel[0]))
        heading_err = abs(angle_diff(los_heading, self.blue_heading[i]))
        alt_err = abs(float(rel[2]))
        blue_vel = velocity_from_state(self.blue_speed[i], self.blue_heading[i], self.blue_gamma[i])
        closure = float(np.dot(blue_vel - target_vel, unit(rel)))
        return heading_err <= typ.attack_cone and alt_err <= 1_600.0 and closure > -30.0

    def _comm_has_chain_to_attacker(self) -> bool:
        attacker_ids = [i for i, typ in enumerate(self.config.blue_types) if typ.role in {ROLE_ATTACKER, ROLE_INTERCEPTOR}]
        if not attacker_ids:
            return False
        return any(self._has_target_information(dst) for dst in attacker_ids)

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

    def _min_blue_red_distance(self) -> float:
        return float(np.min(np.linalg.norm(self.blue_pos - self.red_pos[0], axis=1)))

    def _min_blue_blue_distance(self) -> float:
        distances = [
            float(np.linalg.norm(self.blue_pos[i] - self.blue_pos[j]))
            for i in range(self.config.num_blue)
            for j in range(i + 1, self.config.num_blue)
        ]
        return float(min(distances)) if distances else float("inf")

    def _attack_geometry_score(self) -> float:
        scores: list[float] = []
        red_vel = velocity_from_state(self.red_speed[0], self.red_heading[0], self.red_gamma[0])
        for i, typ in enumerate(self.config.blue_types):
            if typ.role not in {ROLE_ATTACKER, ROLE_INTERCEPTOR}:
                continue
            rel = self.red_pos[0] - self.blue_pos[i]
            dist = float(np.linalg.norm(rel))
            if dist <= 1e-6:
                continue
            if dist < typ.attack_range_min:
                range_score = max(0.0, dist / max(typ.attack_range_min, 1e-6))
            elif dist > typ.attack_range_max:
                range_score = max(0.0, 1.0 - (dist - typ.attack_range_max) / max(typ.attack_range_max, 1e-6))
            else:
                range_score = 1.0

            los_heading = math.atan2(float(rel[1]), float(rel[0]))
            heading_err = abs(angle_diff(los_heading, self.blue_heading[i]))
            heading_score = max(0.0, 1.0 - heading_err / max(typ.attack_cone, 1e-6))
            alt_score = max(0.0, 1.0 - abs(float(rel[2])) / 1_600.0)
            blue_vel = velocity_from_state(self.blue_speed[i], self.blue_heading[i], self.blue_gamma[i])
            closure = float(np.dot(blue_vel - red_vel, unit(rel)))
            closure_score = float(np.clip((closure + 30.0) / 120.0, 0.0, 1.0))
            scores.append(range_score * heading_score * alt_score * closure_score)
        return float(max(scores)) if scores else 0.0

    def _safety_proximity_penalty(self) -> float:
        cfg = self.config
        if cfg.safety_proximity_distance <= 0.0 or cfg.safety_proximity_penalty_weight <= 0.0:
            return 0.0
        threshold = float(cfg.safety_proximity_distance)
        violations: list[float] = []
        for i in range(cfg.num_blue):
            blue_red_dist = float(np.linalg.norm(self.blue_pos[i] - self.red_pos[0]))
            violations.append(max(0.0, (threshold - blue_red_dist) / threshold))
            for j in range(i + 1, cfg.num_blue):
                blue_blue_dist = float(np.linalg.norm(self.blue_pos[i] - self.blue_pos[j]))
                violations.append(max(0.0, (threshold - blue_blue_dist) / threshold))
        return float(np.mean(violations)) if violations else 0.0

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
        if self.config.v16r_mission_mode:
            progress = float(np.clip((prev_range - cur_range) / 1_000.0, -1.0, 1.0))
            geometry = self._attack_geometry_score()
            base = 0.35 * progress + 0.65 * geometry
            if self.success:
                base += 2.0
            if self.collision:
                base -= 2.0
            if self.constraint_violation:
                base -= 1.5
            return np.full((self.config.num_blue, 1), base, dtype=np.float32)
        progress = np.clip((prev_range - cur_range) / 1_000.0, -1.0, 1.0)
        connectivity = self._comm_connectivity()
        age_penalty = min(1.0, self._mean_message_age() / 80.0)
        base = 0.25 * progress + 0.12 * tracking + 0.18 * window + 0.05 * connectivity - 0.03 * age_penalty
        base += 0.05 * max(0.0, tracking - prev_tracking) + 0.08 * max(0.0, window - prev_window)
        base += self.config.attack_geometry_reward_weight * self._attack_geometry_score()
        base += self.post_loss_chain_reclosure_bonus
        base -= self.config.safety_proximity_penalty_weight * self._safety_proximity_penalty()
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

    def _local_inbound_connectivity(self, agent_id: int) -> float:
        mask = np.ones(self.config.num_blue, dtype=bool)
        mask[agent_id] = False
        if not np.any(mask):
            return 1.0
        return float(np.mean(self.comm_adj[agent_id, mask]))

    def _local_inbound_message_age(self, agent_id: int) -> float:
        mask = np.ones(self.config.num_blue, dtype=bool)
        mask[agent_id] = False
        if not np.any(mask):
            return 0.0
        return float(np.mean(self.message_age[agent_id, mask]))

    def _local_target_cache_age(self, agent_id: int) -> float:
        if self.target_cache_valid[agent_id] <= 0.5 or self.target_cache_generation_step[agent_id] < 0:
            return float(self.config.max_steps)
        return float(max(0, self.step_count - int(self.target_cache_generation_step[agent_id])))

    def _local_target_cache_confidence(self, agent_id: int) -> float:
        if not self._has_fresh_target_cache(agent_id):
            return 0.0
        return float(self.target_cache_confidence[agent_id])

    def _has_fresh_target_cache(self, agent_id: int) -> bool:
        if self.target_cache_valid[agent_id] <= 0.5:
            return False
        if self.target_cache_generation_step[agent_id] < 0:
            return False
        cache_age = self._local_target_cache_age(agent_id)
        if cache_age > float(self.config.max_target_message_age_steps):
            return False
        if float(self.target_cache_confidence[agent_id]) < float(self.config.min_target_confidence):
            return False
        return True

    def _target_cache_stale_rate(self) -> float:
        valid_ids = [i for i in range(self.config.num_blue) if self.target_cache_valid[i] > 0.5]
        if not valid_ids:
            return 0.0
        stale = [not self._has_fresh_target_cache(i) for i in valid_ids]
        return float(np.mean(stale))

    def _info(self, timeout: bool) -> Dict[str, float]:
        local_cache_ages = [self._local_target_cache_age(i) for i in range(self.config.num_blue)]
        local_cache_conf = [self._local_target_cache_confidence(i) for i in range(self.config.num_blue)]
        attacker_ids = [
            i
            for i, typ in enumerate(self.config.blue_types)
            if typ.role in {ROLE_ATTACKER, ROLE_INTERCEPTOR}
        ]
        fresh_attacker_ids = [i for i in attacker_ids if self._has_target_information(i)]
        attacker_window_info_ids = [
            i for i in fresh_attacker_ids if self.attack_window[i] > 0.5
        ]
        attacker_cache_generation_steps = [
            float(self.target_cache_generation_step[i])
            for i in fresh_attacker_ids
            if self.target_cache_generation_step[i] >= 0
        ]
        attacker_cache_delivery_steps = [
            float(self.target_cache_delivery_step[i])
            for i in fresh_attacker_ids
            if self.target_cache_delivery_step[i] >= 0
        ]
        attacker_window_cache_generation_steps = [
            float(self.target_cache_generation_step[i])
            for i in attacker_window_info_ids
            if self.target_cache_generation_step[i] >= 0
        ]
        attacker_window_cache_delivery_steps = [
            float(self.target_cache_delivery_step[i])
            for i in attacker_window_info_ids
            if self.target_cache_delivery_step[i] >= 0
        ]
        attacker_window_cache_hop_counts = [
            float(self.target_cache_hop_count[i])
            for i in attacker_window_info_ids
            if self.target_cache_hop_count[i] >= 0
        ]
        direct_window_info_ids = [
            i for i in attacker_window_info_ids if self.detected_by[i] > 0.5
        ]
        comm_window_info_ids = [
            i for i in attacker_window_info_ids if self.target_cache_hop_count[i] > 0
        ]
        return {
            "success": float(self.success),
            "timeout": float(timeout and not self.success and not self.collision and not self.constraint_violation),
            "collision": float(self.collision),
            "constraint_violation": float(self.constraint_violation),
            "mean_range": self._mean_target_range(),
            "min_blue_red_distance": self._min_blue_red_distance(),
            "min_blue_blue_distance": self._min_blue_blue_distance(),
            "tracking_rate": float(np.mean(self.detected_by)),
            "attack_window_rate": float(np.mean(self.attack_window)),
            "attack_geometry_score": self._attack_geometry_score(),
            # P2IA8 instrumentation: exact nonterminal condition used above
            # to advance attack_hold in default (non-v16) task execution.
            # It is logged only; dynamics, reward, success, and termination
            # remain unchanged.
            "chain_support_t": float(
                float(np.max(self.attack_window)) > 0.5
                and float(np.mean(self.detected_by)) > 0.0
                and self._comm_has_chain_to_attacker()
            ),
            "chain_closed": float(self.attack_hold >= self.config.attack_hold_steps),
            "min_success_step": float(self.config.min_success_step),
            "post_loss_chain_reclosure_bonus": float(self.post_loss_chain_reclosure_bonus),
            "post_loss_chain_reclosure_rewarded": float(self.post_loss_chain_reclosure_rewarded),
            "comm_connectivity": self._comm_connectivity(),
            "mean_message_age": self._mean_message_age(),
            "safety_proximity_penalty": self._safety_proximity_penalty(),
            "communication_range_scale": float(self.config.communication_range_scale),
            "strict_target_sensing": float(self.config.strict_target_sensing),
            "agent_target_info_bottleneck": float(self.config.agent_target_info_bottleneck),
            "target_estimate_age": float(self.step_count - self.last_detection_step) if self.last_detection_step >= 0 else float(self.config.max_steps),
            "target_estimate_is_prior": float(self.config.strict_target_sensing and self.last_detected_target_pos is None),
            "target_cache_age_mean": float(np.mean(local_cache_ages)),
            "target_cache_confidence_mean": float(np.mean(local_cache_conf)),
            "target_cache_stale_rate": self._target_cache_stale_rate(),
            "attacker_has_fresh_target_info": float(bool(fresh_attacker_ids)),
            "attacker_target_cache_generation_step_max": max(attacker_cache_generation_steps) if attacker_cache_generation_steps else -1.0,
            "attacker_target_cache_delivery_step_max": max(attacker_cache_delivery_steps) if attacker_cache_delivery_steps else -1.0,
            "attacker_info_attack_window": float(bool(attacker_window_info_ids)),
            "attacker_window_cache_generation_step_max": max(attacker_window_cache_generation_steps) if attacker_window_cache_generation_steps else -1.0,
            "attacker_window_cache_delivery_step_max": max(attacker_window_cache_delivery_steps) if attacker_window_cache_delivery_steps else -1.0,
            "attacker_window_cache_hop_count_min": min(attacker_window_cache_hop_counts) if attacker_window_cache_hop_counts else -1.0,
            "attacker_window_direct_info": float(bool(direct_window_info_ids)),
            "attacker_window_comm_info": float(bool(comm_window_info_ids)),
            "node_failure_active": float(any(self._is_comm_failed(i) for i in range(self.config.num_blue))),
            "failed_blue_agent": float(self.config.failed_blue_agent),
            "step": float(self.step_count),
        }

    def _target_state_for_observation(self) -> tuple[np.ndarray, float, float, float, np.ndarray]:
        if not self.config.strict_target_sensing:
            vel = velocity_from_state(self.red_speed[0], self.red_heading[0], self.red_gamma[0])
            return self.red_pos[0], float(self.red_speed[0]), float(self.red_heading[0]), float(self.red_gamma[0]), vel
        return self._estimated_target_state()

    def _target_state_for_graph_observation(self) -> tuple[np.ndarray, float, float, float, np.ndarray]:
        if not (self.config.strict_target_sensing and self.config.agent_target_info_bottleneck):
            return self._target_state_for_observation()
        # Actor graph observations are shared by all blue actors. Under the
        # strict target-information bottleneck, any target state in the shared
        # graph would leak a scout's private detection to agents that have not
        # received a delivered message. Target information is therefore carried
        # only by per-agent observations/caches, while the graph target node is
        # zero-masked.
        pos = np.zeros(3, dtype=np.float32)
        vel = np.zeros(3, dtype=np.float32)
        return pos, 0.0, 0.0, 0.0, vel

    def _target_state_for_agent_observation(self, agent_id: int) -> tuple[np.ndarray, float, float, float, np.ndarray]:
        if (
            self.config.strict_target_sensing
            and self.config.agent_target_info_bottleneck
            and self._has_fresh_target_cache(agent_id)
        ):
            pos = self.target_cache_pos[agent_id]
            vel = self.target_cache_vel[agent_id]
            speed = float(np.linalg.norm(vel))
            if speed <= 1e-6:
                return pos, 0.0, 0.0, 0.0, vel.astype(np.float32)
            heading = math.atan2(float(vel[1]), float(vel[0]))
            gamma = math.atan2(float(vel[2]), float(np.linalg.norm(vel[:2]) + 1e-6))
            return pos, speed, heading, gamma, vel.astype(np.float32)
        if (
            not self.config.strict_target_sensing
            or not self.config.agent_target_info_bottleneck
            or self._has_target_information(agent_id)
        ):
            return self._target_state_for_observation()
        pos = np.zeros(3, dtype=np.float32)
        vel = np.zeros(3, dtype=np.float32)
        return pos, 0.0, 0.0, 0.0, vel

    def _estimated_target_state(self) -> tuple[np.ndarray, float, float, float, np.ndarray]:
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
        for i, typ in enumerate(self.config.blue_types):
            target_visible = (
                not self.config.strict_target_sensing
                or not self.config.agent_target_info_bottleneck
                or self._has_target_information(i)
            )
            target_est, _, _, _, red_vel = self._target_state_for_agent_observation(i)
            if target_visible:
                rel = target_est - self.blue_pos[i]
                target_range_norm = float(np.linalg.norm(rel)) / self.config.world_radius
            else:
                rel = np.zeros(3, dtype=np.float32)
                red_vel = np.zeros(3, dtype=np.float32)
                target_range_norm = 0.0
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
                    target_range_norm,
                    red_vel[0] / typ.max_speed,
                    red_vel[1] / typ.max_speed,
                    red_vel[2] / typ.max_speed,
                    vel[0] / typ.max_speed,
                    vel[1] / typ.max_speed,
                    vel[2] / typ.max_speed,
                    self.detected_by[i],
                    self.local_attack_window[i],
                    self.blue_energy[i],
                    typ.radar_range / self.config.world_radius,
                    typ.comm_range * self.config.communication_range_scale / self.config.world_radius,
                    typ.attack_range_max / self.config.world_radius,
                    float(typ.role == ROLE_SCOUT),
                    float(typ.role == ROLE_RELAY),
                    float(typ.role == ROLE_ATTACKER),
                    float(typ.role == ROLE_INTERCEPTOR),
                    self._local_inbound_connectivity(i),
                    self._local_inbound_message_age(i) / self.config.max_steps,
                    self._local_target_cache_age(i) / self.config.max_steps,
                    self._local_target_cache_confidence(i),
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

        target_pos, target_speed, target_heading, target_gamma, target_vel = self._target_state_for_graph_observation()
        positions = np.vstack([self.blue_pos, target_pos[None, :]])
        speeds = np.concatenate([self.blue_speed, np.asarray([target_speed], dtype=np.float32)])
        headings = np.concatenate([self.blue_heading, np.asarray([target_heading], dtype=np.float32)])
        gammas = np.concatenate([self.blue_gamma, np.asarray([target_gamma], dtype=np.float32)])
        roles = [typ.role for typ in self.config.blue_types] + [ROLE_TARGET]
        max_speeds = [typ.max_speed for typ in self.config.blue_types] + [self.config.target_type.max_speed]
        graph_target_masked = self.config.strict_target_sensing and self.config.agent_target_info_bottleneck

        for i in range(n):
            vel = velocity_from_state(speeds[i], headings[i], gammas[i])
            role[i] = roles[i]
            target_detection_flag = 0.0 if graph_target_masked else float(np.any(self.detected_by))
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
                    self.detected_by[i] if i < n_blue else target_detection_flag,
                    self.local_attack_window[i] if i < n_blue else 0.0,
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
                # Graph convention: A[receiver, sender] = 1. Task-support
                # edges gate delivered communication messages; they are not an
                # independent information channel.
                support = float(i < n_blue and j < n_blue and self._support_edge(j, i))
                active_support = float(i < n_blue and j < n_blue and self._active_support_edge(j, i))
                if self.config.graph_relation_ablation == "no_task_support":
                    support = 0.0
                    active_support = 0.0
                # Local attack-window is exposed as a node feature and may
                # activate task-support between blue agents; it must not open a
                # hidden fourth channel in the union graph.
                attack = 0.0
                age = 0.0
                if i < n_blue and j < n_blue:
                    age = self.message_age[i, j] / self.config.max_steps
                confidence = max(sensing, max(0.0, 1.0 - age))
                adj[i, j] = max(adj[i, j], sensing, comm, active_support)
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
        if self._has_fresh_target_cache(agent_id):
            return True
        return False

    def _active_support_edge(self, src: int, dst: int) -> bool:
        """Return whether a role-compatible edge currently serves the kill chain."""
        if not self._support_edge(src, dst):
            return False
        if self.comm_adj[dst, src] <= 0.5:
            return False
        src_role = self.config.blue_types[src].role
        if src_role == ROLE_SCOUT:
            return self._has_target_information(src)
        if src_role == ROLE_RELAY:
            return self._has_target_information(src)
        if src_role in {ROLE_ATTACKER, ROLE_INTERCEPTOR}:
            return bool(self.local_attack_window[src] > 0.5)
        return False

    def _write_target_cache(
        self,
        agent_id: int,
        *,
        pos: np.ndarray,
        vel: np.ndarray,
        source: int,
        generation_step: int,
        delivery_step: int,
        hop_count: int,
        confidence: float,
        path: list[int],
    ) -> None:
        current_generation = int(self.target_cache_generation_step[agent_id])
        current_hops = int(self.target_cache_hop_count[agent_id])
        if (
            self.target_cache_valid[agent_id] > 0.5
            and generation_step < current_generation
        ):
            return
        if (
            self.target_cache_valid[agent_id] > 0.5
            and generation_step == current_generation
            and current_hops >= 0
            and hop_count > current_hops
        ):
            return
        self.target_cache_valid[agent_id] = 1.0
        self.target_cache_pos[agent_id] = np.asarray(pos, dtype=np.float32)
        self.target_cache_vel[agent_id] = np.asarray(vel, dtype=np.float32)
        self.target_cache_source[agent_id] = int(source)
        self.target_cache_generation_step[agent_id] = int(generation_step)
        self.target_cache_delivery_step[agent_id] = int(delivery_step)
        self.target_cache_hop_count[agent_id] = int(hop_count)
        self.target_cache_confidence[agent_id] = float(confidence)
        self.target_cache_path[agent_id] = list(path)


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
