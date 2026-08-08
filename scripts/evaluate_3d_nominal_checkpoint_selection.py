from __future__ import annotations

import argparse
import csv
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.evaluate_ri_gmappo_3d import CSV_COLUMNS, evaluate  # noqa: E402


SUMMARY_COLUMNS = (
    "split",
    "method",
    "graph_encoder",
    "train_seed",
    "checkpoint_update",
    "checkpoint",
    "episodes",
    "success_mean",
    "attack_window_formed_mean",
    "tracking_rate_mean",
    "comm_connectivity_mean",
    "timeout_mean",
    "collision_mean",
    "constraint_violation_mean",
    "selection_score",
    "validation_rmst80",
    "validation_establishment_probability",
    "validation_censoring_rate",
    "validation_rmst220",
)

SELECTION_COLUMNS = (
    "split",
    "method",
    "graph_encoder",
    "train_seed",
    "selected_checkpoint_update",
    "selected_checkpoint",
    "selection_score",
    "success_mean",
    "attack_window_formed_mean",
    "tracking_rate_mean",
    "comm_connectivity_mean",
    "collision_mean",
    "episodes",
    "validation_rmst80",
    "validation_establishment_probability",
    "validation_censoring_rate",
    "validation_rmst220",
)


@dataclass(frozen=True)
class Case:
    method: str
    graph_encoder: str
    train_seed: int
    run_dir: Path


@dataclass(frozen=True)
class Candidate:
    case: Case
    checkpoint: Path
    update: int


def parse_case(text: str) -> Case:
    parts = text.split("=", 1)
    if len(parts) != 2:
        raise argparse.ArgumentTypeError("case must use name=graph_encoder:seed:run_dir")
    method, rest = parts
    fields = rest.split(":", 2)
    if len(fields) != 3:
        raise argparse.ArgumentTypeError("case must use name=graph_encoder:seed:run_dir")
    graph_encoder, seed_text, run_dir = fields
    if graph_encoder not in {"no_graph", "single", "multi_relation"}:
        raise argparse.ArgumentTypeError(f"unsupported graph_encoder: {graph_encoder}")
    return Case(method=method, graph_encoder=graph_encoder, train_seed=int(seed_text), run_dir=Path(run_dir))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate nominal 3DOF checkpoint snapshots on validation/test splits and select checkpoints."
    )
    parser.add_argument("--case", action="append", type=parse_case, required=True)
    parser.add_argument("--split", choices=("validation", "test"), default="validation")
    parser.add_argument("--selection-csv", type=Path, default=None)
    parser.add_argument("--checkpoint-glob", type=str, default="actor_critic_update_*.pt")
    parser.add_argument("--episodes", type=int, default=20)
    parser.add_argument("--base-seed", type=int, default=509_000)
    parser.add_argument("--target-policy", type=str, default="weaving_mild")
    parser.add_argument("--max-selection-collision-rate", type=float, default=0.0)
    parser.add_argument("--hidden-dim", type=int, default=64)
    parser.add_argument("--role-dim", type=int, default=8)
    parser.add_argument("--intent-dim", type=int, default=8)
    parser.add_argument("--eval-batch-size", type=int, default=1)
    parser.add_argument("--device", type=str, default="cpu")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "results" / "nominal_checkpoint_selection")
    parser.add_argument("--resume", action="store_true")
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


def resolve(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def discover_candidates(args: argparse.Namespace) -> list[Candidate]:
    candidates: list[Candidate] = []
    for case in args.case:
        run_dir = resolve(case.run_dir)
        for checkpoint in sorted(run_dir.glob(args.checkpoint_glob), key=checkpoint_update):
            candidates.append(Candidate(case=case, checkpoint=checkpoint, update=checkpoint_update(checkpoint)))
    if not candidates:
        raise FileNotFoundError("no checkpoint candidates found")
    return candidates


def candidates_from_selection(args: argparse.Namespace) -> list[Candidate]:
    if args.selection_csv is None:
        return discover_candidates(args)
    selection_csv = resolve(args.selection_csv)
    rows = read_csv(selection_csv)
    case_by_key = {(case.method, case.graph_encoder, case.train_seed): case for case in args.case}
    candidates: list[Candidate] = []
    for row in rows:
        key = (row["method"], row["graph_encoder"], int(row["train_seed"]))
        if key not in case_by_key:
            continue
        checkpoint = resolve(Path(row["selected_checkpoint"]))
        candidates.append(
            Candidate(
                case=case_by_key[key],
                checkpoint=checkpoint,
                update=int(row["selected_checkpoint_update"]),
            )
        )
    if not candidates:
        raise FileNotFoundError(f"no selected checkpoints from {selection_csv}")
    return candidates


def make_eval_args(args: argparse.Namespace, candidate: Candidate) -> argparse.Namespace:
    return SimpleNamespace(
        checkpoint=candidate.checkpoint,
        episodes=args.episodes,
        eval_batch_size=args.eval_batch_size,
        seed=candidate.case.train_seed,
        base_seed=args.base_seed,
        target_policy=args.target_policy,
        communication_range_scale=1.0,
        communication_dropout_prob=0.30,
        message_delay_steps=2,
        radar_dropout_prob=0.10,
        strict_target_sensing=True,
        agent_target_info_bottleneck=True,
        max_target_message_age_steps=80,
        min_target_confidence=0.2,
        failed_blue_agent=1,
        node_failure_start_step=40,
        node_failure_duration_steps=80,
        stochastic=False,
        allow_random_policy=False,
        hidden_dim=args.hidden_dim,
        role_dim=args.role_dim,
        intent_dim=args.intent_dim,
        graph_encoder=candidate.case.graph_encoder,
        graph_relation_ablation="none",
        graph_message_ablation="none",
        graph_input_ablation="none",
        device=args.device,
    )


def mean(rows: list[dict[str, object]], key: str) -> float:
    return float(np.mean([float(row[key]) for row in rows])) if rows else float("nan")


def selection_score(success: float, attack_window: float, tracking: float, collision: float, constraint: float, max_collision: float) -> float:
    if collision > max_collision or constraint > 0.0:
        return -1_000_000_000.0
    return 1_000.0 * success + 100.0 * attack_window + 10.0 * tracking


def validation_rmst(rows: list[dict[str, object]], tau: float) -> float:
    values = []
    for row in rows:
        raw = row.get("post_failure_chain_recovery_steps_censored", row.get("post_failure_chain_recovery_steps", tau))
        try:
            values.append(float(np.clip(float(raw), 0.0, tau)))
        except (TypeError, ValueError):
            values.append(float(tau))
    return float(np.mean(values)) if values else float(tau)


def summarize_rows(args: argparse.Namespace, candidate: Candidate, rows: list[dict[str, object]]) -> dict[str, str]:
    success = mean(rows, "success")
    attack_window = mean(rows, "attack_window_formed")
    tracking = mean(rows, "tracking_rate")
    connectivity = mean(rows, "comm_connectivity")
    collision = mean(rows, "collision")
    constraint = mean(rows, "constraint_violation")
    score = selection_score(success, attack_window, tracking, collision, constraint, args.max_selection_collision_rate)
    rmst80 = validation_rmst(rows, 80.0)
    rmst220 = validation_rmst(rows, 220.0)
    establishment = mean(rows, "post_failure_chain_recovered")
    censoring = float(1.0 - establishment)
    return {
        "split": args.split,
        "method": candidate.case.method,
        "graph_encoder": candidate.case.graph_encoder,
        "train_seed": str(candidate.case.train_seed),
        "checkpoint_update": str(candidate.update),
        "checkpoint": display_path(candidate.checkpoint),
        "episodes": str(args.episodes),
        "success_mean": f"{success:.6g}",
        "attack_window_formed_mean": f"{attack_window:.6g}",
        "tracking_rate_mean": f"{tracking:.6g}",
        "comm_connectivity_mean": f"{connectivity:.6g}",
        "timeout_mean": f"{mean(rows, 'timeout'):.6g}",
        "collision_mean": f"{collision:.6g}",
        "constraint_violation_mean": f"{constraint:.6g}",
        "selection_score": f"{score:.6g}",
        "validation_rmst80": f"{rmst80:.6g}",
        "validation_establishment_probability": f"{establishment:.6g}",
        "validation_censoring_rate": f"{censoring:.6g}",
        "validation_rmst220": f"{rmst220:.6g}",
    }


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, object]], columns: tuple[str, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def completed_key(row: dict[str, object]) -> tuple[str, str, str, str, str]:
    return (
        str(row["split"]),
        str(row["method"]),
        str(row["graph_encoder"]),
        str(row["train_seed"]),
        str(row["checkpoint_update"]),
    )


def select_checkpoints(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    grouped: dict[tuple[str, str, str], list[dict[str, str]]] = {}
    for row in rows:
        grouped.setdefault((row["method"], row["graph_encoder"], row["train_seed"]), []).append(row)
    selected: list[dict[str, str]] = []
    for (_method, _graph, _seed), group in sorted(grouped.items()):
        eligible = [row for row in group if float(row["selection_score"]) > -1_000_000_000.0]
        if not eligible:
            eligible = group
        # Censoring-aware preregistered estimand: lower RMST80, then higher
        # establishment probability, then lower RMST220, then earlier update.
        best = min(
            eligible,
            key=lambda row: (
                float(row["validation_rmst80"]),
                -float(row["validation_establishment_probability"]),
                float(row["validation_rmst220"]),
                int(row["checkpoint_update"]),
            ),
        )
        selected.append(
            {
                "split": best["split"],
                "method": best["method"],
                "graph_encoder": best["graph_encoder"],
                "train_seed": best["train_seed"],
                "selected_checkpoint_update": best["checkpoint_update"],
                "selected_checkpoint": best["checkpoint"],
                "selection_score": best["selection_score"],
                "success_mean": best["success_mean"],
                "attack_window_formed_mean": best["attack_window_formed_mean"],
                "tracking_rate_mean": best["tracking_rate_mean"],
                "comm_connectivity_mean": best["comm_connectivity_mean"],
                "collision_mean": best["collision_mean"],
                "episodes": best["episodes"],
                "validation_rmst80": best["validation_rmst80"],
                "validation_establishment_probability": best["validation_establishment_probability"],
                "validation_censoring_rate": best["validation_censoring_rate"],
                "validation_rmst220": best["validation_rmst220"],
            }
        )
    return selected


def write_report(path: Path, args: argparse.Namespace, selected_rows: list[dict[str, str]]) -> None:
    lines = [
        "# Nominal 3DOF Checkpoint Selection",
        "",
        "This report evaluates nominal 3DOF checkpoints on a fixed split. Validation rows are for checkpoint selection; test rows must use a frozen validation selection CSV.",
        "",
        "## Protocol",
        "",
        "```text",
        f"split = {args.split}",
        f"target_policy = {args.target_policy}",
        f"episodes = {args.episodes}",
        f"base_seed = {args.base_seed}",
        f"eval_batch_size = {args.eval_batch_size}",
        f"selection_csv = {display_path(resolve(args.selection_csv)) if args.selection_csv else 'none'}",
        f"max_selection_collision_rate = {args.max_selection_collision_rate}",
        "failure = agent 1, start 40, duration 80; dropout=0.30, delay=2, radar_dropout=0.10, strict sensing + target bottleneck",
        "selection = RMST80 ascending; establishment probability descending; RMST220 ascending; earlier update tie-break",
        "```",
        "",
        "## Selected Checkpoints",
        "",
        "| Method | Graph | Seed | Update | Success | Attack window | Collision | Checkpoint |",
        "|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in selected_rows:
        lines.append(
            f"| `{row['method']}` | `{row['graph_encoder']}` | {row['train_seed']} | "
            f"{row['selected_checkpoint_update']} | {row['success_mean']} | "
            f"{row['attack_window_formed_mean']} | {row['collision_mean']} | "
            f"`{row['selected_checkpoint']}` |"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- Use validation split only for checkpoint selection and hyperparameter decisions.",
            "- Use test split only after checkpoint selection is frozen.",
            "- Do not tune on test split results.",
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
    report_path = args.out_dir / f"{args.split}_checkpoint_selection.md"
    episode_rows: list[dict[str, object]] = read_csv(episode_path) if args.resume else []
    summary_rows: list[dict[str, str]] = read_csv(summary_path) if args.resume else []
    completed = {completed_key(row) for row in summary_rows}
    extra_episode_columns = ("split", "method", "graph_encoder", "train_seed", "checkpoint_update")

    for candidate in candidates:
        key = (args.split, candidate.case.method, candidate.case.graph_encoder, str(candidate.case.train_seed), str(candidate.update))
        if key in completed:
            print(f"skip completed {key}", flush=True)
            continue
        print(
            f"eval {args.split} {candidate.case.method} {candidate.case.graph_encoder} "
            f"seed={candidate.case.train_seed} update={candidate.update}",
            flush=True,
        )
        rows = evaluate(make_eval_args(args, candidate))
        for row in rows:
            row.update(
                {
                    "split": args.split,
                    "method": candidate.case.method,
                    "graph_encoder": candidate.case.graph_encoder,
                    "train_seed": candidate.case.train_seed,
                    "checkpoint_update": candidate.update,
                }
            )
        episode_rows.extend(rows)
        summary_rows.append(summarize_rows(args, candidate, rows))
        completed.add(key)
        write_csv(episode_path, episode_rows, (*extra_episode_columns, *CSV_COLUMNS))
        write_csv(summary_path, summary_rows, SUMMARY_COLUMNS)

    selected_rows = select_checkpoints(summary_rows)
    write_csv(episode_path, episode_rows, (*extra_episode_columns, *CSV_COLUMNS))
    write_csv(summary_path, summary_rows, SUMMARY_COLUMNS)
    write_csv(selection_path, selected_rows, SELECTION_COLUMNS)
    write_report(report_path, args, selected_rows)
    print(summary_path)
    print(selection_path)
    print(report_path)


if __name__ == "__main__":
    main()
