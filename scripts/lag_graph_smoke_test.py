from __future__ import annotations

import argparse
import csv
import math
import sys
import types
from dataclasses import dataclass
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LAG_ROOT = ROOT.parent / "LAG"


@dataclass
class AgentState:
    pos_neu: np.ndarray
    vel_neu: np.ndarray
    body_vel: np.ndarray
    attitude: np.ndarray
    team: int
    alive: float = 1.0


def _unit(v: np.ndarray, eps: float = 1e-8) -> np.ndarray:
    norm = float(np.linalg.norm(v))
    if norm < eps:
        return np.zeros_like(v, dtype=np.float32)
    return (v / norm).astype(np.float32)


def build_role_graph(
    states: list[AgentState],
    comm_radius: float,
    pos_scale: float = 10000.0,
    vel_scale: float = 340.0,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Build EA-RG-MAPPO-S style graph tensors from aircraft kinematics."""
    n = len(states)
    node_feat = np.zeros((n, 15), dtype=np.float32)
    edge_feat = np.zeros((n, n, 13), dtype=np.float32)
    adj = np.zeros((n, n), dtype=np.float32)
    role = np.array([s.team for s in states], dtype=np.int64)

    for i, s in enumerate(states):
        roll, pitch, heading = s.attitude
        node_feat[i] = np.array(
            [
                s.pos_neu[2] / pos_scale,
                math.sin(roll),
                math.cos(roll),
                math.sin(pitch),
                math.cos(pitch),
                math.sin(heading),
                math.cos(heading),
                s.vel_neu[0] / vel_scale,
                s.vel_neu[1] / vel_scale,
                s.vel_neu[2] / vel_scale,
                s.body_vel[0] / vel_scale,
                s.body_vel[1] / vel_scale,
                s.body_vel[2] / vel_scale,
                s.alive,
                float(s.team),
            ],
            dtype=np.float32,
        )

    for i, src in enumerate(states):
        for j, dst in enumerate(states):
            rel_pos = dst.pos_neu - src.pos_neu
            rel_vel = dst.vel_neu - src.vel_neu
            dist = float(np.linalg.norm(rel_pos))
            los = _unit(rel_pos)
            same_team = float(src.team == dst.team)
            reachable = float(i == j or same_team and dist <= comm_radius)
            enemy_observable = float(src.team != dst.team)
            adj[i, j] = max(reachable, enemy_observable)
            edge_feat[i, j] = np.array(
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


def synthetic_states(step: int) -> list[AgentState]:
    base = [
        (-1200.0, -600.0, 3200.0, 185.0, 18.0, -3.0, 0),
        (-1150.0, 700.0, 3150.0, 178.0, -12.0, 2.0, 0),
        (1100.0, -650.0, 3300.0, -175.0, 10.0, -1.0, 1),
        (1250.0, 600.0, 3250.0, -182.0, -15.0, 1.0, 1),
    ]
    states = []
    for idx, (n, e, u, vn, ve, vu, team) in enumerate(base):
        t = float(step)
        pos = np.array([n + vn * t * 0.25, e + ve * t * 0.25, u + vu * t * 0.25], dtype=np.float32)
        vel = np.array([vn, ve, vu], dtype=np.float32)
        body = np.array([math.sqrt(vn * vn + ve * ve), 0.0, vu], dtype=np.float32)
        heading = math.atan2(ve, vn)
        attitude = np.array([0.03 * math.sin(0.05 * t + idx), 0.02 * math.cos(0.04 * t), heading], dtype=np.float32)
        states.append(AgentState(pos_neu=pos, vel_neu=vel, body_vel=body, attitude=attitude, team=team))
    return states


def lag_states(env) -> list[AgentState]:
    from envs.JSBSim.utils.utils import LLA2NEU

    states: list[AgentState] = []
    agent_ids = list(env.agents.keys())[: env.num_agents]
    team_by_id = {agent_id: 0 if agent_id in env.ego_ids else 1 for agent_id in agent_ids}
    for agent_id in agent_ids:
        sim = env.agents[agent_id]
        raw = np.array(sim.get_property_values(env.task.state_var), dtype=np.float32)
        pos_neu = np.array(LLA2NEU(*raw[:3], env.center_lon, env.center_lat, env.center_alt), dtype=np.float32)
        vel_neu = raw[6:9].astype(np.float32)
        body_vel = raw[9:12].astype(np.float32)
        attitude = raw[3:6].astype(np.float32)
        states.append(
            AgentState(
                pos_neu=pos_neu,
                vel_neu=vel_neu,
                body_vel=body_vel,
                attitude=attitude,
                team=team_by_id[agent_id],
                alive=float(getattr(sim, "is_alive", True)),
            )
        )
    return states


def summarize_graph(step: int, radius: float, node_feat: np.ndarray, edge_feat: np.ndarray, adj: np.ndarray, role: np.ndarray) -> dict[str, float]:
    same_team = role[:, None] == role[None, :]
    not_self = ~np.eye(len(role), dtype=bool)
    team_mask = same_team & not_self
    ranges = edge_feat[:, :, 3]
    return {
        "step": step,
        "comm_radius": radius,
        "nodes": int(node_feat.shape[0]),
        "team_edges": int(np.sum((adj > 0.5) & team_mask)),
        "enemy_edges": int(np.sum((adj > 0.5) & (~same_team))),
        "total_edges": int(np.sum(adj > 0.5)),
        "min_range": float(np.min(ranges[not_self])),
        "max_range": float(np.max(ranges[not_self])),
        "nan_count": int(np.isnan(node_feat).sum() + np.isnan(edge_feat).sum() + np.isnan(adj).sum()),
        "inf_count": int(np.isinf(node_feat).sum() + np.isinf(edge_feat).sum() + np.isinf(adj).sum()),
    }


def run_synthetic(steps: int, radii: list[float]) -> list[dict[str, float]]:
    rows = []
    for step in range(steps):
        states = synthetic_states(step)
        previous_team_edges = -1
        for radius in radii:
            graph = build_role_graph(states, radius)
            row = summarize_graph(step, radius, *graph)
            if row["team_edges"] < previous_team_edges:
                raise AssertionError("team edge count should not decrease as communication radius grows")
            previous_team_edges = row["team_edges"]
            rows.append(row)
    return rows


def run_lag(lag_root: Path, config: str, steps: int, radii: list[float]) -> list[dict[str, float]]:
    sys.path.insert(0, str(lag_root))
    # The copied LAG tree may omit optional human-control task modules, while
    # envs/JSBSim/envs/__init__.py imports them indirectly. Stub them so the
    # MultipleCombat environment can be imported without modifying LAG itself.
    human_pkg = types.ModuleType("envs.JSBSim.human_task")
    freefly_mod = types.ModuleType("envs.JSBSim.human_task.HumanFreeFlyTask")
    single_mod = types.ModuleType("envs.JSBSim.human_task.HumanSingleCombatTask")
    freefly_mod.HumanFreeFlyTask = type("HumanFreeFlyTask", (), {})
    single_mod.HumanSingleCombatTask = type("HumanSingleCombatTask", (), {})
    sys.modules.setdefault("envs.JSBSim.human_task", human_pkg)
    sys.modules.setdefault("envs.JSBSim.human_task.HumanFreeFlyTask", freefly_mod)
    sys.modules.setdefault("envs.JSBSim.human_task.HumanSingleCombatTask", single_mod)
    from envs.JSBSim.envs import MultipleCombatEnv

    env = MultipleCombatEnv(config)
    env.seed(0)
    env.reset()
    rows = []
    try:
        for step in range(steps):
            states = lag_states(env)
            previous_team_edges = -1
            for radius in radii:
                graph = build_role_graph(states, radius)
                row = summarize_graph(step, radius, *graph)
                if row["team_edges"] < previous_team_edges:
                    raise AssertionError("team edge count should not decrease as communication radius grows")
                previous_team_edges = row["team_edges"]
                rows.append(row)
            actions = np.array([env.action_space.sample() for _ in range(env.num_agents)])
            env.step(actions)
    finally:
        env.close()
    return rows


def write_csv(rows: list[dict[str, float]], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Smoke-test EA-RG graph construction for LAG/JSBSim migration.")
    parser.add_argument("--mode", choices=["synthetic", "lag"], default="synthetic")
    parser.add_argument("--lag-root", type=Path, default=DEFAULT_LAG_ROOT)
    parser.add_argument("--lag-config", default="2v2/NoWeapon/HierarchySelfplay")
    parser.add_argument("--steps", type=int, default=100)
    parser.add_argument("--radii", type=float, nargs="+", default=[2000.0, 4000.0, 8000.0, 12000.0])
    parser.add_argument("--out-csv", type=Path, default=ROOT / "results" / "lag_graph_smoke_stats.csv")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        if args.mode == "synthetic":
            rows = run_synthetic(args.steps, args.radii)
        else:
            rows = run_lag(args.lag_root, args.lag_config, args.steps, args.radii)
    except OSError as exc:
        if args.mode == "lag" and "Can't find root directory" in str(exc):
            raise SystemExit(
                "LAG/JSBSim data directory is missing. Expected a JSBSim data root under "
                f"{args.lag_root / 'envs' / 'JSBSim' / 'data'}. "
                "Initialize/copy the LAG JSBSim data submodule before running --mode lag."
            ) from exc
        raise
    write_csv(rows, args.out_csv)
    print(f"wrote {len(rows)} rows to {args.out_csv}")
    print(f"nan_count={sum(row['nan_count'] for row in rows)}, inf_count={sum(row['inf_count'] for row in rows)}")


if __name__ == "__main__":
    main()
