from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.evaluate_3d_topology_robustness import SCENARIOS
from scripts.evaluate_ri_gmappo_3d import CSV_COLUMNS, evaluate


SUMMARY_COLUMNS = (
    "split",
    "scenario",
    "graph_encoder",
    "graph_relation_ablation",
    "graph_message_ablation",
    "graph_input_ablation",
    "train_seed",
    "checkpoint_update",
    "checkpoint",
    "strict_target_sensing",
    "agent_target_info_bottleneck",
    "max_target_message_age_steps",
    "min_target_confidence",
    "episodes",
    "success_mean",
    "post_failure_chain_recovered_mean",
    "post_failure_chain_recovery_steps_mean",
    "chain_closed_during_failure_rate_mean",
    "tracking_during_failure_rate_mean",
    "connectivity_during_failure_mean",
    "episode_min_blue_red_distance_mean",
    "episode_min_blue_blue_distance_mean",
    "steps_mean",
    "timeout_mean",
    "collision_mean",
    "constraint_violation_mean",
    "selection_score",
)

SELECTION_COLUMNS = (
    "split",
    "scenario",
    "graph_encoder",
    "graph_relation_ablation",
    "graph_message_ablation",
    "graph_input_ablation",
    "train_seed",
    "selected_checkpoint_update",
    "selected_checkpoint",
    "strict_target_sensing",
    "agent_target_info_bottleneck",
    "max_target_message_age_steps",
    "min_target_confidence",
    "selection_score",
    "post_failure_chain_recovered_mean",
    "post_failure_chain_recovery_steps_mean",
    "success_mean",
    "collision_mean",
    "episode_min_blue_red_distance_mean",
    "episode_min_blue_blue_distance_mean",
    "constraint_violation_mean",
    "episodes",
)


@dataclass(frozen=True)
class Candidate:
    graph_encoder: str
    train_seed: int
    checkpoint: Path
    update: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate saved 3DOF checkpoint snapshots on fixed matched episodes and select checkpoints."
    )
    parser.add_argument("--split", choices=("validation", "test"), default="validation")
    parser.add_argument("--seeds", nargs="+", type=int, default=(0, 1, 2))
    parser.add_argument(
        "--graph-encoders",
        nargs="+",
        choices=("no_graph", "single", "multi_relation"),
        default=("single", "multi_relation"),
    )
    parser.add_argument("--scenarios", nargs="+", choices=tuple(SCENARIOS), default=("relay_failure",))
    parser.add_argument("--episodes", type=int, default=50)
    parser.add_argument("--eval-batch-size", type=int, default=1)
    parser.add_argument("--base-seed", type=int, default=120_000)
    parser.add_argument("--target-policy", type=str, default="straight")
    parser.add_argument("--strict-target-sensing", action="store_true", default=True)
    parser.add_argument("--no-strict-target-sensing", dest="strict_target_sensing", action="store_false")
    parser.add_argument("--agent-target-info-bottleneck", action="store_true")
    parser.add_argument("--graph-relation-ablation", choices=("none", "no_task_support"), default="none")
    parser.add_argument("--graph-message-ablation", choices=("none", "no_role_pair_gate"), default="none")
    parser.add_argument("--graph-input-ablation", choices=("none", "no_edge_features", "no_role_identity"), default="none")
    parser.add_argument("--max-target-message-age-steps", type=int, default=80)
    parser.add_argument("--min-target-confidence", type=float, default=0.2)
    parser.add_argument("--single-root", type=Path, default=ROOT / "results" / "intercept_3d_strict_sensing_formal" / "runs" / "single")
    parser.add_argument("--multi-root", type=Path, default=ROOT / "results" / "intercept_3d_strict_sensing_formal" / "runs" / "multi_relation")
    parser.add_argument("--no-graph-root", type=Path, default=ROOT / "results" / "intercept_3d_strict_sensing_fair_baselines" / "runs" / "no_graph")
    parser.add_argument("--checkpoint-glob", type=str, default="actor_critic_update_*.pt")
    parser.add_argument("--selection-csv", type=Path, default=None)
    parser.add_argument("--device", type=str, default="cpu")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "results" / "intercept_3d_strict_sensing_checkpoint_sweep")
    parser.add_argument("--allow-missing", action="store_true")
    parser.add_argument("--resume", action="store_true", help="Resume an interrupted sweep by skipping completed checkpoint/scenario rows.")
    parser.add_argument(
        "--max-selection-collision-rate",
        type=float,
        default=None,
        help=(
            "If set, validation checkpoints with collision_mean above this threshold "
            "receive an invalid selection score. Use 0.0 for safety-critical formal runs."
        ),
    )
    return parser.parse_args()


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def checkpoint_update(path: Path) -> int:
    match = re.search(r"update_(\d+)", path.name)
    if match:
        return int(match.group(1))
    if path.name == "actor_critic_best.pt":
        return -2
    if path.name == "actor_critic_latest.pt":
        return -1
    return -99


def root_for(args: argparse.Namespace, graph_encoder: str) -> Path:
    if graph_encoder == "no_graph":
        return args.no_graph_root
    if graph_encoder == "single":
        return args.single_root
    if graph_encoder == "multi_relation":
        return args.multi_root
    raise ValueError(f"Unsupported graph_encoder: {graph_encoder}")


def discover_candidates(args: argparse.Namespace) -> list[Candidate]:
    candidates: list[Candidate] = []
    for graph_encoder in args.graph_encoders:
        root = root_for(args, graph_encoder)
        for seed in args.seeds:
            run_dir = root / f"bc_ppo_seed{seed}"
            paths = sorted(run_dir.glob(args.checkpoint_glob), key=checkpoint_update)
            if not paths:
                message = f"no checkpoints matching {args.checkpoint_glob} under {run_dir}"
                if args.allow_missing:
                    print(f"skip: {message}", flush=True)
                    continue
                raise FileNotFoundError(message)
            for checkpoint in paths:
                candidates.append(Candidate(graph_encoder, seed, checkpoint, checkpoint_update(checkpoint)))
    return candidates


def candidates_from_selection(args: argparse.Namespace) -> list[Candidate]:
    if args.selection_csv is None:
        return discover_candidates(args)
    if not args.selection_csv.exists():
        raise FileNotFoundError(args.selection_csv)
    candidates: list[Candidate] = []
    with args.selection_csv.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            graph_encoder = row["graph_encoder"]
            if graph_encoder not in args.graph_encoders:
                continue
            seed = int(row["train_seed"])
            if seed not in args.seeds:
                continue
            checkpoint = ROOT / row["selected_checkpoint"]
            if not checkpoint.exists():
                if args.allow_missing:
                    print(f"skip missing selected checkpoint: {checkpoint}", flush=True)
                    continue
                raise FileNotFoundError(checkpoint)
            candidates.append(
                Candidate(
                    graph_encoder=graph_encoder,
                    train_seed=seed,
                    checkpoint=checkpoint,
                    update=int(row["selected_checkpoint_update"]),
                )
            )
    return candidates


def make_eval_args(
    args: argparse.Namespace,
    candidate: Candidate,
    scenario_name: str,
) -> argparse.Namespace:
    scenario = SCENARIOS[scenario_name]
    return SimpleNamespace(
        checkpoint=candidate.checkpoint,
        episodes=args.episodes,
        eval_batch_size=args.eval_batch_size,
        seed=candidate.train_seed,
        base_seed=args.base_seed,
        target_policy=args.target_policy,
        communication_range_scale=scenario.communication_range_scale,
        communication_dropout_prob=scenario.communication_dropout_prob,
        message_delay_steps=scenario.message_delay_steps,
        radar_dropout_prob=scenario.radar_dropout_prob,
        strict_target_sensing=args.strict_target_sensing,
        agent_target_info_bottleneck=args.agent_target_info_bottleneck,
        max_target_message_age_steps=args.max_target_message_age_steps,
        min_target_confidence=args.min_target_confidence,
        failed_blue_agent=scenario.failed_blue_agent,
        node_failure_start_step=scenario.node_failure_start_step,
        node_failure_duration_steps=scenario.node_failure_duration_steps,
        stochastic=False,
        allow_random_policy=False,
        hidden_dim=64,
        role_dim=8,
        intent_dim=8,
        graph_encoder=candidate.graph_encoder,
        graph_relation_ablation=args.graph_relation_ablation,
        graph_message_ablation=args.graph_message_ablation,
        graph_input_ablation=args.graph_input_ablation,
        device=args.device,
    )


def mean(rows: list[dict[str, object]], key: str) -> float:
    values = [float(row[key]) for row in rows]
    return float(np.mean(values)) if values else float("nan")


def mean_recovery_steps(rows: list[dict[str, object]]) -> float:
    values = [float(row["post_failure_chain_recovery_steps"]) for row in rows if float(row["post_failure_chain_recovered"]) > 0.5]
    return float(np.mean(values)) if values else float("inf")


def selection_score(
    recovery: float,
    recovery_steps: float,
    success: float,
    collision: float,
    max_collision_rate: float | None,
) -> float:
    if max_collision_rate is not None and collision > max_collision_rate:
        return -1_000_000_000.0
    finite_steps = recovery_steps if np.isfinite(recovery_steps) else 1_000.0
    return 1_000.0 * recovery + 100.0 * success - finite_steps


def summarize_rows(
    args: argparse.Namespace,
    candidate: Candidate,
    scenario_name: str,
    rows: list[dict[str, object]],
) -> dict[str, str]:
    recovery = mean(rows, "post_failure_chain_recovered")
    recovery_steps = mean_recovery_steps(rows)
    success = mean(rows, "success")
    collision = mean(rows, "collision")
    score = selection_score(
        recovery=recovery,
        recovery_steps=recovery_steps,
        success=success,
        collision=collision,
        max_collision_rate=args.max_selection_collision_rate,
    )
    return {
        "split": args.split,
        "scenario": scenario_name,
        "graph_encoder": candidate.graph_encoder,
        "graph_relation_ablation": args.graph_relation_ablation,
        "graph_message_ablation": args.graph_message_ablation,
        "graph_input_ablation": args.graph_input_ablation,
        "train_seed": str(candidate.train_seed),
        "checkpoint_update": str(candidate.update),
        "checkpoint": display_path(candidate.checkpoint),
        "strict_target_sensing": str(args.strict_target_sensing),
        "agent_target_info_bottleneck": str(args.agent_target_info_bottleneck),
        "max_target_message_age_steps": str(args.max_target_message_age_steps),
        "min_target_confidence": f"{args.min_target_confidence:.6g}",
        "episodes": str(args.episodes),
        "success_mean": f"{success:.6g}",
        "post_failure_chain_recovered_mean": f"{recovery:.6g}",
        "post_failure_chain_recovery_steps_mean": "inf" if not np.isfinite(recovery_steps) else f"{recovery_steps:.6g}",
        "chain_closed_during_failure_rate_mean": f"{mean(rows, 'chain_closed_during_failure_rate'):.6g}",
        "tracking_during_failure_rate_mean": f"{mean(rows, 'tracking_during_failure_rate'):.6g}",
        "connectivity_during_failure_mean": f"{mean(rows, 'connectivity_during_failure'):.6g}",
        "episode_min_blue_red_distance_mean": f"{mean(rows, 'episode_min_blue_red_distance'):.6g}",
        "episode_min_blue_blue_distance_mean": f"{mean(rows, 'episode_min_blue_blue_distance'):.6g}",
        "steps_mean": f"{mean(rows, 'steps'):.6g}",
        "timeout_mean": f"{mean(rows, 'timeout'):.6g}",
        "collision_mean": f"{collision:.6g}",
        "constraint_violation_mean": f"{mean(rows, 'constraint_violation'):.6g}",
        "selection_score": f"{score:.6g}",
    }


def write_csv(path: Path, rows: list[dict[str, object]], columns: tuple[str, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def read_existing_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def completed_key(row: dict[str, object]) -> tuple[str, str, str, str, str]:
    return (
        str(row["split"]),
        str(row["scenario"]),
        str(row["graph_encoder"]),
        str(row.get("graph_relation_ablation", "none")),
        str(row.get("graph_message_ablation", "none")),
        str(row.get("graph_input_ablation", "none")),
        str(row["train_seed"]),
        str(row["checkpoint_update"]),
    )


def select_checkpoints(summary_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    grouped: dict[tuple[str, str, str, str, str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in summary_rows:
        key = (
            row["split"],
            row["scenario"],
            row["graph_encoder"],
            row.get("graph_relation_ablation", "none"),
            row.get("graph_message_ablation", "none"),
            row.get("graph_input_ablation", "none"),
            row["train_seed"],
        )
        grouped[key].append(row)
    selected: list[dict[str, str]] = []
    for key, rows in sorted(grouped.items()):
        eligible_rows = [row for row in rows if float(row["selection_score"]) > -1_000_000_000.0]
        if not eligible_rows:
            split, scenario, graph_encoder, graph_relation_ablation, graph_message_ablation, graph_input_ablation, train_seed = key
            raise RuntimeError(
                "no collision-eligible checkpoint for "
                f"split={split}, scenario={scenario}, graph_encoder={graph_encoder}, "
                f"graph_relation_ablation={graph_relation_ablation}, "
                f"graph_message_ablation={graph_message_ablation}, "
                f"graph_input_ablation={graph_input_ablation}, train_seed={train_seed}"
            )
        best = max(
            eligible_rows,
            key=lambda row: (
                float(row["selection_score"]),
                int(row["checkpoint_update"]),
            ),
        )
        selected.append(
            {
                "split": best["split"],
                "scenario": best["scenario"],
                "graph_encoder": best["graph_encoder"],
                "graph_relation_ablation": best.get("graph_relation_ablation", "none"),
                "graph_message_ablation": best.get("graph_message_ablation", "none"),
                "graph_input_ablation": best.get("graph_input_ablation", "none"),
                "train_seed": best["train_seed"],
                "selected_checkpoint_update": best["checkpoint_update"],
                "selected_checkpoint": best["checkpoint"],
                "strict_target_sensing": best.get("strict_target_sensing", ""),
                "agent_target_info_bottleneck": best.get("agent_target_info_bottleneck", ""),
                "max_target_message_age_steps": best.get("max_target_message_age_steps", ""),
                "min_target_confidence": best.get("min_target_confidence", ""),
                "selection_score": best["selection_score"],
                "post_failure_chain_recovered_mean": best["post_failure_chain_recovered_mean"],
                "post_failure_chain_recovery_steps_mean": best["post_failure_chain_recovery_steps_mean"],
                "success_mean": best["success_mean"],
                "collision_mean": best.get("collision_mean", ""),
                "episode_min_blue_red_distance_mean": best.get("episode_min_blue_red_distance_mean", ""),
                "episode_min_blue_blue_distance_mean": best.get("episode_min_blue_blue_distance_mean", ""),
                "constraint_violation_mean": best.get("constraint_violation_mean", ""),
                "episodes": best["episodes"],
            }
        )
    return selected


def write_report(
    path: Path,
    args: argparse.Namespace,
    summary_rows: list[dict[str, str]],
    selected_rows: list[dict[str, str]],
) -> None:
    lines = [
        "# 3DOF Strict-Sensing Checkpoint Sweep",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "Purpose:",
        "",
        "```text",
        "Evaluate checkpoint snapshots on a fixed matched split and select checkpoints before final testing.",
        "Selection score = 1000 * recovery_rate + 100 * success_rate - mean_recovery_steps.",
        "Final test evaluation should use the selected validation checkpoints and a disjoint base seed.",
        "```",
        "",
        "## Protocol",
        "",
        "```text",
        f"split = {args.split}",
        f"seeds = {list(args.seeds)}",
        f"graph_encoders = {list(args.graph_encoders)}",
        f"scenarios = {list(args.scenarios)}",
        f"episodes = {args.episodes}",
        f"base_seed = {args.base_seed}",
        f"strict_target_sensing = {args.strict_target_sensing}",
        f"agent_target_info_bottleneck = {args.agent_target_info_bottleneck}",
        f"max_target_message_age_steps = {args.max_target_message_age_steps}",
        f"min_target_confidence = {args.min_target_confidence}",
        f"selection_csv = {display_path(args.selection_csv) if args.selection_csv else 'none'}",
        f"max_selection_collision_rate = {args.max_selection_collision_rate}",
        "```",
        "",
        "## Selected Checkpoints",
        "",
        "| Scenario | Graph | Seed | Update | Recovery | Recovery steps | Success | Checkpoint |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in selected_rows:
        lines.append(
            f"| {row['scenario']} | {row['graph_encoder']} | {row['train_seed']} | "
            f"{row['selected_checkpoint_update']} | {row['post_failure_chain_recovered_mean']} | "
            f"{row['post_failure_chain_recovery_steps_mean']} | {row['success_mean']} | "
            f"`{row['selected_checkpoint']}` |"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- Use validation split only for checkpoint selection and hyperparameter decisions.",
            "- Use test split only after checkpoint selection is frozen.",
            "- Do not compare test results from checkpoints selected on test episodes.",
            "",
            "## Files",
            "",
            f"- Summary rows: `{display_path(args.out_dir / f'{args.split}_checkpoint_summary.csv')}`",
            f"- Episode rows: `{display_path(args.out_dir / f'{args.split}_episode_metrics.csv')}`",
            f"- Selected checkpoints: `{display_path(args.out_dir / f'{args.split}_selected_checkpoints.csv')}`",
            "",
            f"Evaluated checkpoint-scenario combinations: {len(summary_rows)}",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    candidates = candidates_from_selection(args)
    episode_path = args.out_dir / f"{args.split}_episode_metrics.csv"
    summary_path = args.out_dir / f"{args.split}_checkpoint_summary.csv"
    selection_path = args.out_dir / f"{args.split}_selected_checkpoints.csv"
    report_path = args.out_dir / f"{args.split}_checkpoint_sweep.md"
    episode_rows: list[dict[str, object]] = read_existing_csv(episode_path) if args.resume else []
    summary_rows: list[dict[str, str]] = read_existing_csv(summary_path) if args.resume else []
    completed = {completed_key(row) for row in summary_rows}
    extra_episode_columns = ("split", "scenario", "graph_encoder", "train_seed", "checkpoint_update")

    for candidate in candidates:
        for scenario_name in args.scenarios:
            key = (args.split, scenario_name, candidate.graph_encoder, str(candidate.train_seed), str(candidate.update))
            if key in completed:
                print(
                    f"skip completed {args.split} {scenario_name} {candidate.graph_encoder} "
                    f"seed={candidate.train_seed} update={candidate.update}",
                    flush=True,
                )
                continue
            print(
                f"eval {args.split} {scenario_name} {candidate.graph_encoder} seed={candidate.train_seed} update={candidate.update}",
                flush=True,
            )
            rows = evaluate(make_eval_args(args, candidate, scenario_name))
            for row in rows:
                row.update(
                    {
                        "split": args.split,
                        "scenario": scenario_name,
                        "graph_encoder": candidate.graph_encoder,
                        "train_seed": candidate.train_seed,
                        "checkpoint_update": candidate.update,
                    }
                )
            episode_rows.extend(rows)
            summary_rows.append(summarize_rows(args, candidate, scenario_name, rows))
            completed.add(key)
            write_csv(episode_path, episode_rows, (*extra_episode_columns, *CSV_COLUMNS))
            write_csv(summary_path, summary_rows, SUMMARY_COLUMNS)

    selected_rows = select_checkpoints(summary_rows)
    write_csv(episode_path, episode_rows, (*extra_episode_columns, *CSV_COLUMNS))
    write_csv(summary_path, summary_rows, SUMMARY_COLUMNS)
    write_csv(selection_path, selected_rows, SELECTION_COLUMNS)
    write_report(report_path, args, summary_rows, selected_rows)
    print(summary_path)
    print(selection_path)


if __name__ == "__main__":
    main()
