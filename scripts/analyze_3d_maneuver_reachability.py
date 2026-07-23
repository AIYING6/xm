from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import numpy as np
import torch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from algorithms.ri_gmappo.simple_ri_gmappo import make_env  # noqa: E402
from evaluate_ri_gmappo_3d import build_agent, build_config, stack_graphs  # noqa: E402


STEP_COLUMNS = (
    "case",
    "train_seed",
    "checkpoint",
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
    "train_seed",
    "checkpoint",
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


def parse_case(text: str) -> tuple[str, int, Path]:
    parts = text.split("=", 2)
    if len(parts) != 3:
        raise argparse.ArgumentTypeError(
            "cases must use case_name=train_seed=checkpoint_path"
        )
    name, train_seed_text, checkpoint_text = parts
    return name, int(train_seed_text), Path(checkpoint_text)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Replay 3DOF maneuvering-target checkpoints and record reachability traces."
    )
    parser.add_argument(
        "--case",
        action="append",
        type=parse_case,
        required=True,
        help="Case spec: case_name=train_seed=checkpoint_path. Can be repeated.",
    )
    parser.add_argument("--episodes", type=int, default=30)
    parser.add_argument("--base-seed", type=int, default=409_000)
    parser.add_argument("--target-policy", type=str, default="weaving_mild")
    parser.add_argument("--graph-encoder", choices=("no_graph", "single", "multi_relation"), default="multi_relation")
    parser.add_argument("--graph-relation-ablation", choices=("none", "no_task_support"), default="none")
    parser.add_argument("--graph-message-ablation", choices=("none", "no_role_pair_gate"), default="none")
    parser.add_argument("--graph-input-ablation", choices=("none", "no_edge_features", "no_role_identity"), default="none")
    parser.add_argument("--strict-target-sensing", action="store_true")
    parser.add_argument("--agent-target-info-bottleneck", action="store_true")
    parser.add_argument("--communication-range-scale", type=float, default=1.0)
    parser.add_argument("--communication-dropout-prob", type=float, default=0.0)
    parser.add_argument("--message-delay-steps", type=int, default=0)
    parser.add_argument("--radar-dropout-prob", type=float, default=0.0)
    parser.add_argument("--failed-blue-agent", type=int, default=-1)
    parser.add_argument("--node-failure-start-step", type=int, default=0)
    parser.add_argument("--node-failure-duration-steps", type=int, default=0)
    parser.add_argument("--max-target-message-age-steps", type=int, default=80)
    parser.add_argument("--min-target-confidence", type=float, default=0.2)
    parser.add_argument("--hidden-dim", type=int, default=64)
    parser.add_argument("--role-dim", type=int, default=8)
    parser.add_argument("--intent-dim", type=int, default=8)
    parser.add_argument("--device", type=str, default="cpu")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "results" / "maneuver_reachability")
    return parser.parse_args()


def resolve_checkpoint(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def agent_args(args: argparse.Namespace, checkpoint: Path, rollout_seed: int) -> argparse.Namespace:
    return argparse.Namespace(
        checkpoint=checkpoint,
        seed=rollout_seed,
        episodes=1,
        base_seed=rollout_seed,
        target_policy=args.target_policy,
        communication_range_scale=args.communication_range_scale,
        communication_dropout_prob=args.communication_dropout_prob,
        message_delay_steps=args.message_delay_steps,
        radar_dropout_prob=args.radar_dropout_prob,
        strict_target_sensing=args.strict_target_sensing,
        agent_target_info_bottleneck=args.agent_target_info_bottleneck,
        max_target_message_age_steps=args.max_target_message_age_steps,
        min_target_confidence=args.min_target_confidence,
        failed_blue_agent=args.failed_blue_agent,
        node_failure_start_step=args.node_failure_start_step,
        node_failure_duration_steps=args.node_failure_duration_steps,
        graph_relation_ablation=args.graph_relation_ablation,
        graph_message_ablation=args.graph_message_ablation,
        graph_input_ablation=args.graph_input_ablation,
        stochastic=False,
        allow_random_policy=False,
        hidden_dim=args.hidden_dim,
        role_dim=args.role_dim,
        intent_dim=args.intent_dim,
        graph_encoder=args.graph_encoder,
        device=args.device,
    )


def step_row(
    case_name: str,
    train_seed: int,
    checkpoint: Path,
    rollout_seed: int,
    episode: int,
    actions: np.ndarray,
    info: dict[str, float],
    env,
) -> dict[str, float | int | str]:
    row: dict[str, float | int | str] = {
        "case": case_name,
        "train_seed": train_seed,
        "checkpoint": checkpoint.as_posix(),
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


def replay_episode(
    args: argparse.Namespace,
    case_name: str,
    train_seed: int,
    checkpoint: Path,
    episode: int,
) -> list[dict[str, float | int | str]]:
    rollout_seed = args.base_seed + episode
    run_args = agent_args(args, checkpoint, rollout_seed)
    cfg = build_config(run_args)
    agent, _policy_source = build_agent(run_args, cfg)
    device = torch.device(args.device)
    env = make_env(cfg, rollout_seed, training=False)
    obs, share_obs, graph = env.reset()
    rows: list[dict[str, float | int | str]] = []

    with torch.no_grad():
        while True:
            g = stack_graphs([graph])
            actions, _, _, _, _, _ = agent.get_action_and_value(
                torch.as_tensor(obs[None, ...], dtype=torch.float32, device=device),
                torch.as_tensor(g["node_feat"], dtype=torch.float32, device=device),
                torch.as_tensor(g["edge_feat"], dtype=torch.float32, device=device),
                torch.as_tensor(g["role"], dtype=torch.long, device=device),
                torch.as_tensor(g["adj"], dtype=torch.float32, device=device),
                torch.as_tensor(share_obs[None, ...], dtype=torch.float32, device=device),
                relation_adj=torch.as_tensor(g["relation_adj"], dtype=torch.float32, device=device),
                deterministic=True,
                intent_label=torch.as_tensor(g["intent_label"], dtype=torch.long, device=device),
                detach_intent=False,
                oracle_intent=False,
            )
            action_np = actions.squeeze(0).cpu().numpy().astype(np.int64)
            obs, share_obs, graph, _rewards, dones, info = env.step(action_np)
            rows.append(step_row(case_name, train_seed, checkpoint, rollout_seed, episode, action_np, info, env))
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
        "train_seed": first_row["train_seed"],
        "checkpoint": first_row["checkpoint"],
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
    path.parent.mkdir(parents=True, exist_ok=True)
    step_rel = step_csv.resolve().relative_to(ROOT).as_posix()
    summary_rel = summary_csv.resolve().relative_to(ROOT).as_posix()
    lines = [
        "# Maneuvering-Target Reachability Analysis",
        "",
        "This diagnostic replays maneuvering-target policies step-by-step to determine whether failure comes from poor approach, poor tracking, or inability to form attack geometry.",
        "",
        "## Files",
        "",
        f"- Step trace: `{step_rel}`",
        f"- Summary: `{summary_rel}`",
        "",
        "## Summary",
        "",
        "| Case | Train seed | Success | Min range | Range reduction | Tracking | Max geometry | Geometry > 0.25 | Attack-window episodes |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary_rows:
        lines.append(
            f"| `{row['case']}` | {row['train_seed']} | {float(row['success_rate']):.3f} | "
            f"{float(row['mean_min_range']):.1f} | {float(row['mean_range_reduction']):.1f} | "
            f"{float(row['mean_tracking_rate']):.3f} | {float(row['mean_max_attack_geometry_score']):.3f} | "
            f"{float(row['episodes_with_attack_geometry_gt_025']):.3f} | {float(row['episodes_with_attack_window']):.3f} |"
        )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    all_step_rows: list[dict[str, float | int | str]] = []
    summary_rows: list[dict[str, float | int | str]] = []
    for case_name, train_seed, checkpoint_text in args.case:
        checkpoint = resolve_checkpoint(checkpoint_text)
        case_rows: list[dict[str, float | int | str]] = []
        for episode in range(args.episodes):
            case_rows.extend(replay_episode(args, case_name, train_seed, checkpoint, episode))
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
