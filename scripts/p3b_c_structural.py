# p3b_c_structural.py — P3-B communication structural counterfactual metric.
#
# Same-state offline counterfactual: one algorithm-independent qualification
# trajectory (IC-MPC nominal) is recorded (blue positions, direct sensing per
# step); then G_base(t) and G_shift(t) are both built OFFLINE from the SAME
# saved states, so any difference is purely topological.
#
# Metrics (frozen definitions):
#   p_affected : fraction of steps the to-be-perturbed edge exists in base graph
#   p_path_base: fraction of steps a task-relevant directed path exists (base)
#   p_path_shift: fraction of steps such a path exists after perturbation
#   delta_p_path = p_path_base - p_path_shift
#   p_alt       : fraction of steps an ALTERNATE task-relevant directed path
#                 exists after perturbation (graceful degradation, not task death)
#
# Task path: a directed physical communication path from a "source" (a blue node
# with legal direct target information per environment truth) to an
# attacker/interceptor, using env comm rules (range, dropout, delay, failure).
# This is environment-defined and architecture-independent: it does NOT read
# EA-RG graph, Task-Support, MAPPO, or any learned output.
#
# Usage (NOMINAL qualification only; no new C candidates):
#   python scripts/p3b_c_structural.py --nominal
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from algorithms.ri_gmappo.simple_ri_gmappo import RIGMAPPOConfig, make_env  # noqa: E402
from scripts.p3a_ood_cells import EVAL_BASE_SEED, FAILURE_DURATION, FAILURE_START, HORIZON  # noqa: E402

ROLE_SCOUT, ROLE_RELAY, ROLE_ATTACKER = 0, 1, 2


def _cfg(nom: bool):
    over = {}
    if not nom:
        # legacy C1-like symmetric longest-pair prune used only as anchor
        over = {"comm_topology_mode": "symmetric_longest_prune"}
    return RIGMAPPOConfig(
        env_name="3d_intercept", seed=EVAL_BASE_SEED, eval_episodes=1,
        target_policy="straight",
        communication_range_scale=1.0, communication_dropout_prob=0.3,
        message_delay_steps=2, radar_dropout_prob=0.0,
        strict_target_sensing=True, agent_target_info_bottleneck=True,
        target_prior_position=(0.0, 0.0, 0.0),
        max_target_message_age_steps=40, min_target_confidence=0.0,
        failed_blue_agent=1, node_failure_start_step=FAILURE_START,
        node_failure_duration_steps=FAILURE_DURATION, attack_hold_steps=4,
        min_success_step=0, graph_encoder="multi_relation",
        graph_relation_ablation="none", graph_message_ablation="none",
        graph_input_ablation="none", device="cpu",
        comm_topology_mode=over.get("comm_topology_mode", "none"),
    )


def _comm_link_exists(env, a: int, b: int, state: dict, use_shift: bool,
                      prune: list[tuple[int, int]] | None = None) -> bool:
    """Directed physical communication a->b exists at this saved state."""
    # rebuild reachability from the SAVED blue positions (offline counterfactual)
    p_a = state["blue_pos"][a]
    p_b = state["blue_pos"][b]
    rng_scale = env.config.communication_range_scale
    eff = rng_scale * min(env.config.blue_types[a].comm_range,
                          env.config.blue_types[b].comm_range)
    if float(np.linalg.norm(p_a - p_b)) > eff:
        return False
    if env.config.communication_dropout_prob > 0:
        # use the deterministic seed to decide dropout on (a,b) so offline
        # rebuild matches the online draw for the SAME trajectory
        seed = int(env.config.seed) + a * 31 + b * 17 + int(state["step"])
        rng = np.random.default_rng(seed)
        if rng.random() < env.config.communication_dropout_prob:
            return False
    if use_shift:
        # apply the perturbation: remove the designated edge pair
        for (s, r) in prune or []:
            if (s, r) == (a, b):
                return False
    return True


def _has_direct_info(env, i: int, state: dict) -> bool:
    """Legal direct target information for node i (environment truth)."""
    p = state["blue_pos"][i]
    t = state["red_pos"]
    dist = float(np.linalg.norm(p - t))
    typ = env.config.blue_types[i]
    if dist > typ.radar_range:
        return False
    # heading cone check
    los = t - p
    h = float(state["blue_heading"][i])
    los_h = float(np.arctan2(los[1], los[0]))
    from envs.uav_intercept_3d_env import angle_diff
    if abs(angle_diff(los_h, h)) > 0.5 * typ.radar_fov_h:
        return False
    if env.config.radar_dropout_prob > 0:
        seed = int(env.config.seed) + i * 101 + int(state["step"])
        rng = np.random.default_rng(seed)
        if rng.random() < env.config.radar_dropout_prob:
            return False
    return True


def _path_exists(env, state: dict, use_shift: bool,
                 prune: list[tuple[int, int]] | None = None) -> bool:
    """Exists a directed path from any info-source to an attacker."""
    n = env.num_agents
    sources = [i for i in range(n) if _has_direct_info(env, i, state)]
    attackers = [i for i, t in enumerate(env.config.blue_types)
                 if t.role == ROLE_ATTACKER]
    if not sources or not attackers:
        return False
    adj = [[_comm_link_exists(env, a, b, state, use_shift, prune) for b in range(n)]
           for a in range(n)]
    # BFS from sources
    seen = set(sources)
    stack = list(sources)
    while stack:
        u = stack.pop()
        for v in range(n):
            if adj[u][v] and v not in seen:
                seen.add(v)
                stack.append(v)
    return any(att in seen for att in attackers)


def _alt_path_exists(env, state: dict, prune: list[tuple[int, int]] | None = None) -> bool:
    """Alternate path after perturbation: path exists without the pruned edge."""
    return _path_exists(env, state, use_shift=True, prune=prune)


def record_trajectory(env) -> list[dict]:
    """Run the algorithm-independent IC-MPC trajectory on a RESET env and save
    states until episode end (done) or horizon."""
    from scripts.p3b_oracle_feasibility import oracle_action
    env.reset()
    states = []
    done = False
    for t in range(HORIZON):
        states.append({
            "step": t,
            "blue_pos": env.blue_pos.copy(),
            "blue_heading": env.blue_heading.copy(),
            "red_pos": env.red_pos[0].copy(),
        })
        acts = np.array([oracle_action(env, i, use_ic=True) for i in range(env.num_agents)],
                        dtype=np.int64)
        obs, so, g, rew, done, info = env.step(acts)
        if np.all(done):
            break
    return states


def _legacy_longest_pair(states: list[dict]) -> list[tuple[int, int]]:
    """Recompute the legacy 'longest blue-blue XY pair' (C1/C2 anchor) OFFLINE
    from the recorded nominal trajectory's first state, as the env would."""
    if not states:
        return []
    pos = states[0]["blue_pos"]
    best = None
    best_d = -1.0
    n = pos.shape[0]
    for a in range(n):
        for b in range(a + 1, n):
            d = float(np.linalg.norm(pos[a][:2] - pos[b][:2]))
            if d > best_d:
                best_d = d
                best = (a, b)
    if best is None:
        return []
    lo, hi = best
    # symmetric (C1) uses both directions; directed (C2) uses lower-y->higher-y
    if pos[lo][1] <= pos[hi][1]:
        return [(lo, hi), (hi, lo)]
    return [(hi, lo), (lo, hi)]


def nominal_qualification(n_ep: int = 40) -> list[dict]:
    rows = []
    for ep in range(n_ep):
        env = make_env(_cfg(nom=True), EVAL_BASE_SEED + ep, training=False)
        states = record_trajectory(env)
        pr = _legacy_longest_pair(states)
        # aggregate over recorded steps (same-state offline counterfactual)
        pb = [int(_path_exists(env, st, use_shift=False)) for st in states]
        ps = [int(_path_exists(env, st, use_shift=True, prune=pr)) for st in states]
        pa = [int(_alt_path_exists(env, st, prune=pr)) for st in states]
        affected = []
        for st in states:
            for (a, b) in pr:
                affected.append(int(_comm_link_exists(env, a, b, st, use_shift=False)))
        rows.append({
            "episode": ep,
            "steps_recorded": len(states),
            "p_affected": float(np.mean(affected)) if affected else 0.0,
            "p_path_base": float(np.mean(pb)),
            "p_path_shift": float(np.mean(ps)),
            "delta_p_path": float(np.mean(pb)) - float(np.mean(ps)),
            "p_alt": float(np.mean(pa)),
        })
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--nominal", action="store_true", help="nominal structural qualification only")
    parser.add_argument("--n-ep", type=int, default=40)
    parser.add_argument("--out", default="docs/statistics/p3a_ood_results_v1_1/p3b_c_structural_nominal.csv")
    args = parser.parse_args()
    if not args.nominal:
        print("Only --nominal qualification is allowed before protocol freeze.")
        return 1
    rows = nominal_qualification(args.n_ep)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    for r in rows[:5]:
        print(r)
    means = {k: float(np.mean([r[k] for r in rows])) for k in
             ("p_affected", "p_path_base", "p_path_shift", "delta_p_path", "p_alt")}
    print("means:", means)
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
