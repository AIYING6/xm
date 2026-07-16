from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Mapping, Sequence

import numpy as np


@dataclass(frozen=True)
class LAGAgentState:
    pos_neu: np.ndarray
    vel_neu: np.ndarray
    body_vel: np.ndarray
    attitude: np.ndarray
    role: int
    alive: float = 1.0
    agent_id: str = ""


def _as_vec3(value: Sequence[float] | np.ndarray, name: str) -> np.ndarray:
    arr = np.asarray(value, dtype=np.float32).reshape(-1)
    if arr.size < 3:
        raise ValueError(f"{name} must contain at least three values, got shape={arr.shape}")
    return arr[:3].astype(np.float32)


def _unit(v: np.ndarray, eps: float = 1e-8) -> np.ndarray:
    norm = float(np.linalg.norm(v))
    if norm < eps:
        return np.zeros_like(v, dtype=np.float32)
    return (v / norm).astype(np.float32)


def build_lag_role_graph(
    states: Sequence[LAGAgentState],
    comm_radius: float,
    pos_scale: float = 10000.0,
    vel_scale: float = 340.0,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Build EA-RG-MAPPO-S style graph tensors from aircraft kinematics.

    Node feature dim = 15:
    altitude, sin/cos roll, sin/cos pitch, sin/cos heading,
    NEU velocity, body velocity, alive flag, role.

    Edge feature dim = 13:
    relative NEU position, range, range/communication radius,
    line-of-sight vector, relative NEU velocity, same-team flag,
    communication reachability flag.
    """
    n = len(states)
    node_feat = np.zeros((n, 15), dtype=np.float32)
    edge_feat = np.zeros((n, n, 13), dtype=np.float32)
    adj = np.zeros((n, n), dtype=np.float32)
    role = np.asarray([s.role for s in states], dtype=np.int64)

    for i, state in enumerate(states):
        roll, pitch, heading = _as_vec3(state.attitude, "attitude")
        pos = _as_vec3(state.pos_neu, "pos_neu")
        vel = _as_vec3(state.vel_neu, "vel_neu")
        body = _as_vec3(state.body_vel, "body_vel")
        node_feat[i] = np.asarray(
            [
                pos[2] / pos_scale,
                math.sin(float(roll)),
                math.cos(float(roll)),
                math.sin(float(pitch)),
                math.cos(float(pitch)),
                math.sin(float(heading)),
                math.cos(float(heading)),
                vel[0] / vel_scale,
                vel[1] / vel_scale,
                vel[2] / vel_scale,
                body[0] / vel_scale,
                body[1] / vel_scale,
                body[2] / vel_scale,
                float(state.alive),
                float(state.role),
            ],
            dtype=np.float32,
        )

    for i, src in enumerate(states):
        src_pos = _as_vec3(src.pos_neu, "src.pos_neu")
        src_vel = _as_vec3(src.vel_neu, "src.vel_neu")
        for j, dst in enumerate(states):
            dst_pos = _as_vec3(dst.pos_neu, "dst.pos_neu")
            dst_vel = _as_vec3(dst.vel_neu, "dst.vel_neu")
            rel_pos = dst_pos - src_pos
            rel_vel = dst_vel - src_vel
            dist = float(np.linalg.norm(rel_pos))
            los = _unit(rel_pos)
            same_team = float(src.role == dst.role)
            reachable = float(i == j or (same_team > 0.5 and dist <= comm_radius))
            enemy_observable = float(src.role != dst.role)
            adj[i, j] = max(reachable, enemy_observable)
            edge_feat[i, j] = np.asarray(
                [
                    rel_pos[0] / pos_scale,
                    rel_pos[1] / pos_scale,
                    rel_pos[2] / pos_scale,
                    dist / pos_scale,
                    dist / max(comm_radius, 1e-6),
                    los[0],
                    los[1],
                    los[2],
                    rel_vel[0] / vel_scale,
                    rel_vel[1] / vel_scale,
                    rel_vel[2] / vel_scale,
                    same_team,
                    reachable,
                ],
                dtype=np.float32,
            )
    return node_feat, edge_feat, adj, role


def _sim_alive(sim: object) -> float:
    value = getattr(sim, "is_alive", True)
    if callable(value):
        value = value()
    return float(bool(value))


def _body_velocity_from_sim(sim: object, fallback_vel: np.ndarray, state_var: object = None) -> np.ndarray:
    getter = getattr(sim, "get_property_values", None)
    if state_var is None:
        state_var = getattr(sim, "state_var", None)
    if callable(getter) and state_var is not None:
        try:
            raw = np.asarray(getter(state_var), dtype=np.float32).reshape(-1)
            if raw.size >= 12:
                return raw[9:12].astype(np.float32)
        except Exception:
            pass
    return fallback_vel.astype(np.float32)


def states_from_lag_env(env: object) -> list[LAGAgentState]:
    """Extract role-graph states from a LAG-like environment.

    The function is intentionally duck-typed so it can be tested without
    importing JSBSim. A real LAG env is expected to expose `agents`, `ego_ids`,
    `enm_ids`, and each simulator should expose position/velocity/attitude
    getters.
    """
    agents: Mapping[str, object] = getattr(env, "agents")
    ego_ids = set(getattr(env, "ego_ids", []))
    enm_ids = set(getattr(env, "enm_ids", []))
    task_state_var = getattr(getattr(env, "task", None), "state_var", None)
    agent_ids = list(agents.keys())[: int(getattr(env, "num_agents", len(agents)))]
    states: list[LAGAgentState] = []
    for agent_id in agent_ids:
        sim = agents[agent_id]
        pos = _as_vec3(sim.get_position(), f"{agent_id}.position")
        vel = _as_vec3(sim.get_velocity(), f"{agent_id}.velocity")
        attitude = _as_vec3(sim.get_rpy(), f"{agent_id}.rpy")
        role = 0 if agent_id in ego_ids else 1 if agent_id in enm_ids else int(agent_id[0] != agent_ids[0][0])
        states.append(
            LAGAgentState(
                pos_neu=pos,
                vel_neu=vel,
                body_vel=_body_velocity_from_sim(sim, vel, task_state_var),
                attitude=attitude,
                role=role,
                alive=_sim_alive(sim),
                agent_id=agent_id,
            )
        )
    return states
