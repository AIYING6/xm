"""G0-only 3-versus-2 UAV asset-defense environment with primitive 3DOF control."""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np

from envs.uav_intercept_3d_env import (
    ACTION3D_TABLE, ROLE_ATTACKER, UAVIntercept3DConfig, UAVIntercept3DEnv,
    angle_diff, unit, velocity_from_state, wrap_angle,
)


@dataclass(frozen=True)
class MultiThreatAssetDefenseConfig:
    horizon: int = 190
    branch_step: int = 28
    asset_x: float = -8_000.0
    asset_lateral: float = 7_500.0
    asset_strike_radius: float = 1_200.0
    red_initial_lateral: float = 2_400.0
    red_center_y: float = 0.0
    mirror_y: bool = False
    seed: int = 0


class MultiThreatAssetDefenseEnv:
    """Defend two assets from two independently moving red attackers.

    Each red attacker is assigned a distinct asset only after the public
    approach phase. The assignment minimizes physical blue coverage subject to
    one attacker per asset. Neither actor nor critic receives an assignment
    label before that event; observations contain only legal current geometry.
    """

    num_agents = 3
    action_dim = len(ACTION3D_TABLE)

    def __init__(self, config: MultiThreatAssetDefenseConfig | None = None):
        self.config = config or MultiThreatAssetDefenseConfig()
        self.rng = np.random.default_rng(self.config.seed)
        self.base = UAVIntercept3DEnv(UAVIntercept3DConfig(
            max_steps=self.config.horizon, strict_target_sensing=True,
            agent_target_info_bottleneck=True, relay_dependent_task=True,
            target_policy="straight", seed=self.config.seed,
        ))
        self.reset()

    def seed(self, seed: int) -> None:
        self.rng = np.random.default_rng(seed)

    def _asset(self, sign: int) -> np.ndarray:
        return np.asarray((self.config.asset_x, sign * self.config.asset_lateral, 5_000.0), dtype=np.float32)

    def reset(self):
        self.base.seed(int(self.rng.integers(0, 2**31 - 1)))
        self.base.reset()
        if self.config.mirror_y:
            # A complete geometric reflection preserves each vehicle's role
            # and dynamics while removing the incidental lower/upper bias of
            # the legacy initial formation and headings.
            self.base.blue_pos[:, 1] *= -1.0
            self.base.blue_heading[:] = -self.base.blue_heading
        self.base.step_count = 0
        self.base.done = False
        self.blue_destroyed = np.zeros(2, dtype=bool)
        self.asset_integrity = {-1: 1.0, 1: 1.0}
        self.route_assignment: tuple[int, int] | None = None
        self.red_pos = np.asarray(((11_000.0, self.config.red_center_y - self.config.red_initial_lateral, 5_000.0), (11_000.0, self.config.red_center_y + self.config.red_initial_lateral, 5_000.0)), dtype=np.float32)
        self.red_heading = np.asarray((math.pi, math.pi), dtype=np.float32)
        self.red_gamma = np.zeros(2, dtype=np.float32)
        self.red_speed = np.asarray((220.0, 220.0), dtype=np.float32)
        self._sync_base_target(0)
        self.base._update_sensing_and_comm()
        return self._obs(), self._share_obs(), self._graph()

    def _sync_base_target(self, index: int) -> None:
        """Reuse blue-to-blue communication dynamics; target cache is not used as
        a privileged source for the two-threat observations below."""
        self.base.red_pos[0] = self.red_pos[index]
        self.base.red_heading[0] = self.red_heading[index]
        self.base.red_gamma[0] = self.red_gamma[index]
        self.base.red_speed[0] = self.red_speed[index]

    def _visible(self, agent: int, threat: int) -> bool:
        typ = self.base.config.blue_types[agent]
        rel = self.red_pos[threat] - self.base.blue_pos[agent]
        distance = float(np.linalg.norm(rel))
        if distance > typ.radar_range:
            return False
        azimuth = math.atan2(float(rel[1]), float(rel[0]))
        elevation = math.atan2(float(rel[2]), float(np.linalg.norm(rel[:2]) + 1e-6))
        return abs(angle_diff(azimuth, float(self.base.blue_heading[agent]))) <= typ.radar_fov_h * 0.5 and abs(elevation - float(self.base.blue_gamma[agent])) <= typ.radar_fov_v * 0.5

    def _coverage(self, asset: np.ndarray) -> float:
        distances = np.linalg.norm(self.base.blue_pos - asset[None, :], axis=1)
        return float(np.sum(np.exp(-distances / 7_000.0)))

    def _assign_routes(self) -> None:
        # The pair must attack different assets.  The lower total coverage
        # matching is selected, with a seeded tie break.
        neg, pos = self._asset(-1), self._asset(1)
        cneg, cpos = self._coverage(neg), self._coverage(pos)
        if math.isclose(cneg, cpos, abs_tol=1e-8):
            self.route_assignment = (-1, 1) if self.rng.random() < 0.5 else (1, -1)
        elif cneg < cpos:
            self.route_assignment = (-1, 1)
        else:
            self.route_assignment = (1, -1)
        self.red_speed[:] = self.base.config.target_type.max_speed

    def _move_red(self, threat: int) -> None:
        if self.route_assignment is None:
            target = np.asarray((4_000.0, self.config.red_center_y + (-1 if threat == 0 else 1) * self.config.red_initial_lateral, 5_000.0), dtype=np.float32)
        else:
            target = self._asset(self.route_assignment[threat])
        delta = target - self.red_pos[threat]
        desired = math.atan2(float(delta[1]), float(delta[0]))
        typ = self.base.config.target_type
        turn = float(np.clip(angle_diff(desired, float(self.red_heading[threat])), -typ.max_turn_rate, typ.max_turn_rate))
        climb = float(np.clip(delta[2] / 1_500.0, -1.0, 1.0))
        self.red_heading[threat] = wrap_angle(float(self.red_heading[threat]) + turn * self.base.config.dt)
        self.red_gamma[threat] = float(np.clip(self.red_gamma[threat] + climb * 0.25 * typ.max_gamma * self.base.config.dt, -typ.max_gamma, typ.max_gamma))
        self.red_pos[threat] += velocity_from_state(float(self.red_speed[threat]), float(self.red_heading[threat]), float(self.red_gamma[threat])) * self.base.config.dt

    def _attack_window(self, threat: int) -> bool:
        attacker = next(i for i, typ in enumerate(self.base.config.blue_types) if typ.role == ROLE_ATTACKER)
        typ = self.base.config.blue_types[attacker]
        rel = self.red_pos[threat] - self.base.blue_pos[attacker]
        distance = float(np.linalg.norm(rel))
        if not typ.attack_range_min <= distance <= typ.attack_range_max:
            return False
        los = math.atan2(float(rel[1]), float(rel[0]))
        if abs(angle_diff(los, float(self.base.blue_heading[attacker]))) > typ.attack_cone or abs(float(rel[2])) > 1_600.0:
            return False
        blue_vel = velocity_from_state(float(self.base.blue_speed[attacker]), float(self.base.blue_heading[attacker]), float(self.base.blue_gamma[attacker]))
        red_vel = velocity_from_state(float(self.red_speed[threat]), float(self.red_heading[threat]), float(self.red_gamma[threat]))
        return float(np.dot(blue_vel - red_vel, unit(rel))) > -30.0 and any(self._visible(i, threat) for i in range(self.num_agents))

    def step(self, actions: np.ndarray | list[int]):
        if self.base.done:
            raise RuntimeError("Call reset() before stepping a finished episode.")
        actions = np.asarray(actions, dtype=np.int64).reshape(self.num_agents)
        self.base.step_count += 1
        self.base._move_blue(np.clip(actions, 0, self.action_dim - 1))
        if self.route_assignment is None and self.base.step_count >= self.config.branch_step:
            self._assign_routes()
        for threat in range(2):
            if not self.blue_destroyed[threat]:
                self._move_red(threat)
                if self._attack_window(threat):
                    self.blue_destroyed[threat] = True
        self._sync_base_target(0)
        self.base._update_sensing_and_comm()
        breach = False
        if self.route_assignment is not None:
            for threat, asset_sign in enumerate(self.route_assignment):
                if not self.blue_destroyed[threat] and np.linalg.norm(self.red_pos[threat] - self._asset(asset_sign)) <= self.config.asset_strike_radius:
                    self.asset_integrity[asset_sign] = 0.0
                    breach = True
        defense_success = bool(self.blue_destroyed.all())
        collision = self.base._has_collision()
        constraint = self.base._has_constraint_violation()
        timeout = self.base.step_count >= self.config.horizon
        self.base.done = bool(defense_success or breach or collision or constraint or timeout)
        rewards = np.full((self.num_agents, 1), 1.5 if defense_success else (-1.0 if breach else -0.005), dtype=np.float32)
        dones = np.full((self.num_agents, 1), self.base.done, dtype=np.float32)
        info: dict[str, Any] = {
            "defense_success": float(defense_success), "asset_breach": float(breach),
            "neutralized_threats": float(self.blue_destroyed.sum()), "route_committed": float(self.route_assignment is not None),
            "timeout": float(timeout and not defense_success and not breach and not collision and not constraint),
            "collision": float(collision), "constraint_violation": float(constraint),
            "primitive_action_interface": "3dof_27_discrete",
        }
        return self._obs(), self._share_obs(), self._graph(), rewards, dones, info

    def _obs(self) -> np.ndarray:
        rows = []
        for agent, typ in enumerate(self.base.config.blue_types):
            own = np.concatenate((
                self.base.blue_pos[agent] / self.base.config.world_radius,
                [
                    self.base.blue_speed[agent] / typ.max_speed,
                    self.base.blue_energy[agent],
                    np.sin(self.base.blue_heading[agent]),
                    np.cos(self.base.blue_heading[agent]),
                ],
            ))
            threats: list[float] = []
            for threat in range(2):
                visible = self._visible(agent, threat)
                rel = (self.red_pos[threat] - self.base.blue_pos[agent]) / self.base.config.world_radius if visible else np.zeros(3, dtype=np.float32)
                threats.extend((*rel.tolist(), float(visible)))
            role = np.zeros(3, dtype=np.float32); role[agent] = 1.0
            rows.append(np.asarray([*own, *threats, *role, self.base.step_count / self.config.horizon], dtype=np.float32))
        return np.stack(rows)

    def _share_obs(self) -> np.ndarray:
        # No future route label is supplied.  At G0, central state includes
        # current physical positions only; route selection is encoded in motion.
        state = np.concatenate((self.base.blue_pos.flatten(), self.red_pos.flatten(), [self.base.step_count / self.config.horizon])).astype(np.float32)
        return np.tile(state[None, :], (self.num_agents, 1))

    def _graph(self) -> dict[str, np.ndarray]:
        return {"node_features": self._obs(), "active_adj": self.base.comm_adj.astype(np.int8), "action_masks": np.ones((self.num_agents, self.action_dim), dtype=np.int8)}
