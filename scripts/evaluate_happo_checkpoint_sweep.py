from __future__ import annotations

import argparse
import csv
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.evaluate_3d_checkpoint_sweep import (  # noqa: E402
    SELECTION_COLUMNS,
    SUMMARY_COLUMNS,
    completed_key,
    display_path,
    mean,
    mean_delayed_recovery,
    mean_delayed_recovery_steps,
    mean_recovery_steps,
    read_existing_csv,
    selection_score,
    select_checkpoints,
    write_csv,
)
from scripts.evaluate_happo_3d import evaluate  # noqa: E402
from scripts.evaluate_ri_gmappo_3d import CSV_COLUMNS  # noqa: E402
from scripts.evaluate_3d_topology_robustness import SCENARIOS  # noqa: E402


@dataclass(frozen=True)
class Candidate:
    train_seed: int
    checkpoint: Path
    update: int


def checkpoint_update(path: Path) -> int:
    match = re.search(r"update_(\d+)", path.name)
    if match:
        return int(match.group(1))
    if path.name == "happo_latest.pt":
        return -1
    return -99


def discover_candidates(args: argparse.Namespace) -> list[Candidate]:
    candidates: list[Candidate] = []
    allowed_updates = set(args.checkpoint_updates) if args.checkpoint_updates else None
    for seed in args.seeds:
        run_dir = args.happo_root / args.run_dir_template.format(seed=seed)
        paths = sorted(run_dir.glob(args.checkpoint_glob), key=checkpoint_update)
        if allowed_updates is not None:
            paths = [path for path in paths if checkpoint_update(path) in allowed_updates]
        if not paths:
            message = f"no HAPPO checkpoints matching {args.checkpoint_glob} under {run_dir}"
            if allowed_updates is not None:
                message += f" after filtering updates {sorted(allowed_updates)}"
            if args.allow_missing:
                print(f"skip: {message}", flush=True)
                continue
            raise FileNotFoundError(message)
        for checkpoint in paths:
            candidates.append(Candidate(seed, checkpoint, checkpoint_update(checkpoint)))
    return candidates


def candidates_from_selection(args: argparse.Namespace) -> list[Candidate]:
    if args.selection_csv is None:
        return discover_candidates(args)
    if not args.selection_csv.exists():
        raise FileNotFoundError(args.selection_csv)
    candidates: list[Candidate] = []
    with args.selection_csv.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if row["graph_encoder"] != "happo":
                continue
            seed = int(row["train_seed"])
            if seed not in args.seeds:
                continue
            checkpoint = ROOT / row["selected_checkpoint"]
            if not checkpoint.exists():
                if args.allow_missing:
                    print(f"skip missing selected HAPPO checkpoint: {checkpoint}", flush=True)
                    continue
                raise FileNotFoundError(checkpoint)
            candidates.append(Candidate(seed, checkpoint, int(row["selected_checkpoint_update"])))
    return candidates


def make_eval_args(args: argparse.Namespace, candidate: Candidate, scenario_name: str) -> argparse.Namespace:
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
        target_prior_position=tuple(args.target_prior_position),
        max_target_message_age_steps=args.max_target_message_age_steps,
        min_target_confidence=args.min_target_confidence,
        failed_blue_agent=scenario.failed_blue_agent,
        node_failure_start_step=scenario.node_failure_start_step,
        node_failure_duration_steps=scenario.node_failure_duration_steps,
        min_success_step=args.min_success_step,
        stochastic=False,
        allow_random_policy=False,
        hidden_dim=args.hidden_dim,
        role_dim=args.role_dim,
        intent_dim=args.intent_dim,
        graph_relation_ablation="none",
        graph_message_ablation="none",
        graph_input_ablation="none",
        device=args.device,
    )


def summarize_rows(
    args: argparse.Namespace,
    candidate: Candidate,
    scenario_name: str,
    rows: list[dict[str, object]],
) -> dict[str, str]:
    recovery = mean(rows, "post_failure_chain_recovered")
    recovered_after_loss = mean(rows, "post_failure_chain_recovered_after_loss")
    delayed = mean_delayed_recovery(rows, args.delayed_recovery_min_step)
    recovery_steps = mean_recovery_steps(rows)
    delayed_steps = mean_delayed_recovery_steps(rows, args.delayed_recovery_min_step)
    success = mean(rows, "success")
    collision = mean(rows, "collision")
    score_recovery = delayed if args.selection_metric == "delayed_recovery" else recovery
    score_steps = delayed_steps if args.selection_metric == "delayed_recovery" else recovery_steps
    score = selection_score(
        score_recovery,
        score_steps,
        success,
        collision,
        args.max_selection_collision_rate,
        args.selection_success_weight,
    )
    return {
        "split": args.split,
        "scenario": scenario_name,
        "graph_encoder": "happo",
        "graph_relation_ablation": "none",
        "graph_message_ablation": "none",
        "graph_input_ablation": "none",
        "train_seed": str(candidate.train_seed),
        "checkpoint_update": str(candidate.update),
        "checkpoint": display_path(candidate.checkpoint),
        "strict_target_sensing": str(args.strict_target_sensing),
        "agent_target_info_bottleneck": str(args.agent_target_info_bottleneck),
        "target_prior_position": ";".join(f"{float(x):.6g}" for x in args.target_prior_position),
        "max_target_message_age_steps": str(args.max_target_message_age_steps),
        "min_target_confidence": f"{args.min_target_confidence:.6g}",
        "episodes": str(args.episodes),
        "success_mean": f"{success:.6g}",
        "post_failure_chain_recovered_mean": f"{recovery:.6g}",
        "post_failure_chain_recovered_after_loss_mean": f"{recovered_after_loss:.6g}",
        "delayed_recovery_min_step": str(args.delayed_recovery_min_step),
        "delayed_recovery_mean": f"{delayed:.6g}",
        "post_failure_chain_recovery_steps_mean": "inf" if not np.isfinite(recovery_steps) else f"{recovery_steps:.6g}",
        "delayed_recovery_steps_mean": "inf" if not np.isfinite(delayed_steps) else f"{delayed_steps:.6g}",
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
        "selection_metric": args.selection_metric,
        "selection_success_weight": f"{args.selection_success_weight:.6g}",
    }


def write_report(path: Path, args: argparse.Namespace, summary_rows: list[dict[str, str]], selected_rows: list[dict[str, str]]) -> None:
    lines = [
        "# 3DOF HAPPO Checkpoint Sweep",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "```text",
        f"split = {args.split}",
        f"seeds = {list(args.seeds)}",
        f"scenarios = {list(args.scenarios)}",
        f"episodes = {args.episodes}",
        f"base_seed = {args.base_seed}",
        f"checkpoint_updates = {list(args.checkpoint_updates) if args.checkpoint_updates else 'all'}",
        f"selection_group = {args.selection_group}",
        f"selection_metric = {args.selection_metric}",
        f"delayed_recovery_min_step = {args.delayed_recovery_min_step}",
        f"selection_success_weight = {args.selection_success_weight}",
        f"selection_csv = {display_path(args.selection_csv) if args.selection_csv else 'none'}",
        "```",
        "",
        "| Scenario | Seed | Update | Recovery | Recovery steps | Success | Checkpoint |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in selected_rows:
        lines.append(
            f"| {row['scenario']} | {row['train_seed']} | {row['selected_checkpoint_update']} | "
            f"{row['post_failure_chain_recovered_mean']} | {row['post_failure_chain_recovery_steps_mean']} | "
            f"{row['success_mean']} | `{row['selected_checkpoint']}` |"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- HAPPO uses the same validation/test selection schema as the other paper methods.",
            "- Test split should use validation-selected checkpoints through `--selection-csv`.",
            "",
            f"Evaluated checkpoint-scenario combinations: {len(summary_rows)}",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate HAPPO checkpoint snapshots on fixed matched episodes.")
    parser.add_argument("--split", choices=("validation", "test"), default="validation")
    parser.add_argument("--seeds", nargs="+", type=int, default=(0,))
    parser.add_argument("--scenarios", nargs="+", choices=tuple(SCENARIOS), default=("relay_failure",))
    parser.add_argument("--episodes", type=int, default=50)
    parser.add_argument("--eval-batch-size", type=int, default=1)
    parser.add_argument("--base-seed", type=int, default=120_000)
    parser.add_argument("--target-policy", type=str, default="straight")
    parser.add_argument("--strict-target-sensing", action="store_true", default=True)
    parser.add_argument("--no-strict-target-sensing", dest="strict_target_sensing", action="store_false")
    parser.add_argument("--agent-target-info-bottleneck", action="store_true")
    parser.add_argument("--target-prior-position", type=float, nargs=3, default=(10_000.0, 0.0, 5_000.0))
    parser.add_argument("--max-target-message-age-steps", type=int, default=80)
    parser.add_argument("--min-target-confidence", type=float, default=0.2)
    parser.add_argument("--min-success-step", type=int, default=0)
    parser.add_argument("--happo-root", type=Path, default=ROOT / "results" / "paper_config_runs" / "smoke" / "runs" / "happo")
    parser.add_argument(
        "--run-dir-template",
        type=str,
        default="bc_ppo_seed{seed}",
        help="Per-seed run directory template under --happo-root.",
    )
    parser.add_argument("--checkpoint-glob", type=str, default="happo_update_*.pt")
    parser.add_argument(
        "--checkpoint-updates",
        nargs="*",
        type=int,
        default=None,
        help="Optional update numbers to keep after --checkpoint-glob discovery.",
    )
    parser.add_argument("--selection-csv", type=Path, default=None)
    parser.add_argument("--hidden-dim", type=int, default=64)
    parser.add_argument("--role-dim", type=int, default=8)
    parser.add_argument("--intent-dim", type=int, default=8)
    parser.add_argument("--device", type=str, default="cpu")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "results" / "happo_checkpoint_sweep")
    parser.add_argument("--allow-missing", action="store_true")
    parser.add_argument("--resume", action="store_true", help="Resume an interrupted sweep by skipping completed checkpoint/scenario rows.")
    parser.add_argument(
        "--selection-group",
        choices=("scenario", "suite"),
        default="scenario",
        help=(
            "Checkpoint-selection grouping. scenario selects one checkpoint per scenario; "
            "suite selects one checkpoint per seed using mean validation score across requested scenarios."
        ),
    )
    parser.add_argument(
        "--selection-metric",
        choices=("legacy_recovery", "delayed_recovery"),
        default="legacy_recovery",
        help="Checkpoint-selection metric, matching the RI-GMAPPO checkpoint sweep.",
    )
    parser.add_argument(
        "--delayed-recovery-min-step",
        type=int,
        default=80,
        help="Absolute minimum post-failure first-chain step when --selection-metric=delayed_recovery.",
    )
    parser.add_argument(
        "--max-new-evals",
        type=int,
        default=None,
        help="Stop after this many newly evaluated checkpoint/scenario pairs. Useful for chunking long sweeps.",
    )
    parser.add_argument("--max-selection-collision-rate", type=float, default=None)
    parser.add_argument(
        "--selection-success-weight",
        type=float,
        default=100.0,
        help="Weight applied to success_mean in checkpoint selection.",
    )
    return parser.parse_args()


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

    new_evals = 0
    stop_requested = False
    for candidate in candidates:
        for scenario_name in args.scenarios:
            key = (args.split, scenario_name, "happo", "none", "none", "none", str(candidate.train_seed), str(candidate.update))
            if key in completed:
                print(
                    f"skip completed {args.split} {scenario_name} happo "
                    f"seed={candidate.train_seed} update={candidate.update}",
                    flush=True,
                )
                continue
            print(f"eval {args.split} {scenario_name} happo seed={candidate.train_seed} update={candidate.update}", flush=True)
            rows = evaluate(make_eval_args(args, candidate, scenario_name))
            for row in rows:
                row.update(
                    {
                        "split": args.split,
                        "scenario": scenario_name,
                        "graph_encoder": "happo",
                        "train_seed": candidate.train_seed,
                        "checkpoint_update": candidate.update,
                    }
                )
            episode_rows.extend(rows)
            summary_rows.append(summarize_rows(args, candidate, scenario_name, rows))
            completed.add(key)
            write_csv(episode_path, episode_rows, (*extra_episode_columns, *CSV_COLUMNS))
            write_csv(summary_path, summary_rows, SUMMARY_COLUMNS)
            new_evals += 1
            if args.max_new_evals is not None and new_evals >= args.max_new_evals:
                stop_requested = True
                break
        if stop_requested:
            break

    selected_rows = select_checkpoints(args, summary_rows)
    write_csv(episode_path, episode_rows, (*extra_episode_columns, *CSV_COLUMNS))
    write_csv(summary_path, summary_rows, SUMMARY_COLUMNS)
    write_csv(selection_path, selected_rows, SELECTION_COLUMNS)
    write_report(report_path, args, summary_rows, selected_rows)
    print(summary_path)
    print(selection_path)
    print(report_path)


if __name__ == "__main__":
    main()
