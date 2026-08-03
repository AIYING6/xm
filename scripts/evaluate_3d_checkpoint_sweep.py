from __future__ import annotations

import argparse
import csv
import hashlib
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
    "target_prior_position",
    "max_target_message_age_steps",
    "min_target_confidence",
    "episodes",
    "success_mean",
    "post_failure_chain_recovered_mean",
    "post_failure_chain_recovered_after_loss_mean",
    "pre_failure_chain_established_mean",
    "pre_failure_chain_maintained_mean",
    "pre_failure_chain_recovered_after_loss_mean",
    "post_failure_chain_first_established_mean",
    "post_failure_chain_never_established_mean",
    "post_failure_fresh_info_recovered_mean",
    "post_failure_fresh_info_acquired_without_prior_loss_mean",
    "post_failure_fresh_info_first_established_mean",
    "post_failure_fresh_direct_recovered_mean",
    "post_failure_fresh_comm_recovered_mean",
    "post_failure_post_delivered_old_info_recovered_mean",
    "post_failure_stale_cache_recovered_mean",
    "delayed_recovery_min_step",
    "delayed_recovery_mean",
    "post_failure_chain_recovery_steps_mean",
    "post_failure_fresh_info_recovery_steps_mean",
    "delayed_recovery_steps_mean",
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
    "selection_metric",
    "selection_success_weight",
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
    "checkpoint_sha256",
    "strict_target_sensing",
    "agent_target_info_bottleneck",
    "target_prior_position",
    "max_target_message_age_steps",
    "min_target_confidence",
    "selection_score",
    "selection_metric",
    "selection_success_weight",
    "post_failure_chain_recovered_mean",
    "post_failure_chain_recovered_after_loss_mean",
    "pre_failure_chain_established_mean",
    "pre_failure_chain_maintained_mean",
    "pre_failure_chain_recovered_after_loss_mean",
    "post_failure_chain_first_established_mean",
    "post_failure_chain_never_established_mean",
    "post_failure_fresh_info_recovered_mean",
    "post_failure_fresh_info_acquired_without_prior_loss_mean",
    "post_failure_fresh_info_first_established_mean",
    "post_failure_fresh_direct_recovered_mean",
    "post_failure_fresh_comm_recovered_mean",
    "post_failure_post_delivered_old_info_recovered_mean",
    "post_failure_stale_cache_recovered_mean",
    "delayed_recovery_min_step",
    "delayed_recovery_mean",
    "post_failure_chain_recovery_steps_mean",
    "post_failure_fresh_info_recovery_steps_mean",
    "delayed_recovery_steps_mean",
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
    parser.add_argument("--target-prior-position", type=float, nargs=3, default=(10_000.0, 0.0, 5_000.0))
    parser.add_argument("--graph-relation-ablation", choices=("none", "no_task_support"), default="none")
    parser.add_argument("--graph-message-ablation", choices=("none", "no_role_pair_gate"), default="none")
    parser.add_argument("--graph-input-ablation", choices=("none", "no_edge_features", "no_role_identity"), default="none")
    parser.add_argument("--multi-relation-global-residual-weight", type=float, default=1.0)
    parser.add_argument("--max-target-message-age-steps", type=int, default=80)
    parser.add_argument("--min-target-confidence", type=float, default=0.2)
    parser.add_argument("--single-root", type=Path, default=ROOT / "results" / "intercept_3d_strict_sensing_formal" / "runs" / "single")
    parser.add_argument("--multi-root", type=Path, default=ROOT / "results" / "intercept_3d_strict_sensing_formal" / "runs" / "multi_relation")
    parser.add_argument("--no-graph-root", type=Path, default=ROOT / "results" / "intercept_3d_strict_sensing_fair_baselines" / "runs" / "no_graph")
    parser.add_argument("--checkpoint-glob", type=str, default="actor_critic_update_*.pt")
    parser.add_argument(
        "--run-dir-template",
        type=str,
        default="bc_ppo_seed{seed}",
        help="Run directory name template under each method root. The template may reference {seed}.",
    )
    parser.add_argument(
        "--checkpoint-updates",
        nargs="*",
        type=int,
        default=None,
        help=(
            "Optional update numbers to keep after --checkpoint-glob discovery. "
            "Use this to evaluate a small set of candidate snapshots without changing run directories."
        ),
    )
    parser.add_argument("--selection-csv", type=Path, default=None)
    parser.add_argument("--device", type=str, default="cpu")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "results" / "intercept_3d_strict_sensing_checkpoint_sweep")
    parser.add_argument("--allow-missing", action="store_true")
    parser.add_argument("--resume", action="store_true", help="Resume an interrupted sweep by skipping completed checkpoint/scenario rows.")
    parser.add_argument(
        "--max-new-evals",
        type=int,
        default=None,
        help="Stop after this many newly evaluated checkpoint/scenario pairs. Useful for chunking long sweeps.",
    )
    parser.add_argument(
        "--max-selection-collision-rate",
        type=float,
        default=None,
        help=(
            "If set, validation checkpoints with collision_mean above this threshold "
            "receive an invalid selection score. Use 0.0 for safety-critical formal runs."
        ),
    )
    parser.add_argument(
        "--selection-metric",
        choices=("legacy_recovery", "delayed_recovery", "fresh_info_recovery"),
        default="legacy_recovery",
        help=(
            "Checkpoint-selection metric. legacy_recovery preserves the original "
            "score (v1.4 adjudication default); delayed_recovery selects using first "
            "post-failure chain closure at or after --delayed-recovery-min-step; "
            "fresh_info_recovery selects stable post-failure recovery with attacker "
            "fresh target information."
        ),
    )
    parser.add_argument(
        "--selection-group",
        choices=("scenario", "suite"),
        default="suite",
        help=(
            "Checkpoint-selection grouping. scenario preserves the legacy behavior "
            "of selecting one checkpoint per scenario. suite selects one checkpoint "
            "per method/seed using the mean validation score across all requested scenarios."
        ),
    )
    parser.add_argument(
        "--delayed-recovery-min-step",
        type=int,
        default=80,
        help="Absolute minimum post-failure first-chain step used when --selection-metric=delayed_recovery.",
    )
    parser.add_argument(
        "--selection-success-weight",
        type=float,
        default=100.0,
        help=(
            "Weight applied to success_mean in checkpoint selection "
            "(v1.4 adjudication default 100, per schema score formula)."
        ),
    )
    parser.add_argument(
        "--min-success-step",
        type=int,
        default=0,
        help="Optional minimum environment step before chain closure can terminate an episode as success.",
    )
    parser.add_argument(
        "--attack-hold-steps",
        type=int,
        default=4,
        help="Number of consecutive chain-closed steps required by the environment success condition.",
    )
    return parser.parse_args()


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def checkpoint_sha256(rel_or_abs: str) -> str:
    """SHA256 of a checkpoint file given a display path (relative to ROOT)."""
    path = Path(rel_or_abs)
    if not path.is_absolute():
        path = ROOT / path
    if not path.exists():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


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
    allowed_updates = set(args.checkpoint_updates) if args.checkpoint_updates else None
    for graph_encoder in args.graph_encoders:
        root = root_for(args, graph_encoder)
        for seed in args.seeds:
            run_dir = root / args.run_dir_template.format(seed=seed)
            paths = sorted(run_dir.glob(args.checkpoint_glob), key=checkpoint_update)
            if allowed_updates is not None:
                paths = [path for path in paths if checkpoint_update(path) in allowed_updates]
            if not paths:
                message = f"no checkpoints matching {args.checkpoint_glob} under {run_dir}"
                if allowed_updates is not None:
                    message += f" after filtering updates {sorted(allowed_updates)}"
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
        target_prior_position=tuple(args.target_prior_position),
        max_target_message_age_steps=args.max_target_message_age_steps,
        min_target_confidence=args.min_target_confidence,
        failed_blue_agent=scenario.failed_blue_agent,
        node_failure_start_step=scenario.node_failure_start_step,
        node_failure_duration_steps=scenario.node_failure_duration_steps,
        attack_hold_steps=args.attack_hold_steps,
        min_success_step=args.min_success_step,
        stochastic=False,
        allow_random_policy=False,
        hidden_dim=64,
        role_dim=8,
        intent_dim=8,
        graph_encoder=candidate.graph_encoder,
        graph_relation_ablation=args.graph_relation_ablation,
        graph_message_ablation=args.graph_message_ablation,
        graph_input_ablation=args.graph_input_ablation,
        multi_relation_global_residual_weight=args.multi_relation_global_residual_weight,
        device=args.device,
    )


def mean(rows: list[dict[str, object]], key: str) -> float:
    values = [float(row[key]) for row in rows]
    return float(np.mean(values)) if values else float("nan")


def mean_recovery_steps(rows: list[dict[str, object]]) -> float:
    values = [float(row["post_failure_chain_recovery_steps"]) for row in rows if float(row["post_failure_chain_recovered"]) > 0.5]
    return float(np.mean(values)) if values else float("inf")


def mean_fresh_info_recovery_steps(rows: list[dict[str, object]]) -> float:
    values = [
        float(row["post_failure_fresh_info_recovery_steps"])
        for row in rows
        if float(row.get("post_failure_fresh_info_recovered", 0.0)) > 0.5
    ]
    return float(np.mean(values)) if values else float("inf")


def delayed_recovery(row: dict[str, object], min_step: int) -> float:
    if float(row.get("post_failure_chain_recovered_after_loss", row["post_failure_chain_recovered"])) <= 0.5:
        return 0.0
    return float(float(row.get("post_failure_first_chain_step", -1.0)) >= min_step)


def mean_delayed_recovery(rows: list[dict[str, object]], min_step: int) -> float:
    values = [delayed_recovery(row, min_step) for row in rows]
    return float(np.mean(values)) if values else float("nan")


def mean_delayed_recovery_steps(rows: list[dict[str, object]], min_step: int) -> float:
    values = [
        float(row.get("post_failure_first_chain_step", row["post_failure_chain_recovery_steps"]))
        for row in rows
        if delayed_recovery(row, min_step) > 0.5
    ]
    return float(np.mean(values)) if values else float("inf")


def selection_score(
    recovery: float,
    recovery_steps: float,
    success: float,
    collision: float,
    max_collision_rate: float | None,
    success_weight: float,
) -> float:
    if max_collision_rate is not None and collision > max_collision_rate:
        return -1_000_000_000.0
    finite_steps = recovery_steps if np.isfinite(recovery_steps) else 1_000.0
    return 1_000.0 * recovery + success_weight * success - finite_steps


def summarize_rows(
    args: argparse.Namespace,
    candidate: Candidate,
    scenario_name: str,
    rows: list[dict[str, object]],
) -> dict[str, str]:
    recovery = mean(rows, "post_failure_chain_recovered")
    recovered_after_loss = mean(rows, "post_failure_chain_recovered_after_loss")
    pre_established = mean(rows, "pre_failure_chain_established")
    pre_maintained = mean(rows, "pre_failure_chain_maintained")
    pre_recovered_after_loss = mean(rows, "pre_failure_chain_recovered_after_loss")
    first_established = mean(rows, "post_failure_chain_first_established")
    never_established = mean(rows, "post_failure_chain_never_established")
    fresh_info_recovered = mean(rows, "post_failure_fresh_info_recovered")
    fresh_without_prior_loss = mean(rows, "post_failure_fresh_info_acquired_without_prior_loss")
    fresh_first_established = mean(rows, "post_failure_fresh_info_first_established")
    fresh_direct_recovered = mean(rows, "post_failure_fresh_direct_recovered")
    fresh_comm_recovered = mean(rows, "post_failure_fresh_comm_recovered")
    post_delivered_old_recovered = mean(rows, "post_failure_post_delivered_old_info_recovered")
    stale_cache_recovered = mean(rows, "post_failure_stale_cache_recovered")
    delayed = mean_delayed_recovery(rows, args.delayed_recovery_min_step)
    recovery_steps = mean_recovery_steps(rows)
    fresh_info_steps = mean_fresh_info_recovery_steps(rows)
    delayed_steps = mean_delayed_recovery_steps(rows, args.delayed_recovery_min_step)
    success = mean(rows, "success")
    collision = mean(rows, "collision")
    if args.selection_metric == "fresh_info_recovery":
        score_recovery = fresh_info_recovered
        score_steps = fresh_info_steps
    elif args.selection_metric == "delayed_recovery":
        score_recovery = delayed
        score_steps = delayed_steps
    else:
        score_recovery = recovery
        score_steps = recovery_steps
    score = selection_score(
        recovery=score_recovery,
        recovery_steps=score_steps,
        success=success,
        collision=collision,
        max_collision_rate=args.max_selection_collision_rate,
        success_weight=args.selection_success_weight,
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
        "target_prior_position": ";".join(f"{float(x):.6g}" for x in args.target_prior_position),
        "max_target_message_age_steps": str(args.max_target_message_age_steps),
        "min_target_confidence": f"{args.min_target_confidence:.6g}",
        "episodes": str(args.episodes),
        "success_mean": f"{success:.6g}",
        "post_failure_chain_recovered_mean": f"{recovery:.6g}",
        "post_failure_chain_recovered_after_loss_mean": f"{recovered_after_loss:.6g}",
        "pre_failure_chain_established_mean": f"{pre_established:.6g}",
        "pre_failure_chain_maintained_mean": f"{pre_maintained:.6g}",
        "pre_failure_chain_recovered_after_loss_mean": f"{pre_recovered_after_loss:.6g}",
        "post_failure_chain_first_established_mean": f"{first_established:.6g}",
        "post_failure_chain_never_established_mean": f"{never_established:.6g}",
        "post_failure_fresh_info_recovered_mean": f"{fresh_info_recovered:.6g}",
        "post_failure_fresh_info_acquired_without_prior_loss_mean": f"{fresh_without_prior_loss:.6g}",
        "post_failure_fresh_info_first_established_mean": f"{fresh_first_established:.6g}",
        "post_failure_fresh_direct_recovered_mean": f"{fresh_direct_recovered:.6g}",
        "post_failure_fresh_comm_recovered_mean": f"{fresh_comm_recovered:.6g}",
        "post_failure_post_delivered_old_info_recovered_mean": f"{post_delivered_old_recovered:.6g}",
        "post_failure_stale_cache_recovered_mean": f"{stale_cache_recovered:.6g}",
        "delayed_recovery_min_step": str(args.delayed_recovery_min_step),
        "delayed_recovery_mean": f"{delayed:.6g}",
        "post_failure_chain_recovery_steps_mean": "inf" if not np.isfinite(recovery_steps) else f"{recovery_steps:.6g}",
        "post_failure_fresh_info_recovery_steps_mean": "inf" if not np.isfinite(fresh_info_steps) else f"{fresh_info_steps:.6g}",
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


def completed_key(row: dict[str, object]) -> tuple[str, str, str, str, str, str, str, str]:
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


def parse_score(value: str) -> float:
    try:
        return float(value)
    except ValueError:
        return -1_000_000_000.0


def mean_numeric(rows: list[dict[str, str]], key: str) -> str:
    values: list[float] = []
    for row in rows:
        value = row.get(key, "")
        if value == "":
            return ""
        try:
            values.append(float(value))
        except ValueError:
            return row.get(key, "")
    if not values:
        return ""
    result = float(np.mean(values))
    return "inf" if not np.isfinite(result) else f"{result:.6g}"


def aggregate_suite_rows(args: argparse.Namespace, summary_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    expected_scenarios = set(args.scenarios)
    grouped: dict[tuple[str, str, str, str, str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in summary_rows:
        key = (
            row["split"],
            row["graph_encoder"],
            row.get("graph_relation_ablation", "none"),
            row.get("graph_message_ablation", "none"),
            row.get("graph_input_ablation", "none"),
            row["train_seed"],
            row["checkpoint_update"],
        )
        grouped[key].append(row)

    aggregate_rows: list[dict[str, str]] = []
    for rows in grouped.values():
        scenario_set = {row["scenario"] for row in rows}
        if scenario_set != expected_scenarios:
            continue
        base = dict(rows[0])
        base["scenario"] = "scenario_suite"
        scores = [parse_score(row["selection_score"]) for row in rows]
        base["selection_score"] = (
            "-1000000000" if any(score <= -1_000_000_000.0 for score in scores) else f"{float(np.mean(scores)):.6g}"
        )
        for key in (
            "post_failure_chain_recovered_mean",
            "post_failure_chain_recovered_after_loss_mean",
            "pre_failure_chain_established_mean",
            "pre_failure_chain_maintained_mean",
            "pre_failure_chain_recovered_after_loss_mean",
            "post_failure_chain_first_established_mean",
            "post_failure_chain_never_established_mean",
            "post_failure_fresh_info_recovered_mean",
            "post_failure_fresh_info_acquired_without_prior_loss_mean",
            "post_failure_fresh_info_first_established_mean",
            "post_failure_fresh_direct_recovered_mean",
            "post_failure_fresh_comm_recovered_mean",
            "post_failure_post_delivered_old_info_recovered_mean",
            "post_failure_stale_cache_recovered_mean",
            "delayed_recovery_mean",
            "post_failure_chain_recovery_steps_mean",
            "post_failure_fresh_info_recovery_steps_mean",
            "delayed_recovery_steps_mean",
            "success_mean",
            "chain_closed_mean",
            "attack_window_formed_mean",
            "tracking_rate_mean",
            "comm_connectivity_mean",
            "mean_message_age_mean",
            "chain_closed_during_failure_rate_mean",
            "tracking_during_failure_rate_mean",
            "connectivity_during_failure_mean",
            "episode_min_blue_red_distance_mean",
            "episode_min_blue_blue_distance_mean",
            "steps_mean",
            "timeout_mean",
            "collision_mean",
            "constraint_violation_mean",
        ):
            if key in base:
                base[key] = mean_numeric(rows, key)
        aggregate_rows.append(base)
    return aggregate_rows


def select_checkpoints(args: argparse.Namespace, summary_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows_for_selection = aggregate_suite_rows(args, summary_rows) if args.selection_group == "suite" else summary_rows
    grouped: dict[tuple[str, str, str, str, str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows_for_selection:
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
        eligible_rows = [row for row in rows if parse_score(row["selection_score"]) > -1_000_000_000.0]
        if not eligible_rows:
            split, scenario, graph_encoder, graph_relation_ablation, graph_message_ablation, graph_input_ablation, train_seed = key
            raise RuntimeError(
                "no collision-eligible checkpoint for "
                f"split={split}, scenario={scenario}, graph_encoder={graph_encoder}, "
                f"graph_relation_ablation={graph_relation_ablation}, "
                f"graph_message_ablation={graph_message_ablation}, "
                f"graph_input_ablation={graph_input_ablation}, train_seed={train_seed}"
            )
        # v1.4 selection adjudication (Case C, eval-ops-v1.4.1):
        # rank solely by selection_score (weighted formula, computed in
        # summarize_rows/selection_score), then by larger checkpoint_update on
        # exact ties. No recovery/steps/success lexicographic ordering is used.
        best = max(
            eligible_rows,
            key=lambda row: (
                parse_score(row.get("selection_score", "-1000000000")),
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
                "checkpoint_sha256": checkpoint_sha256(best["checkpoint"]),
                "strict_target_sensing": best.get("strict_target_sensing", ""),
                "agent_target_info_bottleneck": best.get("agent_target_info_bottleneck", ""),
                "target_prior_position": best.get("target_prior_position", ""),
                "max_target_message_age_steps": best.get("max_target_message_age_steps", ""),
                "min_target_confidence": best.get("min_target_confidence", ""),
                "selection_score": best["selection_score"],
                "selection_metric": best.get("selection_metric", "legacy_recovery"),
                "selection_success_weight": best.get("selection_success_weight", "100"),
                "post_failure_chain_recovered_mean": best["post_failure_chain_recovered_mean"],
                "post_failure_chain_recovered_after_loss_mean": best.get(
                    "post_failure_chain_recovered_after_loss_mean", ""
                ),
                "pre_failure_chain_established_mean": best.get("pre_failure_chain_established_mean", ""),
                "pre_failure_chain_maintained_mean": best.get("pre_failure_chain_maintained_mean", ""),
                "pre_failure_chain_recovered_after_loss_mean": best.get(
                    "pre_failure_chain_recovered_after_loss_mean", ""
                ),
                "post_failure_chain_first_established_mean": best.get(
                    "post_failure_chain_first_established_mean", ""
                ),
                "post_failure_chain_never_established_mean": best.get(
                    "post_failure_chain_never_established_mean", ""
                ),
                "post_failure_fresh_info_recovered_mean": best.get(
                    "post_failure_fresh_info_recovered_mean", ""
                ),
                "post_failure_fresh_info_acquired_without_prior_loss_mean": best.get(
                    "post_failure_fresh_info_acquired_without_prior_loss_mean", ""
                ),
                "post_failure_fresh_info_first_established_mean": best.get(
                    "post_failure_fresh_info_first_established_mean", ""
                ),
                "post_failure_fresh_direct_recovered_mean": best.get(
                    "post_failure_fresh_direct_recovered_mean", ""
                ),
                "post_failure_fresh_comm_recovered_mean": best.get(
                    "post_failure_fresh_comm_recovered_mean", ""
                ),
                "post_failure_post_delivered_old_info_recovered_mean": best.get(
                    "post_failure_post_delivered_old_info_recovered_mean", ""
                ),
                "post_failure_stale_cache_recovered_mean": best.get(
                    "post_failure_stale_cache_recovered_mean", ""
                ),
                "delayed_recovery_min_step": best.get("delayed_recovery_min_step", ""),
                "delayed_recovery_mean": best.get("delayed_recovery_mean", ""),
                "post_failure_chain_recovery_steps_mean": best["post_failure_chain_recovery_steps_mean"],
                "post_failure_fresh_info_recovery_steps_mean": best.get(
                    "post_failure_fresh_info_recovery_steps_mean", ""
                ),
                "delayed_recovery_steps_mean": best.get("delayed_recovery_steps_mean", ""),
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
        "Default selection score = 1000 * recovery_rate + 100 * success_rate - mean_recovery_steps.",
        "When selection_metric=delayed_recovery, recovery_rate and recovery_steps use delayed recovery.",
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
        f"checkpoint_updates = {list(args.checkpoint_updates) if args.checkpoint_updates else 'all'}",
        f"strict_target_sensing = {args.strict_target_sensing}",
        f"agent_target_info_bottleneck = {args.agent_target_info_bottleneck}",
        f"target_prior_position = {tuple(args.target_prior_position)}",
        f"max_target_message_age_steps = {args.max_target_message_age_steps}",
        f"min_target_confidence = {args.min_target_confidence}",
        f"multi_relation_global_residual_weight = {args.multi_relation_global_residual_weight}",
        f"selection_metric = {args.selection_metric}",
        f"selection_group = {args.selection_group}",
        f"delayed_recovery_min_step = {args.delayed_recovery_min_step}",
        f"selection_success_weight = {args.selection_success_weight}",
        f"selection_csv = {display_path(args.selection_csv) if args.selection_csv else 'none'}",
        f"max_selection_collision_rate = {args.max_selection_collision_rate}",
        "```",
        "",
        "## Selected Checkpoints",
        "",
        "| Scenario | Graph | Seed | Update | Metric | Recovery | Delayed recovery | Recovery steps | Delayed steps | Success | Checkpoint |",
        "| --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in selected_rows:
        lines.append(
            f"| {row['scenario']} | {row['graph_encoder']} | {row['train_seed']} | "
            f"{row['selected_checkpoint_update']} | {row.get('selection_metric', 'legacy_recovery')} | "
            f"{row['post_failure_chain_recovered_mean']} | {row.get('delayed_recovery_mean', '')} | "
            f"{row['post_failure_chain_recovery_steps_mean']} | {row.get('delayed_recovery_steps_mean', '')} | "
            f"{row['success_mean']} | "
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

    new_evals = 0
    stop_requested = False
    for candidate in candidates:
        for scenario_name in args.scenarios:
            key = (
                args.split,
                scenario_name,
                candidate.graph_encoder,
                args.graph_relation_ablation,
                args.graph_message_ablation,
                args.graph_input_ablation,
                str(candidate.train_seed),
                str(candidate.update),
            )
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


if __name__ == "__main__":
    main()
