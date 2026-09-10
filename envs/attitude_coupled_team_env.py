"""P19 trainable environment: three-agent relay chain under attitude coupling.

Chain S -> R -> K.  Each agent has ONE nose carrying a body-fixed radar (limited
half field of view) and a body-fixed directional link (limited half angle).  Each
agent therefore faces a two-duty heading conflict:

    S : look at the target   vs  face R
    R : face S               vs  face K
    K : face R               vs  look at the target

A hop only works when BOTH endpoints face each other on the SAME step, so the team
must synchronise its alternating windows.  Each agent observes only its own two
relative bearings, its own freshness flag and (in the clock arm) a shared mission
clock; it never observes a teammate's heading.

This environment exists to test whether the coupling, already validated for a
single agent in P18, remains load bearing when it becomes a coordination problem.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np


TURN_ACTIONS = (-1, 0, 1)


@dataclass
class TeamCoupledConfig:
    radar_half_fov_deg: float = 65.0
    link_half_angle_deg: float = 45.0
    turn_limit_deg_per_step: float = 15.0
    cache_ttl_steps: int = 8
    horizon_steps: int = 60
    chain_spacing: float = 2.0
    chain_bend_min_deg: float = 100.0
    chain_bend_max_deg: float = 140.0
    # P20: make the geometry policy dependent.  Agents fly forward along their
    # heading, so pointing decisions move the very bearings that must be pointed
    # at.  A clock-only schedule can no longer be optimal because the same clock
    # time corresponds to different geometry depending on what the team did.
    agent_speed: float = 0.0
    target_speed: float = 0.0
    link_range: float = 1.0e9
    include_clock: bool = True
    seed: int | None = None


@dataclass
class AttitudeCoupledTeamEnv:
    config: TeamCoupledConfig = field(default_factory=TeamCoupledConfig)

    def __post_init__(self) -> None:
        cfg = self.config
        self.half_fov = math.radians(cfg.radar_half_fov_deg)
        self.half_link = math.radians(cfg.link_half_angle_deg)
        self.turn = math.radians(cfg.turn_limit_deg_per_step)
        self.ttl = cfg.cache_ttl_steps
        self.n_agents = 3
        self.num_agents = 3
        self.num_roles = 3
        self.action_dim = len(TURN_ACTIONS)
        self.obs_dim = 6
        self.share_obs_dim = 6
        self.rng = np.random.default_rng(cfg.seed)
        self.role_ids = np.asarray([0, 1, 2], dtype=np.int64)
        self.reset()

    def seed(self, seed: int) -> None:
        self.rng = np.random.default_rng(seed)

    def set_clock_arm(self, include_clock: bool) -> None:
        self.config.include_clock = include_clock

    @staticmethod
    def _wrap(a):
        return (a + math.pi) % (2.0 * math.pi) - math.pi

    def reset(self):
        cfg = self.config
        self.step_count = 0
        orientation = float(self.rng.uniform(0.0, 2.0 * math.pi))
        # Bend the chain at the relay so that R's two duties are 40-80 deg apart
        # instead of a full 180 deg reversal.  Facing S and facing K then costs
        # 3-6 turns rather than 12, which is what makes the pipeline physically
        # completable inside the cache TTL.
        bend = math.radians(float(self.rng.uniform(cfg.chain_bend_min_deg, cfg.chain_bend_max_deg)))
        leg0 = np.asarray([math.cos(orientation), math.sin(orientation)])
        leg1 = np.asarray([math.cos(orientation + bend), math.sin(orientation + bend)])
        s_pos = np.zeros(2)
        r_pos = s_pos + leg0 * cfg.chain_spacing
        k_pos = r_pos + leg1 * cfg.chain_spacing
        self.positions = np.stack([s_pos, r_pos, k_pos])
        self.chain_bend = bend
        t_bearing = float(self.rng.uniform(0.0, 2.0 * math.pi))
        t_dist = float(self.rng.uniform(2.0, 5.0))
        self.target = self.positions[0] + np.asarray(
            [math.cos(t_bearing) * t_dist, math.sin(t_bearing) * t_dist]
        )
        t_vel_dir = float(self.rng.uniform(0.0, 2.0 * math.pi))
        self.target_vel = cfg.target_speed * np.asarray(
            [math.cos(t_vel_dir), math.sin(t_vel_dir)]
        )
        self.headings = self.rng.uniform(0.0, 2.0 * math.pi, self.n_agents)
        self.ages = np.full(self.n_agents, self.ttl + 1, dtype=int)
        self.score = 0
        self.done = False
        obs = self._obs()
        return obs, obs.copy(), self._graph()

    def _bearing(self, a: int, b: int) -> float:
        d = self.positions[b] - self.positions[a]
        return math.atan2(d[1], d[0])

    def _bearing_to_point(self, a: int, point: np.ndarray) -> float:
        d = point - self.positions[a]
        return math.atan2(d[1], d[0])

    def _duty_bearings(self):
        """Duty A and duty B bearing for each agent."""
        s_to_t = self._bearing_to_point(0, self.target)
        k_to_t = self._bearing_to_point(2, self.target)
        return (
            (s_to_t, self._bearing(0, 1)),   # S: target, R
            (self._bearing(1, 0), self._bearing(1, 2)),  # R: S, K
            (self._bearing(2, 1), k_to_t),   # K: R, target
        )

    def _in_range(self, i: int, j: int) -> bool:
        return float(np.linalg.norm(self.positions[j] - self.positions[i])) <= self.config.link_range

    def _facing_link(self, i: int, j: int) -> bool:
        if not self._in_range(i, j):
            return False
        return abs(self._wrap(self._bearing(i, j) - self.headings[i])) <= self.half_link

    def _sees_target(self, i: int) -> bool:
        return abs(self._wrap(self._bearing_to_point(i, self.target) - self.headings[i])) <= self.half_fov

    def _obs(self) -> np.ndarray:
        cfg = self.config
        duties = self._duty_bearings()
        out = np.zeros((self.n_agents, self.obs_dim), dtype=np.float32)
        fresh = (self.ages <= self.ttl).astype(np.float32)
        for i in range(self.n_agents):
            a, b = duties[i]
            ra = self._wrap(a - self.headings[i])
            rb = self._wrap(b - self.headings[i])
            values = [math.sin(ra), math.cos(ra), math.sin(rb), math.cos(rb), fresh[i]]
            values.append(self.step_count / cfg.horizon_steps if cfg.include_clock else 0.0)
            out[i] = np.asarray(values, dtype=np.float32)
        return out

    def _graph(self) -> dict:
        n = self.n_agents
        adj = np.zeros((n, n), dtype=np.float32)
        for i in range(n - 1):
            adj[i, i + 1] = 1.0
            adj[i + 1, i] = 1.0
        edge = np.zeros((n, n, 1), dtype=np.float32)
        rel = np.zeros((n, n, 1), dtype=np.float32)
        return {
            "node_feat": np.zeros((n, self.obs_dim), dtype=np.float32),
            "edge_feat": edge,
            "adj": adj,
            "relation_adj": rel,
            "role": self.role_ids.copy(),
            "intent_label": np.zeros(n, dtype=np.int64),
            "has_intent_label": False,
        }

    def step(self, actions):
        if self.done:
            raise RuntimeError("episode finished; call reset()")
        cfg = self.config
        acts = np.asarray(actions).reshape(-1)
        for i in range(self.n_agents):
            self.headings[i] = self._wrap(self.headings[i] + TURN_ACTIONS[int(acts[i])] * self.turn)

        # P20: the nose also drives the airframe, so pointing changes the geometry
        # that the next pointing decision has to satisfy.
        if cfg.agent_speed > 0.0:
            for i in range(self.n_agents):
                self.positions[i] = self.positions[i] + cfg.agent_speed * np.asarray(
                    [math.cos(self.headings[i]), math.sin(self.headings[i])]
                )
        if cfg.target_speed > 0.0:
            self.target = self.target + self.target_vel

        # hop 0: S detects the target
        if self._sees_target(0):
            self.ages[0] = 0
        else:
            self.ages[0] = min(self.ages[0] + 1, self.ttl + 1)

        # hop 1: S -> R, needs both ends aligned AND fresh info at S
        if self._facing_link(0, 1) and self._facing_link(1, 0) and self.ages[0] <= self.ttl:
            self.ages[1] = 0
        else:
            self.ages[1] = min(self.ages[1] + 1, self.ttl + 1)

        # hop 2: R -> K
        if self._facing_link(1, 2) and self._facing_link(2, 1) and self.ages[1] <= self.ttl:
            self.ages[2] = 0
        else:
            self.ages[2] = min(self.ages[2] + 1, self.ttl + 1)

        # mission score: K holds fresh information and its nose is on the target
        reward = 0.0
        if self.ages[2] <= self.ttl and self._sees_target(2):
            reward = 1.0
            self.score += 1

        self.step_count += 1
        self.done = self.step_count >= cfg.horizon_steps
        obs = self._obs()
        graph = self._graph()
        graph["node_feat"] = obs.copy()
        info = {"score": float(self.score), "timeout": float(self.done)}
        return (
            obs,
            obs.copy(),
            graph,
            np.full(self.n_agents, reward, dtype=np.float32),
            np.full(self.n_agents, float(self.done), dtype=np.float32),
            info,
        )
