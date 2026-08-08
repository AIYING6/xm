# p3b_oracle_feasibility.py — P3-B algorithm-independent feasibility calibration.
#
# The oracle is a CENTRALIZED GEOMETRIC / MPC-STYLE controller (no learning):
#   - For each blue agent it enumerates the 27 discrete actions, simulates one
#     step under the SAME env physics, and picks the action minimizing a
#     hand-coded cost that encodes the mission geometry:
#       * attacker: keep distance in the attack annulus [min,max], align LOS
#         heading to the target, align altitude, keep closure positive;
#       * scout: keep target in radar (steer to LOS), stay in relay comm range;
#       * relay: hold the scout-attacker midpoint to keep the chain bridged.
#   - It reads ONLY env geometry / communication parameters (positions,
#     headings, comm ranges, attack annulus, radar FOV). It NEVER reads any
#     learned policy / checkpoint / Full-MAPPO-HAPPO-Wider result.
#
# Nominal qualification (frozen intent): P_aw(oracle, nominal) >= 0.9 and
# P_success(oracle, nominal) >= 0.8. Until that passes, this probe is not yet
# qualified as a feasibility oracle for P3-B cell selection.
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from algorithms.ri_gmappo.simple_ri_gmappo import RIGMAPPOConfig, make_env  # noqa: E402
from envs.uav_intercept_3d_env import ACTION3D_TABLE, angle_diff, velocity_from_state  # noqa: E402
from scripts.p3a_ood_cells import EVAL_BASE_SEED, FAILURE_DURATION, FAILURE_START, HORIZON  # noqa: E402

ROLE_SCOUT, ROLE_RELAY, ROLE_ATTACKER, ROLE_INTERCEPTOR = 0, 1, 2, 3


def _ic_target_estimate(env, i: int):
    """Information-constrained target estimate for agent i.

    Uses ONLY agent i's legal observation / communication cache:
      - direct radar detection this step -> true target state;
      - fresh cache (own or relayed)      -> cached pos/vel extrapolated;
      - stale cache                      -> constant-velocity extrapolation
                                            from own last cache;
      - no info ever                     -> target prior (constant).
    NEVER falls back to env.red_pos when the agent has no legal information.
    Returns (pos_est, has_new_info).
    """
    cfg = env.config
    if env.detected_by[i] > 0.5:
        return env.red_pos[0].astype(np.float64), True
    if env._has_fresh_target_cache(i):
        pos = env.target_cache_pos[i].astype(np.float64)
        vel = env.target_cache_vel[i].astype(np.float64)
        age = max(0, env.step_count - int(env.target_cache_generation_step[i]))
        return pos + vel * age * cfg.dt, True
    if env.target_cache_valid[i] > 0.5 and env.target_cache_generation_step[i] >= 0:
        pos = env.target_cache_pos[i].astype(np.float64)
        vel = env.target_cache_vel[i].astype(np.float64)
        age = max(0, env.step_count - int(env.target_cache_generation_step[i]))
        return pos + vel * age * cfg.dt, False
    return np.asarray(cfg.target_prior_position, dtype=np.float64), False


def _cost_after_action(env, i: int, action: int, use_ic: bool = False) -> float:
    """Cost for agent i if it executes `action` for one step (geometric MPC).

    Uses env physics from the CURRENT state; no mutation of env. With
    use_ic=True, the target reference for the cost is the information-
    constrained estimate for agent i (never the true target when the agent has
    no legal information).
    """
    typ = env.config.blue_types[i]
    role = typ.role
    h = float(env.blue_heading[i])
    g = float(env.blue_gamma[i])
    s = float(env.blue_speed[i])
    pos = env.blue_pos[i].copy()
    turn_cmd, climb_cmd, accel_cmd = ACTION3D_TABLE[int(action)]
    h2 = (h + turn_cmd * typ.max_turn_rate * env.config.dt) % (2.0 * np.pi)
    g2 = float(np.clip(g + climb_cmd * 0.35 * typ.max_gamma * env.config.dt, -typ.max_gamma, typ.max_gamma))
    s2 = float(np.clip(s + accel_cmd * typ.max_accel * env.config.dt, typ.min_speed, typ.max_speed))
    vel = velocity_from_state(s2, h2, g2)
    pos2 = pos + vel * env.config.dt

    if use_ic:
        tgt, _has = _ic_target_estimate(env, i)
    else:
        tgt = env.red_pos[0]
    rel = tgt - pos2
    dist = float(np.linalg.norm(rel))

    if role in (ROLE_ATTACKER, ROLE_INTERCEPTOR):
        # attack-window geometry cost
        # distance: penalize outside annulus, soft target = mid of annulus
        dmid = 0.5 * (typ.attack_range_min + typ.attack_range_max)
        d_cost = abs(dist - dmid) / max(dmid, 1.0)
        los_h = float(np.arctan2(rel[1], rel[0]))
        heading_err = abs(angle_diff(los_h, h2))
        h_cost = heading_err / max(typ.attack_cone, 1e-6)
        alt_err = abs(float(rel[2]))
        a_cost = alt_err / 1_600.0
        # closure: prefer closing
        red_vel = velocity_from_state(env.red_speed[0], env.red_heading[0], env.red_gamma[0])
        rel_u = rel / max(dist, 1e-6)
        closure = float(np.dot(vel - red_vel, rel_u))
        c_cost = max(0.0, -closure) / 100.0
        return 3.0 * h_cost + 2.0 * a_cost + 1.5 * d_cost + 0.5 * c_cost

    if role == ROLE_SCOUT:
        # keep target in radar cone: align LOS heading, penalize altitude gap
        los_h = float(np.arctan2(rel[1], rel[0]))
        heading_err = abs(angle_diff(los_h, h2))
        h_cost = heading_err / max(typ.radar_fov_h * 0.5, 1e-6)
        alt_err = abs(float(rel[2]))
        a_cost = alt_err / 3_000.0
        return 3.0 * h_cost + 1.0 * a_cost

    # relay: hold midpoint between scout(0) and attacker(2); keep chain bridged
    scout_id = [j for j, t in enumerate(env.config.blue_types) if t.role == ROLE_SCOUT]
    att_id = [j for j, t in enumerate(env.config.blue_types) if t.role in (ROLE_ATTACKER, ROLE_INTERCEPTOR)]
    target_mid = None
    if scout_id and att_id:
        target_mid = 0.5 * (env.blue_pos[scout_id[0]] + env.blue_pos[att_id[0]])
    if target_mid is None:
        target_mid = tgt
    rel_m = target_mid - pos2
    d_mid = float(np.linalg.norm(rel_m))
    los_m = float(np.arctan2(rel_m[1], rel_m[0]))
    heading_err = abs(angle_diff(los_m, h2))
    h_cost = heading_err / max(typ.comm_range / 30_000.0, 1e-6)
    a_cost = abs(float(rel_m[2])) / 3_000.0
    return 3.0 * h_cost + 1.5 * a_cost + 0.5 * (d_mid / max(typ.comm_range, 1.0))


def oracle_action(env, i: int, use_ic: bool = False) -> int:
    """Centralized geometric MPC: pick the discrete action with min cost."""
    best_a = 0
    best_c = 1e18
    for a in range(ACTION3D_TABLE.shape[0]):
        c = _cost_after_action(env, i, a, use_ic=use_ic)
        if c < best_c:
            best_c = c
            best_a = a
    return best_a


def run_cell(cfg_overrides: dict, seed: int, n_ep: int, use_ic: bool = False) -> dict:
    from scripts.p3a_ood_cells import common_eval_overrides
    over = common_eval_overrides()
    over.update(cfg_overrides)
    cfg = RIGMAPPOConfig(
        env_name="3d_intercept", seed=seed, eval_episodes=n_ep,
        target_policy=over.get("target_policy", "straight"),
        communication_range_scale=over.get("communication_range_scale", 1.0),
        communication_dropout_prob=0.3, message_delay_steps=2,
        radar_dropout_prob=0.0, strict_target_sensing=True,
        agent_target_info_bottleneck=True, target_prior_position=(0.0, 0.0, 0.0),
        max_target_message_age_steps=40, min_target_confidence=0.0,
        failed_blue_agent=over.get("failed_blue_agent", 1),
        node_failure_start_step=over.get("node_failure_start_step", FAILURE_START),
        node_failure_duration_steps=over.get("node_failure_duration_steps", FAILURE_DURATION),
        attack_hold_steps=4, min_success_step=0,
        graph_encoder="multi_relation", graph_relation_ablation="none",
        graph_message_ablation="none", graph_input_ablation="none", device="cpu",
        blue_init_rotation_deg=over.get("blue_init_rotation_deg", 0.0),
        blue_init_spacing_scale=over.get("blue_init_spacing_scale", 1.0),
        target_init_range_scale=over.get("target_init_range_scale", 1.0),
        target_init_bearing_offset_deg=over.get("target_init_bearing_offset_deg", 0.0),
        comm_topology_mode=over.get("comm_topology_mode", "none"),
    )
    aw_total = 0
    vis_total = 0
    success_total = 0
    for ep in range(n_ep):
        env = make_env(cfg, EVAL_BASE_SEED + ep, training=False)
        obs, so, g = env.reset()
        aw_any = False
        vis_any = False
        for _ in range(HORIZON):
            vis_any = vis_any or bool(np.any(env.detected_by > 0.5))
            aw_any = aw_any or bool(np.any(env.attack_window > 0.5))
            acts = np.array([oracle_action(env, i, use_ic=use_ic) for i in range(env.num_agents)], dtype=np.int64)
            obs, so, g, rew, done, info = env.step(acts)
            if np.all(done):
                break
        aw_total += int(aw_any)
        vis_total += int(vis_any)
        success_total += int(float(info.get("success", 0.0)) > 0.5)
    return {
        "n": n_ep,
        "attack_window_achieved_rate": aw_total / n_ep,
        "target_visible_rate": vis_total / n_ep,
        "success_rate": success_total / n_ep,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cells", nargs="*", default=["G1", "G2", "M1", "M2", "C1", "C2", "J1"])
    parser.add_argument("--overrides", default=None, help="optional json {cell: {field: val}}")
    parser.add_argument("--n-ep", type=int, default=40)
    parser.add_argument("--seed", type=int, default=EVAL_BASE_SEED)
    parser.add_argument("--out", default="docs/statistics/p3a_ood_results_v1_1/p3b_oracle_feasibility.csv")
    parser.add_argument("--nominal", action="store_true", help="run pure nominal qualification only")
    parser.add_argument("--ic", action="store_true", help="use information-constrained MPC oracle")
    args = parser.parse_args()

    from scripts.p3a_ood_cells import cell_overrides
    if args.nominal:
        cell_cfg = {"nominal": {}}
    else:
        cell_cfg = {c: cell_overrides(c) for c in args.cells}
    if args.overrides:
        extra = json.loads(args.overrides)
        for c, ov in extra.items():
            cell_cfg.setdefault(c, {}).update(ov)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for c, ov in cell_cfg.items():
        r = run_cell(ov, args.seed, args.n_ep, use_ic=args.ic)
        row = {"cell": c, "n": r["n"], "attack_window_achieved_rate": f"{r['attack_window_achieved_rate']:.4f}",
               "target_visible_rate": f"{r['target_visible_rate']:.4f}", "success_rate": f"{r['success_rate']:.4f}",
               "overrides": str(ov)}
        rows.append(row)
        print(f"{c}: aw={r['attack_window_achieved_rate']:.3f} vis={r['target_visible_rate']:.3f} "
              f"success={r['success_rate']:.3f}", flush=True)
    with out.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
