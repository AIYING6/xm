"""P18 trainable environment: attitude-coupled sensing and relaying.

One UAV carries a body-fixed radar (limited half field of view) and a body-fixed
directional link to a relay (limited half angle, rear-hemisphere blockage).  It
must keep a fresh target cache by pointing the nose at the target, and it must
hand that fresh information to the relay by pointing the nose at the relay.
There is one nose, a finite turn rate and a finite cache TTL.

This environment exists because P16 measured the conflict and P17 showed that
hand-written rules leave a large gap to the dynamic-programming oracle.  The
question here is whether a learned policy closes that gap.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np


TURN_ACTIONS = (-1, 0, 1)


@dataclass
class AttitudeCoupledRelayConfig:
    radar_half_fov_deg: float = 65.0
    link_half_angle_deg: float = 45.0
    turn_limit_deg_per_step: float = 5.0
    cache_ttl_steps: int = 8
    horizon_steps: int = 60
    initial_heading_deg: float = 0.0
    separation_min_deg: float = 10.0
    separation_max_deg: float = 180.0
    seed: int | None = None
    # P25 motion block.  All default to the stationary P18/P22 behaviour, so every
    # earlier result is reproduced bit for bit unless a config turns them on.  With
    # motion on, the nose also drives the airframe: pointing decisions move the very
    # bearings that must be pointed at, so the optimal duty cycle becomes time varying
    # and no fixed schedule can stay optimal.
    agent_speed: float = 0.0
    target_speed: float = 0.0
    target_distance: float = 3.0
    relay_distance: float = 2.0
    link_range: float = 1.0e9


@dataclass
class AttitudeCoupledRelayEnv:
    config: AttitudeCoupledRelayConfig = field(default_factory=AttitudeCoupledRelayConfig)

    def __post_init__(self) -> None:
        cfg = self.config
        self.half_fov = math.radians(cfg.radar_half_fov_deg)
        self.half_link = math.radians(cfg.link_half_angle_deg)
        self.turn = math.radians(cfg.turn_limit_deg_per_step)
        self.ttl = cfg.cache_ttl_steps
        self.action_dim = len(TURN_ACTIONS)
        self.obs_dim = 4
        self.share_obs_dim = 4
        self.num_agents = 1
        self.num_roles = 2
        self.rng = np.random.default_rng(cfg.seed)
        self.reset()

    def seed(self, seed: int) -> None:
        self.rng = np.random.default_rng(seed)

    @staticmethod
    def _wrap(angle: float) -> float:
        return (angle + math.pi) % (2.0 * math.pi) - math.pi

    def reset(self):
        cfg = self.config
        self.step_count = 0
        self.heading = math.radians(cfg.initial_heading_deg)
        separation = math.radians(
            self.rng.uniform(cfg.separation_min_deg, cfg.separation_max_deg)
        )
        self.target_bearing = float(self.rng.uniform(0.0, 2.0 * math.pi))
        sign = 1.0 if self.rng.random() < 0.5 else -1.0
        self.relay_bearing = self._wrap(self.target_bearing + sign * separation)
        self.separation = abs(separation)
        self.cache_age = self.ttl + 1
        self.delivered = 0
        self.done = False
        # geometry as positions, so motion can change the bearings over time
        self.agent_pos = np.zeros(2)
        self.target_pos = cfg.target_distance * np.asarray(
            [math.cos(self.target_bearing), math.sin(self.target_bearing)]
        )
        self.relay_pos = cfg.relay_distance * np.asarray(
            [math.cos(self.relay_bearing), math.sin(self.relay_bearing)]
        )
        tv_dir = float(self.rng.uniform(0.0, 2.0 * math.pi))
        self.target_vel = cfg.target_speed * np.asarray(
            [math.cos(tv_dir), math.sin(tv_dir)]
        )
        obs = self._obs()
        return obs, obs.copy(), self._graph(obs)

    def _obs(self) -> np.ndarray:
        cfg = self.config
        return np.asarray(
            [
                self._wrap(self.target_bearing - self.heading) / math.pi,
                self._wrap(self.relay_bearing - self.heading) / math.pi,
                min(self.cache_age, self.ttl + 1) / (self.ttl + 1),
                self.step_count / cfg.horizon_steps,
            ],
            dtype=np.float32,
        )

    def _graph(self, obs: np.ndarray) -> dict:
        node = obs.reshape(1, -1).astype(np.float32)
        return {
            "node_feat": node,
            "edge_feat": np.zeros((1, 1, 1), dtype=np.float32),
            "adj": np.ones((1, 1), dtype=np.float32),
            "relation_adj": np.ones((1, 1, 1), dtype=np.float32),
            "role": np.asarray([0], dtype=np.int64),
            "intent_label": np.asarray([0], dtype=np.int64),
            "has_intent_label": False,
        }

    def step(self, actions):
        if self.done:
            raise RuntimeError("episode finished; call reset()")
        cfg = self.config
        action = int(np.asarray(actions).reshape(-1)[0])
        self.heading = self._wrap(self.heading + TURN_ACTIONS[action] * self.turn)

        # P25: the nose steers the airframe, so the geometry is policy dependent.
        if cfg.agent_speed > 0.0 or cfg.target_speed > 0.0:
            if cfg.agent_speed > 0.0:
                self.agent_pos = self.agent_pos + cfg.agent_speed * np.asarray(
                    [math.cos(self.heading), math.sin(self.heading)]
                )
            if cfg.target_speed > 0.0:
                self.target_pos = self.target_pos + self.target_vel
            dt = self.target_pos - self.agent_pos
            dr = self.relay_pos - self.agent_pos
            self.target_bearing = float(math.atan2(dt[1], dt[0]))
            self.relay_bearing = float(math.atan2(dr[1], dr[0]))
            self.separation = abs(self._wrap(self.relay_bearing - self.target_bearing))

        if abs(self._wrap(self.target_bearing - self.heading)) <= self.half_fov:
            self.cache_age = 0
        else:
            self.cache_age = min(self.cache_age + 1, self.ttl + 1)

        in_range = bool(np.linalg.norm(self.relay_pos - self.agent_pos) <= cfg.link_range)
        link_up = in_range and abs(self._wrap(self.relay_bearing - self.heading)) <= self.half_link
        reward = 0.0
        if self.cache_age <= self.ttl and link_up:
            self.delivered += 1
            reward = 1.0

        self.step_count += 1
        self.done = self.step_count >= cfg.horizon_steps
        obs = self._obs()
        info = {
            "delivered": float(self.delivered),
            "separation_deg": math.degrees(self.separation),
            "timeout": float(self.done),
        }
        return (
            obs,
            obs.copy(),
            self._graph(obs),
            np.asarray([reward], dtype=np.float32),
            np.asarray([float(self.done)], dtype=np.float32),
            info,
        )
