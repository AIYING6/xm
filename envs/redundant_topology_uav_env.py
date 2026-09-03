"""Configuration-driven redundant-topology UAV environment.

P1 purpose: deterministic semantic acceptance only.  This module deliberately
contains no learner, optimizer, curriculum, policy scoring, or evaluation tape.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from copy import deepcopy
import hashlib
import json
from math import comb
from typing import Any, Iterable

import numpy as np

ROLE_SCOUT = 0
ROLE_RELAY = 1
ROLE_TERMINAL = 2
ROLE_NAMES = ("scout", "relay", "terminal")


@dataclass(frozen=True)
class RedundantTopologyConfig:
    """All scale differences are expressed by counts, never an N-specific rule."""

    scouts: int
    relays: int
    terminals: int
    objectives: int | None = None
    dt: float = 1.0
    deadline_steps: int = 48
    scout_sense_range: float = 120.0
    relay_radio_range: float = 55.0
    terminal_speed: float = 10.0
    collision_radius: float = 1.0
    boundary: float = 160.0
    tau_max: int = 5
    comm_dropout: float = 0.0
    reward_progress_weight: float = 1.0
    reward_completion_weight: float = 1.0
    reward_collision_weight: float = 1.0
    reward_boundary_weight: float = 1.0
    seed_env: int = 20260902
    seed_comm: int = 20260903
    seed_topology: int = 20260904
    assignment_observation: bool = False
    scout_assignment_observation: bool = False

    def __post_init__(self) -> None:
        if min(self.scouts, self.relays, self.terminals) < 1:
            raise ValueError("each functional role requires at least one instance")
        if self.objectives is not None and self.objectives != self.terminals:
            raise ValueError("P0.5 freezes objectives == terminal count")
        if self.tau_max < 1 or self.deadline_steps < 2:
            raise ValueError("invalid physical timing contract")
        if not 0.0 <= self.comm_dropout < 1.0:
            raise ValueError("comm_dropout must be in [0, 1)")
        if self.scout_assignment_observation and not self.assignment_observation:
            raise ValueError("scout assignment observation requires the shared assignment append block")

    @property
    def num_agents(self) -> int:
        return self.scouts + self.relays + self.terminals

    @property
    def num_objectives(self) -> int:
        return self.terminals if self.objectives is None else self.objectives

    @property
    def roles(self) -> np.ndarray:
        return np.asarray(
            [ROLE_SCOUT] * self.scouts + [ROLE_RELAY] * self.relays + [ROLE_TERMINAL] * self.terminals,
            dtype=np.int64,
        )


def scale_config(scale: str, **overrides: Any) -> RedundantTopologyConfig:
    family = {"small": (1, 2, 1), "main": (2, 2, 2), "large": (2, 3, 3)}
    if scale not in family:
        raise ValueError(f"unknown semantic scale: {scale}")
    scouts, relays, terminals = family[scale]
    return RedundantTopologyConfig(scouts=scouts, relays=relays, terminals=terminals, **overrides)


class RedundantTopologyUAVEnv:
    """A deterministic, information-legal objective-support environment.

    Actor action values are 0 (idle) or 1..K (sense/attempt that objective).
    Relay actions are ignored; forwarding is a frozen network operation, not a
    privileged policy action.  `force_failure_mask` is trainer/test-only and is
    never included in actor observations.
    """

    runtime_format = "redundant_topology_uav_runtime_v1"

    def __init__(self, config: RedundantTopologyConfig):
        self.config = config
        self.roles = config.roles
        self.n = config.num_agents
        self.k = config.num_objectives
        self.scout_ids = np.flatnonzero(self.roles == ROLE_SCOUT)
        self.relay_ids = np.flatnonzero(self.roles == ROLE_RELAY)
        self.terminal_ids = np.flatnonzero(self.roles == ROLE_TERMINAL)
        self.action_dim = self.k + 1
        # The legacy/default interface remains byte-for-byte shape-compatible.
        # P2.8 appends K terminal-only preference values only when explicitly enabled.
        self.obs_dim = 8 + 3 * self.k + (self.k if config.assignment_observation else 0)
        self.share_obs_dim = self.n * 2 + self.k * 3 + self.n * self.n
        self._init_rngs()
        self.reset()

    def _init_rngs(self) -> None:
        self.rng_env = np.random.default_rng(self.config.seed_env)
        self.rng_comm = np.random.default_rng(self.config.seed_comm)
        self.rng_topology = np.random.default_rng(self.config.seed_topology)

    @staticmethod
    def _spaced(count: int, x: float, width: float = 20.0) -> np.ndarray:
        ys = np.asarray([0.0], dtype=np.float32) if count == 1 else np.linspace(-width / 2, width / 2, count, dtype=np.float32)
        return np.stack([np.full(count, x, dtype=np.float32), ys], axis=1)

    def _initial_positions(self) -> np.ndarray:
        return np.concatenate((self._spaced(self.config.scouts, 0.0), self._spaced(self.config.relays, 35.0), self._spaced(self.config.terminals, 70.0)), axis=0)

    def _objective_positions(self) -> np.ndarray:
        return self._spaced(self.k, 90.0)

    def legal_edges(self) -> set[tuple[int, int]]:
        return {(int(s), int(r)) for s in self.scout_ids for r in self.relay_ids} | {(int(r), int(t)) for r in self.relay_ids for t in self.terminal_ids}

    def reset(self, seed_env: int | None = None) -> tuple[np.ndarray, np.ndarray, dict[str, np.ndarray]]:
        if seed_env is not None:
            self.config = RedundantTopologyConfig(**{**asdict(self.config), "seed_env": int(seed_env)})
            self._init_rngs()
        self.step_count = 0
        self.done = False
        self.positions = self._initial_positions()
        self.objective_positions = self._objective_positions()
        self.objective_progress = np.zeros(self.k, dtype=np.float32)
        self.completed = np.zeros(self.k, dtype=bool)
        self.failure_mask: set[tuple[int, int]] = set()
        self.failed_nodes: set[int] = set()
        self.caches: list[dict[int, dict[str, Any]]] = [dict() for _ in range(self.n)]
        self.last_active = np.zeros((self.n, self.n), dtype=np.int8)
        # Stable lane-derived preference: a role-local symmetry-breaking cue.
        # It is deliberately computed from frozen initial geometry, not from
        # faults, future state, reward, training seed, or an evaluation tape.
        terminal_order = self.terminal_ids[np.argsort(self.positions[self.terminal_ids, 1])]
        scout_order = self.scout_ids[np.argsort(self.positions[self.scout_ids, 1])]
        objective_order = np.argsort(self.objective_positions[:, 1])
        self.terminal_assignment = {int(terminal): int(objective) for terminal, objective in zip(terminal_order, objective_order)}
        self.scout_assignment = {int(scout): int(objective) for scout, objective in zip(scout_order, objective_order)}
        self.event_log: list[dict[str, Any]] = []
        self.recovery_times: dict[str, int | None] = {"failure": None, "route": None, "message": None, "task": None}
        return self.actor_observation(), self.critic_observation(), self.graph_observation()

    def set_failure(self, edges: Iterable[tuple[int, int]] = (), nodes: Iterable[int] = ()) -> None:
        legal = self.legal_edges()
        self.failed_nodes = set(map(int, nodes))
        masked = set(map(tuple, edges))
        masked |= {edge for edge in legal if edge[0] in self.failed_nodes or edge[1] in self.failed_nodes}
        if not masked <= legal:
            raise ValueError("failure mask contains an illegal task edge")
        self.failure_mask = masked
        self.recovery_times["failure"] = self.step_count
        self.event_log.append({"event": "failure", "step": self.step_count, "edges": sorted(masked)})

    def task_adjacency(self, faulted: bool = True) -> np.ndarray:
        adj = np.zeros((self.n, self.n), dtype=np.int8)  # receiver, sender
        blocked = self.failure_mask if faulted else set()
        for src, dst in self.legal_edges() - blocked:
            adj[dst, src] = 1
        return adj

    def radio_adjacency(self) -> np.ndarray:
        adj = np.zeros((self.n, self.n), dtype=np.int8)
        for src, dst in self.legal_edges():
            distance = float(np.linalg.norm(self.positions[src] - self.positions[dst]))
            radio_ok = distance <= self.config.relay_radio_range and self.rng_comm.random() >= self.config.comm_dropout
            adj[dst, src] = int(radio_ok)
        return adj

    def active_adjacency(self) -> np.ndarray:
        return self.task_adjacency(faulted=True) * self.radio_adjacency()

    def graph_signature(self) -> dict[str, Any]:
        active = {(src, dst) for src, dst in self.legal_edges() if (src, dst) not in self.failure_mask}
        paths = [(int(s), int(r), int(t)) for s in self.scout_ids for r in self.relay_ids for t in self.terminal_ids if (int(s), int(r)) in active and (int(r), int(t)) in active]
        pair = [[sum(x[0] == int(s) and x[2] == int(t) for x in paths) for t in self.terminal_ids] for s in self.scout_ids]
        return {"edge_set": sorted(active), "total_legal_paths": len(paths), "paths_per_pair": pair,
                "reachable_pairs": int(sum(value > 0 for row in pair for value in row)),
                "terminal_coverage": int(sum(any(pair[i][j] > 0 for i in range(len(self.scout_ids))) for j in range(len(self.terminal_ids)))),
                "relay_node_disjoint_max": int(max((max(row) for row in pair), default=0)),
                "has_legal_route": bool(paths), "cut_set": not bool(paths)}

    def _fresh_token(self, terminal: int, objective: int) -> dict[str, Any] | None:
        token = self.caches[terminal].get(objective)
        if token is None:
            return None
        token["age"] = self.step_count - token["t_sense"]
        valid = token["age"] <= self.config.tau_max and token["valid"]
        return token if valid else None

    def support_action_mask(self, terminal: int) -> np.ndarray:
        mask = np.zeros(self.action_dim, dtype=np.int8); mask[0] = 1
        if self.roles[terminal] != ROLE_TERMINAL or terminal in self.failed_nodes:
            return mask
        for objective in range(self.k):
            mask[objective + 1] = int(not self.completed[objective] and self._fresh_token(terminal, objective) is not None)
        return mask

    def _sense_and_route(self, actions: np.ndarray, active: np.ndarray) -> list[dict[str, Any]]:
        packets: list[dict[str, Any]] = []
        for scout in self.scout_ids:
            action = int(actions[scout])
            if scout in self.failed_nodes or action == 0 or action > self.k:
                continue
            objective = action - 1
            if np.linalg.norm(self.positions[scout] - self.objective_positions[objective]) > self.config.scout_sense_range:
                continue
            packets.append({"objective_id": objective, "estimated_target_state": self.objective_positions[objective].copy(),
                            "source_scout": int(scout), "t_sense": self.step_count, "valid": True})
        delivered: list[dict[str, Any]] = []
        # This occurs after the structural mask/radio graph has already been built.
        for packet in packets:
            scout = packet["source_scout"]
            for relay in self.relay_ids:
                if not active[relay, scout]:
                    continue
                for terminal in self.terminal_ids:
                    if not active[terminal, relay]:
                        continue
                    msg = {**packet, "relay_id": int(relay), "route": (int(scout), int(relay), int(terminal)),
                           "t_receive": self.step_count, "age": 0}
                    previous = self.caches[terminal].get(packet["objective_id"])
                    if previous is None or (msg["t_sense"], -msg["source_scout"], -msg["relay_id"]) >= (previous["t_sense"], -previous["source_scout"], -previous["relay_id"]):
                        self.caches[terminal][packet["objective_id"]] = msg
                    delivered.append(msg)
        if delivered and self.recovery_times["message"] is None and self.recovery_times["failure"] is not None:
            self.recovery_times["message"] = self.step_count
        return delivered

    def _move_terminals(self, actions: np.ndarray) -> None:
        for terminal in self.terminal_ids:
            action = int(actions[terminal])
            if terminal in self.failed_nodes or action == 0 or action > self.k:
                continue
            objective = action - 1
            token = self._fresh_token(int(terminal), objective)
            if token is None or self.completed[objective]:
                continue
            delta = self.objective_positions[objective] - self.positions[terminal]
            distance = float(np.linalg.norm(delta))
            if distance > 0:
                self.positions[terminal] += delta * min(1.0, self.config.terminal_speed * self.config.dt / distance)
            if np.linalg.norm(self.objective_positions[objective] - self.positions[terminal]) <= 1.0:
                self.completed[objective] = True
                self.objective_progress[objective] = 1.0
                self.event_log.append({"event": "objective_complete", "step": self.step_count, "objective": objective, "terminal": int(terminal), "route": token["route"]})
                if self.recovery_times["failure"] is not None and self.recovery_times["task"] is None:
                    self.recovery_times["task"] = self.step_count

    def _collision_metrics(self) -> tuple[float, bool]:
        pairs = [np.linalg.norm(self.positions[i] - self.positions[j]) < self.config.collision_radius for i in range(self.n) for j in range(i + 1, self.n)]
        return (float(sum(pairs) / comb(self.n, 2)), bool(any(pairs)))

    def reward_from_components(self, progress_delta: float, newly_completed: int, collision_pairs: int, boundary_cost: float = 0.0) -> float:
        collision = collision_pairs / comb(self.n, 2)
        return (self.config.reward_progress_weight * progress_delta + self.config.reward_completion_weight * (newly_completed / self.k)
                - self.config.reward_collision_weight * collision - self.config.reward_boundary_weight * boundary_cost)

    def step(self, actions: np.ndarray | list[int]) -> tuple[np.ndarray, np.ndarray, dict[str, np.ndarray], np.ndarray, np.ndarray, dict[str, Any]]:
        if self.done:
            raise RuntimeError("reset required after terminal episode")
        actions = np.asarray(actions, dtype=np.int64).reshape(self.n)
        actions = np.clip(actions, 0, self.action_dim - 1)
        prior = float(self.objective_progress.mean())
        self.step_count += 1
        # Frozen failure ordering: fault -> task graph -> radio -> active -> packets/cache -> obs/actions/dynamics.
        radio = self.radio_adjacency()
        active = self.task_adjacency(faulted=True) * radio
        if self.recovery_times["failure"] is not None and self.recovery_times["route"] is None and bool(active.any()):
            self.recovery_times["route"] = self.step_count
        delivered = self._sense_and_route(actions, active)
        before_complete = int(self.completed.sum())
        self._move_terminals(actions)
        collision_pair, collision_any = self._collision_metrics()
        boundary_cost = float(np.mean(np.maximum(np.abs(self.positions) - self.config.boundary, 0.0)) / self.config.boundary)
        timeout = self.step_count >= self.config.deadline_steps
        success = bool(self.completed.all())
        self.done = success or timeout
        reward = self.reward_from_components(float(self.objective_progress.mean()) - prior, int(self.completed.sum()) - before_complete, int(round(collision_pair * comb(self.n, 2))), boundary_cost)
        info = {"success": success, "timeout": timeout, "collision_pair": collision_pair, "collision_any": collision_any,
                "delivered": deepcopy(delivered), "signature": self.graph_signature(), "recovery": deepcopy(self.recovery_times),
                "task_adj": self.task_adjacency(True), "radio_adj": radio, "active_adj": active}
        self.last_active = active
        self.last_radio = radio
        self.event_log.append({"event": "step", "step": self.step_count, "reward": reward, "collision_pair": collision_pair})
        rewards = np.full((self.n, 1), reward, dtype=np.float32)
        dones = np.full((self.n, 1), self.done, dtype=np.float32)
        return self.actor_observation(), self.critic_observation(), self.graph_observation(), rewards, dones, info

    def actor_observation(self) -> np.ndarray:
        obs = np.zeros((self.n, self.obs_dim), dtype=np.float32)
        base_dim = 8 + 3 * self.k
        for agent in range(self.n):
            obs[agent, :2] = self.positions[agent] / self.config.boundary
            obs[agent, 2 + self.roles[agent]] = 1.0
            if self.roles[agent] == ROLE_TERMINAL:
                for objective in range(self.k):
                    token = self._fresh_token(agent, objective)
                    obs[agent, 5 + objective] = float(token is not None and not self.completed[objective])
                    base = 5 + self.k + 2 * objective
                    if token is not None:
                        obs[agent, base:base + 2] = token["estimated_target_state"] / self.config.boundary
                obs[agent, base_dim - 1] = float(sum(self._fresh_token(agent, k) is not None for k in range(self.k))) / self.k
                if self.config.assignment_observation:
                    obs[agent, base_dim + self.terminal_assignment[agent]] = 1.0
            elif self.roles[agent] == ROLE_SCOUT and self.config.scout_assignment_observation:
                obs[agent, base_dim + self.scout_assignment[agent]] = 1.0
        return obs

    def critic_observation(self) -> np.ndarray:
        return np.concatenate((self.positions.reshape(-1) / self.config.boundary, self.objective_positions.reshape(-1) / self.config.boundary,
                               self.objective_progress, self.task_adjacency(True).reshape(-1))).astype(np.float32)

    def graph_observation(self) -> dict[str, np.ndarray]:
        return {"node_features": self.actor_observation(), "task_adj": self.task_adjacency(True), "active_adj": self.last_active.copy(),
                "roles": self.roles.copy(), "action_masks": np.stack([self.support_action_mask(i) if self.roles[i] == ROLE_TERMINAL else np.ones(self.action_dim, dtype=np.int8) for i in range(self.n)])}

    def runtime_state_dict(self) -> dict[str, Any]:
        attrs = {name: deepcopy(value) for name, value in self.__dict__.items() if not name.startswith("rng_")}
        return {"format": self.runtime_format, "attributes": attrs, "rng_env": deepcopy(self.rng_env.bit_generator.state), "rng_comm": deepcopy(self.rng_comm.bit_generator.state), "rng_topology": deepcopy(self.rng_topology.bit_generator.state)}

    def load_runtime_state_dict(self, state: dict[str, Any]) -> None:
        if state.get("format") != self.runtime_format:
            raise ValueError("unsupported runtime state")
        self.__dict__.clear(); self.__dict__.update(deepcopy(state["attributes"]))
        for name in ("rng_env", "rng_comm", "rng_topology"):
            rng = np.random.default_rng(); rng.bit_generator.state = deepcopy(state[name]); setattr(self, name, rng)

    def telemetry_records(self) -> dict[str, Any]:
        return {"summary": {"steps": self.step_count, "completed": self.completed.astype(int).tolist(), "signature": self.graph_signature()},
                "event_window": deepcopy(self.event_log[-16:]), "full_trajectory": {"positions": self.positions.tolist(), "caches": deepcopy(self.caches), "recovery": deepcopy(self.recovery_times)}}


class TrainingDistributionInterface:
    """Non-learning fairness API shared by future training-distribution methods."""
    def __init__(self, training_support: tuple[str, ...]): self.training_support = tuple(training_support)
    def sample_task(self, task_id: str) -> str:
        if task_id not in self.training_support: raise ValueError("task outside frozen training support")
        return task_id
    def observe_training_signal(self, signal: float) -> float: return float(signal)
    def update_distribution(self, _: Any) -> None: return None


def interface_spec(config: RedundantTopologyConfig) -> dict[str, int]:
    env = RedundantTopologyUAVEnv(config)
    return {"num_agents": env.n, "obs_dim": env.obs_dim, "critic_dim": env.share_obs_dim, "action_dim": env.action_dim, "role_embedding_dim": 3}
