from __future__ import annotations

import argparse
import csv
import math
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.simple_ri_gmappo import RIGMAPPOConfig, make_env  # noqa: E402
from envs.uav_intercept_3d_env import ACTION3D_TABLE, angle_diff, velocity_from_state  # noqa: E402


STEP_COLUMNS = (
    "case",
    "oracle_mode",
    "target_policy",
    "rollout_seed",
    "episode",
    "step",
    "success",
    "timeout",
    "collision",
    "constraint_violation",
    "mean_range",
    "min_blue_red_distance",
    "min_blue_blue_distance",
    "tracking_rate",
    "attack_window_rate",
    "attack_geometry_score",
    "chain_closed",
    "comm_connectivity",
    "mean_message_age",
    "action_0",
    "action_1",
    "action_2",
    "blue0_x",
    "blue0_y",
    "blue0_z",
    "blue1_x",
    "blue1_y",
    "blue1_z",
    "blue2_x",
    "blue2_y",
    "blue2_z",
    "red0_x",
    "red0_y",
    "red0_z",
)

SUMMARY_COLUMNS = (
    "case",
    "oracle_mode",
    "target_policy",
    "episodes",
    "success_rate",
    "timeout_rate",
    "collision_rate",
    "mean_steps",
    "mean_initial_range",
    "mean_final_range",
    "mean_min_range",
    "mean_range_reduction",
    "mean_tracking_rate",
    "mean_attack_window_rate",
    "mean_max_attack_geometry_score",
    "episodes_with_attack_geometry_gt_025",
    "episodes_with_attack_geometry_gt_050",
    "episodes_with_attack_window",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run deterministic geometric-oracle policies in the 3DOF maneuvering-target environment."
    )
    parser.add_argument("--target-policy", action="append", default=None, help="Target policy to evaluate. Can be repeated.")
    parser.add_argument("--oracle-mode", choices=("direct", "lead", "offset"), default="offset")
    parser.add_argument("--episodes", type=int, default=30)
    parser.add_argument("--base-seed", type=int, default=409_000)
    parser.add_argument("--communication-range-scale", type=float, default=1.0)
    parser.add_argument("--communication-dropout-prob", type=float, default=0.0)
    parser.add_argument("--message-delay-steps", type=int, default=0)
    parser.add_argument("--radar-dropout-prob", type=float, default=0.0)
    parser.add_argument("--strict-target-sensing", action="store_true")
    parser.add_argument("--agent-target-info-bottleneck", action="store_true")
    parser.add_argument("--failed-blue-agent", type=int, default=-1)
    parser.add_argument("--node-failure-start-step", type=int, default=0)
    parser.add_argument("--node-failure-duration-steps", type=int, default=0)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "results" / "gate1_geometric_oracle_reachability")
    return parser.parse_args()


def make_config(args: argparse.Namespace, target_policy: str, seed: int) -> RIGMAPPOConfig:
    return RIGMAPPOConfig(
        env_name="3d_intercept",
        seed=seed,
        target_policy=target_policy,
        communication_range_scale=args.communication_range_scale,
        communication_dropout_prob=args.communication_dropout_prob,
        message_delay_steps=args.message_delay_steps,
        radar_dropout_prob=args.radar_dropout_prob,
        strict_target_sensing=args.strict_target_sensing,
        agent_target_info_bottleneck=args.agent_target_info_bottleneck,
        failed_blue_agent=args.failed_blue_agent,
        node_failure_start_step=args.node_failure_start_step,
        node_failure_duration_steps=args.node_failure_duration_steps,
    )


def wrap_angle(angle: float) -> float:
    return (float(angle) + math.pi) % (2.0 * math.pi) - math.pi


def sign_command(value: float, deadband: float) -> float:
    if value > deadband:
        return 1.0
    if value < -deadband:
        return -1.0
    return 0.0


def action_from_setpoints(env, agent_id: int, desired_pos: np.ndarray, desired_speed: float) -> int:
    typ = env.config.blue_types[agent_id]
    rel = desired_pos - env.blue_pos[agent_id]
    desired_heading = math.atan2(float(rel[1]), float(rel[0]))
    heading_error = angle_diff(desired_heading, float(env.blue_heading[agent_id]))
    xy_dist = float(np.linalg.norm(rel[:2]))
    desired_gamma = math.atan2(float(rel[2]), xy_dist + 1e-6)
    gamma_error = desired_gamma - float(env.blue_gamma[agent_id])
    speed_error = float(desired_speed) - float(env.blue_speed[agent_id])

    turn_cmd = sign_command(heading_error, 0.18 * typ.max_turn_rate)
    climb_cmd = sign_command(gamma_error, 0.20 * typ.max_gamma)
    accel_cmd = sign_command(speed_error, 4.0)
    command = np.asarray([turn_cmd, climb_cmd, accel_cmd], dtype=np.float32)
    distances = np.linalg.norm(ACTION3D_TABLE - command[None, :], axis=1)
    return int(np.argmin(distances))


def oracle_actions(env, mode: str) -> np.ndarray:
    red_pos = env.red_pos[0].astype(np.float32)
    red_vel = velocity_from_state(float(env.red_speed[0]), float(env.red_heading[0]), float(env.red_gamma[0]))
    red_xy_vel = red_vel[:2]
    red_xy_speed = float(np.linalg.norm(red_xy_vel))
    red_dir_xy = red_xy_vel / red_xy_speed if red_xy_speed > 1e-6 else np.asarray([1.0, 0.0], dtype=np.float32)
    lateral_xy = np.asarray([-red_dir_xy[1], red_dir_xy[0]], dtype=np.float32)

    actions = np.zeros(env.config.num_blue, dtype=np.int64)
    for i, typ in enumerate(env.config.blue_types):
        rel = red_pos - env.blue_pos[i]
        dist = float(np.linalg.norm(rel))
        lead_time = float(np.clip(dist / max(float(env.blue_speed[i]), 1.0), 8.0, 55.0))
        lead_pos = red_pos + red_vel * lead_time

        if mode == "direct":
            desired_pos = red_pos
        elif mode == "lead":
            desired_pos = lead_pos
        else:
            side = -1.0 if i == 0 else 1.0
            if typ.role == 2:
                trail = 3_800.0 if dist > 7_000.0 else 2_400.0
                desired_pos = lead_pos - np.r_[red_dir_xy * trail, 0.0]
            elif typ.role == 1:
                desired_pos = 0.55 * env.blue_pos[2] + 0.45 * env.blue_pos[0]
                desired_pos[2] = 5_100.0
            else:
                desired_pos = red_pos + np.r_[lateral_xy * side * 3_800.0, 500.0]

        if typ.role == 2 and dist <= typ.attack_range_max:
            desired_pos = red_pos
        desired_speed = typ.max_speed if dist > typ.attack_range_max + 1_500.0 else min(typ.max_speed, float(env.red_speed[0]) + 25.0)
        actions[i] = action_from_setpoints(env, i, desired_pos.astype(np.float32), desired_speed)
    return actions


def step_row(
    case_name: str,
    oracle_mode: str,
    target_policy: str,
    rollout_seed: int,
    episode: int,
    actions: np.ndarray,
    info: dict[str, float],
    env,
) -> dict[str, float | int | str]:
    row: dict[str, float | int | str] = {
        "case": case_name,
        "oracle_mode": oracle_mode,
        "target_policy": target_policy,
        "rollout_seed": rollout_seed,
        "episode": episode,
    }
    for key in (
        "step",
        "success",
        "timeout",
        "collision",
        "constraint_violation",
        "mean_range",
        "min_blue_red_distance",
        "min_blue_blue_distance",
        "tracking_rate",
        "attack_window_rate",
        "attack_geometry_score",
        "chain_closed",
        "comm_connectivity",
        "mean_message_age",
    ):
        row[key] = float(info.get(key, 0.0))
    for i in range(env.config.num_blue):
        row[f"action_{i}"] = int(actions[i])
        row[f"blue{i}_x"] = float(env.blue_pos[i, 0])
        row[f"blue{i}_y"] = float(env.blue_pos[i, 1])
        row[f"blue{i}_z"] = float(env.blue_pos[i, 2])
    row["red0_x"] = float(env.red_pos[0, 0])
    row["red0_y"] = float(env.red_pos[0, 1])
    row["red0_z"] = float(env.red_pos[0, 2])
    return row


def replay_episode(args: argparse.Namespace, target_policy: str, episode: int) -> list[dict[str, float | int | str]]:
    rollout_seed = args.base_seed + episode
    cfg = make_config(args, target_policy, rollout_seed)
    env = make_env(cfg, rollout_seed, training=False)
    env.reset()
    rows: list[dict[str, float | int | str]] = []
    case_name = f"{target_policy}_{args.oracle_mode}"
    while True:
        actions = oracle_actions(env, args.oracle_mode)
        _obs, _share_obs, _graph, _rewards, dones, info = env.step(actions)
        rows.append(step_row(case_name, args.oracle_mode, target_policy, rollout_seed, episode, actions, info, env))
        if np.all(dones):
            return rows


def summarize_case(rows: list[dict[str, float | int | str]]) -> dict[str, float | int | str]:
    by_episode: dict[int, list[dict[str, float | int | str]]] = {}
    for row in rows:
        by_episode.setdefault(int(row["episode"]), []).append(row)

    episode_summaries = []
    for episode_rows in by_episode.values():
        first = episode_rows[0]
        final = episode_rows[-1]
        ranges = np.asarray([float(row["mean_range"]) for row in episode_rows])
        geometry = np.asarray([float(row["attack_geometry_score"]) for row in episode_rows])
        windows = np.asarray([float(row["attack_window_rate"]) for row in episode_rows])
        tracking = np.asarray([float(row["tracking_rate"]) for row in episode_rows])
        episode_summaries.append(
            {
                "success": float(final["success"]),
                "timeout": float(final["timeout"]),
                "collision": float(final["collision"]),
                "steps": float(final["step"]),
                "initial_range": float(first["mean_range"]),
                "final_range": float(final["mean_range"]),
                "min_range": float(np.min(ranges)),
                "range_reduction": float(first["mean_range"]) - float(np.min(ranges)),
                "tracking_rate": float(np.mean(tracking)),
                "attack_window_rate": float(np.mean(windows)),
                "max_attack_geometry_score": float(np.max(geometry)),
                "geometry_gt_025": float(np.max(geometry) > 0.25),
                "geometry_gt_050": float(np.max(geometry) > 0.50),
                "has_attack_window": float(np.max(windows) > 0.0),
            }
        )

    first_row = rows[0]
    return {
        "case": first_row["case"],
        "oracle_mode": first_row["oracle_mode"],
        "target_policy": first_row["target_policy"],
        "episodes": len(episode_summaries),
        "success_rate": float(np.mean([x["success"] for x in episode_summaries])),
        "timeout_rate": float(np.mean([x["timeout"] for x in episode_summaries])),
        "collision_rate": float(np.mean([x["collision"] for x in episode_summaries])),
        "mean_steps": float(np.mean([x["steps"] for x in episode_summaries])),
        "mean_initial_range": float(np.mean([x["initial_range"] for x in episode_summaries])),
        "mean_final_range": float(np.mean([x["final_range"] for x in episode_summaries])),
        "mean_min_range": float(np.mean([x["min_range"] for x in episode_summaries])),
        "mean_range_reduction": float(np.mean([x["range_reduction"] for x in episode_summaries])),
        "mean_tracking_rate": float(np.mean([x["tracking_rate"] for x in episode_summaries])),
        "mean_attack_window_rate": float(np.mean([x["attack_window_rate"] for x in episode_summaries])),
        "mean_max_attack_geometry_score": float(np.mean([x["max_attack_geometry_score"] for x in episode_summaries])),
        "episodes_with_attack_geometry_gt_025": float(np.mean([x["geometry_gt_025"] for x in episode_summaries])),
        "episodes_with_attack_geometry_gt_050": float(np.mean([x["geometry_gt_050"] for x in episode_summaries])),
        "episodes_with_attack_window": float(np.mean([x["has_attack_window"] for x in episode_summaries])),
    }


def write_csv(path: Path, columns: tuple[str, ...], rows: list[dict[str, float | int | str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def write_md(path: Path, summary_rows: list[dict[str, float | int | str]], step_csv: Path, summary_csv: Path) -> None:
    step_rel = step_csv.resolve().relative_to(ROOT).as_posix()
    summary_rel = summary_csv.resolve().relative_to(ROOT).as_posix()
    lines = [
        "# Geometric-Oracle Maneuvering-Target Reachability",
        "",
        "This diagnostic uses a deterministic non-learning policy to test whether the maneuvering-target scenario can form attack windows under the current 3DOF dynamics and attack-window constraints.",
        "",
        "## Files",
        "",
        f"- Step trace: `{step_rel}`",
        f"- Summary: `{summary_rel}`",
        "",
        "## Summary",
        "",
        "| Case | Mode | Target | Success | Collision | Min range | Range reduction | Tracking | Max geometry | Geometry > 0.25 | Attack-window episodes |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary_rows:
        lines.append(
            f"| `{row['case']}` | `{row['oracle_mode']}` | `{row['target_policy']}` | "
            f"{float(row['success_rate']):.3f} | {float(row['collision_rate']):.3f} | "
            f"{float(row['mean_min_range']):.1f} | {float(row['mean_range_reduction']):.1f} | "
            f"{float(row['mean_tracking_rate']):.3f} | {float(row['mean_max_attack_geometry_score']):.3f} | "
            f"{float(row['episodes_with_attack_geometry_gt_025']):.3f} | {float(row['episodes_with_attack_window']):.3f} |"
        )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    target_policies = args.target_policy or ["weaving_tiny", "weaving_mild"]
    all_step_rows: list[dict[str, float | int | str]] = []
    summary_rows: list[dict[str, float | int | str]] = []
    for target_policy in target_policies:
        case_rows: list[dict[str, float | int | str]] = []
        for episode in range(args.episodes):
            case_rows.extend(replay_episode(args, target_policy, episode))
        all_step_rows.extend(case_rows)
        summary_rows.append(summarize_case(case_rows))

    step_csv = args.out_dir / "step_trace.csv"
    summary_csv = args.out_dir / "summary.csv"
    summary_md = args.out_dir / "summary.md"
    write_csv(step_csv, STEP_COLUMNS, all_step_rows)
    write_csv(summary_csv, SUMMARY_COLUMNS, summary_rows)
    write_md(summary_md, summary_rows, step_csv, summary_csv)
    print(step_csv)
    print(summary_csv)
    print(summary_md)


if __name__ == "__main__":
    main()
