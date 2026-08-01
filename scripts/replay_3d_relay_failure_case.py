from __future__ import annotations

import argparse
import csv
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import torch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from evaluate_ri_gmappo_3d import build_agent, build_config, stack_graphs  # noqa: E402
from algorithms.ri_gmappo.simple_ri_gmappo import make_env  # noqa: E402


DEFAULT_CANDIDATES = ROOT / "results" / "intercept_3d_relay_failure_case_candidates.csv"
DEFAULT_OUT_CSV = ROOT / "results" / "intercept_3d_relay_failure_case_replay.csv"
DEFAULT_OUT_MD = ROOT / "docs" / "intercept_3d_relay_failure_case_replay.md"
DEFAULT_OUT_FIG = ROOT / "results" / "figures" / "intercept_3d_relay_failure_case_replay.png"

CSV_COLUMNS = (
    "graph_encoder",
    "train_seed",
    "episode",
    "rollout_seed",
    "step",
    "node_failure_active",
    "success",
    "timeout",
    "chain_closed",
    "tracking_rate",
    "attack_window_rate",
    "comm_connectivity",
    "mean_message_age",
    "mean_range",
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Replay the strongest relay-failure case and generate timeline/trajectory assets.")
    parser.add_argument("--candidates-csv", type=Path, default=DEFAULT_CANDIDATES)
    parser.add_argument("--rank", type=int, default=1)
    parser.add_argument("--out-csv", type=Path, default=DEFAULT_OUT_CSV)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    parser.add_argument("--out-fig", type=Path, default=DEFAULT_OUT_FIG)
    parser.add_argument("--device", type=str, default="cpu")
    parser.add_argument("--target-policy", type=str, default="straight")
    parser.add_argument("--communication-range-scale", type=float, default=1.0)
    parser.add_argument("--communication-dropout-prob", type=float, default=0.0)
    parser.add_argument("--message-delay-steps", type=int, default=0)
    parser.add_argument("--radar-dropout-prob", type=float, default=0.0)
    parser.add_argument("--max-target-message-age-steps", type=int, default=80)
    parser.add_argument("--min-target-confidence", type=float, default=0.2)
    parser.add_argument("--failed-blue-agent", type=int, default=1)
    parser.add_argument("--node-failure-start-step", type=int, default=40)
    parser.add_argument("--node-failure-duration-steps", type=int, default=80)
    parser.add_argument("--graph-relation-ablation", choices=("none", "no_task_support"), default="none")
    parser.add_argument("--graph-message-ablation", choices=("none", "no_role_pair_gate"), default="none")
    parser.add_argument("--hidden-dim", type=int, default=128)
    parser.add_argument("--role-dim", type=int, default=8)
    parser.add_argument("--intent-dim", type=int, default=8)
    return parser.parse_args()


def read_candidates(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def resolve_checkpoint(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def agent_args(args: argparse.Namespace, checkpoint: Path, graph_encoder: str, rollout_seed: int) -> argparse.Namespace:
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
        strict_target_sensing=False,
        agent_target_info_bottleneck=False,
        max_target_message_age_steps=args.max_target_message_age_steps,
        min_target_confidence=args.min_target_confidence,
        failed_blue_agent=args.failed_blue_agent,
        node_failure_start_step=args.node_failure_start_step,
        node_failure_duration_steps=args.node_failure_duration_steps,
        graph_relation_ablation=args.graph_relation_ablation,
        graph_message_ablation=args.graph_message_ablation,
        graph_input_ablation="none",
        stochastic=False,
        allow_random_policy=False,
        hidden_dim=args.hidden_dim,
        role_dim=args.role_dim,
        intent_dim=args.intent_dim,
        graph_encoder=graph_encoder,
        device=args.device,
    )


def state_row(
    graph_encoder: str,
    train_seed: str,
    episode: str,
    rollout_seed: int,
    info: dict[str, float],
    env,
) -> dict[str, str]:
    row: dict[str, str] = {
        "graph_encoder": graph_encoder,
        "train_seed": train_seed,
        "episode": episode,
        "rollout_seed": str(rollout_seed),
    }
    for key in (
        "step",
        "node_failure_active",
        "success",
        "timeout",
        "chain_closed",
        "tracking_rate",
        "attack_window_rate",
        "comm_connectivity",
        "mean_message_age",
        "mean_range",
    ):
        row[key] = f"{float(info[key]):.6g}"
    for i in range(env.config.num_blue):
        row[f"blue{i}_x"] = f"{float(env.blue_pos[i, 0]):.6g}"
        row[f"blue{i}_y"] = f"{float(env.blue_pos[i, 1]):.6g}"
        row[f"blue{i}_z"] = f"{float(env.blue_pos[i, 2]):.6g}"
    row["red0_x"] = f"{float(env.red_pos[0, 0]):.6g}"
    row["red0_y"] = f"{float(env.red_pos[0, 1]):.6g}"
    row["red0_z"] = f"{float(env.red_pos[0, 2]):.6g}"
    return row


def replay_one(
    args: argparse.Namespace,
    checkpoint: Path,
    graph_encoder: str,
    rollout_seed: int,
    train_seed: str,
    episode: str,
) -> list[dict[str, str]]:
    run_args = agent_args(args, checkpoint, graph_encoder, rollout_seed)
    cfg = build_config(run_args)
    agent, _policy_source = build_agent(run_args, cfg)
    device = torch.device(args.device)
    env = make_env(cfg, rollout_seed, training=False)
    obs, share_obs, graph = env.reset()
    rows: list[dict[str, str]] = []
    with torch.no_grad():
        while True:
            g = stack_graphs([graph])
            actions, _, _, _, _, _, _ = agent.get_action_and_value(
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
            obs, share_obs, graph, _rewards, dones, info = env.step(actions.squeeze(0).cpu().numpy())
            rows.append(state_row(graph_encoder, train_seed, episode, rollout_seed, info, env))
            if np.all(dones):
                return rows


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def first_chain_step(rows: list[dict[str, str]]) -> int:
    for row in rows:
        if float(row["chain_closed"]) > 0.5:
            return int(float(row["step"]))
    return -1


def summarize_group(rows: list[dict[str, str]]) -> dict[str, str]:
    final = rows[-1]
    failure_rows = [row for row in rows if float(row["node_failure_active"]) > 0.5]
    return {
        "steps": final["step"],
        "success": final["success"],
        "first_chain_close_step": str(first_chain_step(rows)),
        "tracking_during_failure": f"{np.mean([float(row['tracking_rate']) for row in failure_rows]):.3f}" if failure_rows else "NA",
        "connectivity_during_failure": f"{np.mean([float(row['comm_connectivity']) for row in failure_rows]):.3f}" if failure_rows else "NA",
    }


def write_md(path: Path, rows: list[dict[str, str]], candidate: dict[str, str], out_fig: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    groups = {
        graph: [row for row in rows if row["graph_encoder"] == graph]
        for graph in ("single", "multi_relation")
    }
    summaries = {graph: summarize_group(part) for graph, part in groups.items() if part}
    lines = [
        "# Relay-Failure Case Replay",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "This is a matched qualitative case replay selected from the formal relay-failure evaluation candidates. It is meant to support interpretation of the quantitative table, not replace aggregate statistics.",
        "",
        "## Candidate",
        "",
        "```text",
        f"train_seed = {candidate['train_seed']}",
        f"episode = {candidate['episode']}",
        f"single_rollout_seed = {candidate['single_eval_seed']}",
        f"multi_rollout_seed = {candidate['multi_eval_seed']}",
        f"node_failure = agent 1, steps 40--119",
        "```",
        "",
        "## Replay Summary",
        "",
        "| Graph encoder | Success | Steps | First chain close step | Tracking during failure | Connectivity during failure |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for graph in ("single", "multi_relation"):
        summary = summaries[graph]
        lines.append(
            f"| `{graph}` | {summary['success']} | {summary['steps']} | {summary['first_chain_close_step']} | "
            f"{summary['tracking_during_failure']} | {summary['connectivity_during_failure']} |"
        )
    lines.extend(
        [
            "",
            "## Figure",
            "",
            f"- `{out_fig.relative_to(ROOT).as_posix()}`",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def plot_case(rows: list[dict[str, str]], out_fig: Path) -> None:
    import matplotlib.pyplot as plt

    out_fig.parent.mkdir(parents=True, exist_ok=True)
    colors = {"single": "#386cb0", "multi_relation": "#1b9e77"}
    labels = {"single": "Single graph", "multi_relation": "Multi-relation"}
    fig = plt.figure(figsize=(10.5, 6.8), dpi=180)
    grid = fig.add_gridspec(2, 2, height_ratios=[1.0, 1.1])
    ax_t = fig.add_subplot(grid[0, :])
    ax_xy = fig.add_subplot(grid[1, 0])
    ax_alt = fig.add_subplot(grid[1, 1])

    for graph in ("single", "multi_relation"):
        part = [row for row in rows if row["graph_encoder"] == graph]
        x = np.asarray([float(row["step"]) for row in part])
        tracking = np.asarray([float(row["tracking_rate"]) for row in part])
        chain = np.asarray([float(row["chain_closed"]) for row in part])
        connectivity = np.asarray([float(row["comm_connectivity"]) for row in part])
        ax_t.plot(x, tracking, color=colors[graph], linewidth=2.0, label=f"{labels[graph]} tracking")
        ax_t.plot(x, chain, color=colors[graph], linestyle="--", linewidth=1.8, label=f"{labels[graph]} chain closed")
        ax_t.plot(x, connectivity, color=colors[graph], linestyle=":", linewidth=1.8, label=f"{labels[graph]} connectivity")

        ax_xy.plot(
            [float(row["red0_x"]) / 1000.0 for row in part],
            [float(row["red0_y"]) / 1000.0 for row in part],
            color="#d95f02",
            linewidth=1.6,
            alpha=0.45,
        )
        for i, style in enumerate(("-", "--", ":")):
            ax_xy.plot(
                [float(row[f"blue{i}_x"]) / 1000.0 for row in part],
                [float(row[f"blue{i}_y"]) / 1000.0 for row in part],
                color=colors[graph],
                linestyle=style,
                linewidth=1.5,
                alpha=0.85,
            )
        ax_alt.plot(
            x,
            [float(row["mean_range"]) / 1000.0 for row in part],
            color=colors[graph],
            linewidth=2.0,
            label=labels[graph],
        )

    ax_t.axvspan(40, 120, color="#dddddd", alpha=0.45, label="Relay failure window")
    ax_t.set_ylabel("Rate / indicator")
    ax_t.set_ylim(-0.05, 1.05)
    ax_t.grid(True, linestyle="--", linewidth=0.5, alpha=0.45)
    ax_t.legend(ncol=3, fontsize=7.4, frameon=False)

    ax_xy.set_xlabel("x (km)")
    ax_xy.set_ylabel("y (km)")
    ax_xy.set_title("Top-down trajectories")
    ax_xy.grid(True, linestyle="--", linewidth=0.5, alpha=0.45)

    ax_alt.axvspan(40, 120, color="#dddddd", alpha=0.45)
    ax_alt.set_xlabel("Step")
    ax_alt.set_ylabel("Mean target range (km)")
    ax_alt.set_title("Closure progress")
    ax_alt.grid(True, linestyle="--", linewidth=0.5, alpha=0.45)
    ax_alt.legend(frameon=False, fontsize=8)

    fig.tight_layout()
    fig.savefig(out_fig)
    plt.close(fig)


def main() -> None:
    args = parse_args()
    candidates = read_candidates(args.candidates_csv)
    if args.rank < 1 or args.rank > len(candidates):
        raise ValueError(f"--rank must be in [1, {len(candidates)}]")
    candidate = candidates[args.rank - 1]
    train_seed = candidate["train_seed"]
    episode = candidate["episode"]
    single_rows = replay_one(
        args,
        resolve_checkpoint(candidate["single_checkpoint"]),
        "single",
        int(candidate["single_eval_seed"]),
        train_seed,
        episode,
    )
    multi_rows = replay_one(
        args,
        resolve_checkpoint(candidate["multi_checkpoint"]),
        "multi_relation",
        int(candidate["multi_eval_seed"]),
        train_seed,
        episode,
    )
    rows = single_rows + multi_rows
    write_csv(args.out_csv, rows)
    plot_case(rows, args.out_fig)
    write_md(args.out_md, rows, candidate, args.out_fig)
    print(args.out_csv)
    print(args.out_md)
    print(args.out_fig)


if __name__ == "__main__":
    main()
