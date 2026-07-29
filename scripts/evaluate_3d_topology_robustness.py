from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.evaluate_ri_gmappo_3d import CSV_COLUMNS, evaluate


@dataclass(frozen=True)
class RobustnessScenario:
    name: str
    communication_range_scale: float = 1.0
    communication_dropout_prob: float = 0.0
    message_delay_steps: int = 0
    radar_dropout_prob: float = 0.0
    failed_blue_agent: int = -1
    node_failure_start_step: int = 0
    node_failure_duration_steps: int = 0


SCENARIOS = {
    "nominal": RobustnessScenario("nominal"),
    "range_075": RobustnessScenario("range_075", communication_range_scale=0.75),
    "range_050": RobustnessScenario("range_050", communication_range_scale=0.50),
    "dropout_015": RobustnessScenario("dropout_015", communication_dropout_prob=0.15),
    "dropout_030": RobustnessScenario("dropout_030", communication_dropout_prob=0.30),
    "delay_2": RobustnessScenario("delay_2", message_delay_steps=2),
    "delay_5": RobustnessScenario("delay_5", message_delay_steps=5),
    "radar_010": RobustnessScenario("radar_010", radar_dropout_prob=0.10),
    "radar_025": RobustnessScenario("radar_025", radar_dropout_prob=0.25),
    "relay_failure": RobustnessScenario("relay_failure", failed_blue_agent=1, node_failure_start_step=40, node_failure_duration_steps=80),
    "relay_failure_early": RobustnessScenario(
        "relay_failure_early",
        failed_blue_agent=1,
        node_failure_start_step=25,
        node_failure_duration_steps=80,
    ),
    "relay_failure_late": RobustnessScenario(
        "relay_failure_late",
        failed_blue_agent=1,
        node_failure_start_step=70,
        node_failure_duration_steps=80,
    ),
    "relay_failure_delayed": RobustnessScenario(
        "relay_failure_delayed",
        failed_blue_agent=1,
        node_failure_start_step=55,
        node_failure_duration_steps=80,
    ),
    "dropout030_relay_failure": RobustnessScenario(
        "dropout030_relay_failure",
        communication_dropout_prob=0.30,
        failed_blue_agent=1,
        node_failure_start_step=40,
        node_failure_duration_steps=80,
    ),
    "dropout030_relay_failure_early": RobustnessScenario(
        "dropout030_relay_failure_early",
        communication_dropout_prob=0.30,
        failed_blue_agent=1,
        node_failure_start_step=25,
        node_failure_duration_steps=80,
    ),
    "dropout030_relay_failure_late": RobustnessScenario(
        "dropout030_relay_failure_late",
        communication_dropout_prob=0.30,
        failed_blue_agent=1,
        node_failure_start_step=70,
        node_failure_duration_steps=80,
    ),
    "dropout030_relay_failure_delayed": RobustnessScenario(
        "dropout030_relay_failure_delayed",
        communication_dropout_prob=0.30,
        failed_blue_agent=1,
        node_failure_start_step=55,
        node_failure_duration_steps=80,
    ),
    "dropout030_delay2_relay_failure": RobustnessScenario(
        "dropout030_delay2_relay_failure",
        communication_dropout_prob=0.30,
        message_delay_steps=2,
        failed_blue_agent=1,
        node_failure_start_step=40,
        node_failure_duration_steps=80,
    ),
    "dropout030_delay2_relay_failure_early": RobustnessScenario(
        "dropout030_delay2_relay_failure_early",
        communication_dropout_prob=0.30,
        message_delay_steps=2,
        failed_blue_agent=1,
        node_failure_start_step=25,
        node_failure_duration_steps=80,
    ),
    "dropout030_delay2_relay_failure_late": RobustnessScenario(
        "dropout030_delay2_relay_failure_late",
        communication_dropout_prob=0.30,
        message_delay_steps=2,
        failed_blue_agent=1,
        node_failure_start_step=70,
        node_failure_duration_steps=80,
    ),
    "dropout030_delay2_relay_failure_delayed": RobustnessScenario(
        "dropout030_delay2_relay_failure_delayed",
        communication_dropout_prob=0.30,
        message_delay_steps=2,
        failed_blue_agent=1,
        node_failure_start_step=55,
        node_failure_duration_steps=80,
    ),
    "scout_failure": RobustnessScenario("scout_failure", failed_blue_agent=0, node_failure_start_step=40, node_failure_duration_steps=80),
    "dropout030_scout_failure": RobustnessScenario(
        "dropout030_scout_failure",
        communication_dropout_prob=0.30,
        failed_blue_agent=0,
        node_failure_start_step=40,
        node_failure_duration_steps=80,
    ),
    "dropout030_delay2_scout_failure": RobustnessScenario(
        "dropout030_delay2_scout_failure",
        communication_dropout_prob=0.30,
        message_delay_steps=2,
        failed_blue_agent=0,
        node_failure_start_step=40,
        node_failure_duration_steps=80,
    ),
}

METRICS = (
    "success",
    "chain_closed",
    "attack_window_formed",
    "attack_window_rate",
    "tracking_rate",
    "comm_connectivity",
    "mean_message_age",
    "collision",
    "timeout",
    "constraint_violation",
    "steps",
    "avg_mean_range",
    "final_mean_range",
    "reward_sum",
)
EXTRA_COLUMNS = ("scenario", "graph_encoder", "train_method", "train_seed")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate existing 3DOF single-graph and multi-relation checkpoints under communication-topology disruptions."
    )
    parser.add_argument("--seeds", nargs="+", type=int, default=(0, 1, 2))
    parser.add_argument("--train-methods", nargs="+", choices=("bc_only", "bc_ppo"), default=("bc_ppo",))
    parser.add_argument(
        "--graph-encoders",
        nargs="+",
        choices=("no_graph", "single", "multi_relation"),
        default=("single", "multi_relation"),
    )
    parser.add_argument("--scenarios", nargs="+", choices=tuple(SCENARIOS), default=tuple(SCENARIOS))
    parser.add_argument("--episodes", type=int, default=30)
    parser.add_argument("--eval-base-seed", type=int, default=80_000)
    parser.add_argument("--target-policy", type=str, default="straight")
    parser.add_argument("--strict-target-sensing", action="store_true")
    parser.add_argument("--agent-target-info-bottleneck", action="store_true")
    parser.add_argument("--max-target-message-age-steps", type=int, default=80)
    parser.add_argument("--min-target-confidence", type=float, default=0.2)
    parser.add_argument("--checkpoint-kind", choices=("actor_critic_best.pt", "actor_critic_latest.pt"), default="actor_critic_best.pt")
    parser.add_argument("--no-graph-root", type=Path, default=ROOT / "results" / "intercept_3d_no_graph_matched_protocol" / "runs")
    parser.add_argument("--single-root", type=Path, default=ROOT / "results" / "intercept_3d_single_matched_protocol" / "runs")
    parser.add_argument("--multi-root", type=Path, default=ROOT / "results" / "intercept_3d_multirelation_matched_protocol" / "runs")
    parser.add_argument("--graph-relation-ablation", choices=("none", "no_task_support"), default="none")
    parser.add_argument("--graph-message-ablation", choices=("none", "no_role_pair_gate"), default="none")
    parser.add_argument("--graph-input-ablation", choices=("none", "no_edge_features", "no_role_identity"), default="none")
    parser.add_argument("--device", type=str, default="cpu")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "results" / "intercept_3d_topology_robustness")
    parser.add_argument("--allow-missing", action="store_true")
    return parser.parse_args()


def checkpoint_path(args: argparse.Namespace, graph_encoder: str, train_method: str, seed: int) -> Path:
    if graph_encoder == "no_graph":
        root = args.no_graph_root
    elif graph_encoder == "single":
        root = args.single_root
    elif graph_encoder == "multi_relation":
        root = args.multi_root
    else:
        raise ValueError(f"Unsupported graph_encoder: {graph_encoder}")
    return root / f"{train_method}_seed{seed}" / args.checkpoint_kind


def make_eval_args(
    args: argparse.Namespace,
    scenario: RobustnessScenario,
    checkpoint: Path,
    graph_encoder: str,
    train_seed: int,
) -> argparse.Namespace:
    return SimpleNamespace(
        checkpoint=checkpoint,
        episodes=args.episodes,
        seed=train_seed,
        base_seed=args.eval_base_seed,
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
        graph_relation_ablation=args.graph_relation_ablation,
        graph_message_ablation=args.graph_message_ablation,
        graph_input_ablation=args.graph_input_ablation,
        stochastic=False,
        allow_random_policy=False,
        hidden_dim=128,
        role_dim=8,
        intent_dim=8,
        graph_encoder=graph_encoder,
        device=args.device,
        out_csv=args.out_dir / "_unused.csv",
        summary_md=args.out_dir / "_unused.md",
    )


def run_suite(args: argparse.Namespace) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for graph_encoder in args.graph_encoders:
        for train_method in args.train_methods:
            for train_seed in args.seeds:
                checkpoint = checkpoint_path(args, graph_encoder, train_method, train_seed)
                if not checkpoint.exists():
                    if args.allow_missing:
                        print(f"skip missing checkpoint: {checkpoint}")
                        continue
                    raise FileNotFoundError(f"missing checkpoint: {checkpoint}")
                for scenario_name in args.scenarios:
                    scenario = SCENARIOS[scenario_name]
                    eval_args = make_eval_args(args, scenario, checkpoint, graph_encoder, train_seed)
                    for row in evaluate(eval_args):
                        enriched = {
                            "scenario": scenario.name,
                            "graph_encoder": graph_encoder,
                            "graph_relation_ablation": args.graph_relation_ablation,
                            "graph_message_ablation": args.graph_message_ablation,
                            "graph_input_ablation": args.graph_input_ablation,
                            "train_method": train_method,
                            "train_seed": train_seed,
                            "strict_target_sensing": int(args.strict_target_sensing),
                            "agent_target_info_bottleneck": int(args.agent_target_info_bottleneck),
                        }
                        enriched.update(row)
                        rows.append(enriched)
    return rows


def write_episode_csv(rows: list[dict[str, object]], out_csv: Path) -> None:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=(*EXTRA_COLUMNS, *CSV_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)


def aggregate_seed_means(rows: list[dict[str, object]]) -> dict[tuple[str, str, str], dict[str, list[float]]]:
    per_seed: dict[tuple[str, str, str, int], dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        key = (
            str(row["scenario"]),
            str(row["graph_encoder"]),
            str(row["train_method"]),
            int(row["train_seed"]),
        )
        for metric in METRICS:
            per_seed[key][metric].append(float(row[metric]))

    aggregate: dict[tuple[str, str, str], dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for (scenario, graph_encoder, train_method, _seed), metrics in per_seed.items():
        for metric, values in metrics.items():
            aggregate[(scenario, graph_encoder, train_method)][metric].append(float(np.mean(values)))
    return aggregate


def write_summary(rows: list[dict[str, object]], out_md: Path, args: argparse.Namespace) -> None:
    aggregate = aggregate_seed_means(rows)
    lines = [
        "# 3DOF Topology Robustness Evaluation",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "Purpose:",
        "",
        "```text",
        "Evaluate saved 3DOF checkpoints under communication range compression, dropout, delay, radar dropout, and temporary communication-node failure.",
        "When the checkpoints are nominally trained, use this as scenario screening; when they are topology-curriculum trained, use it as a matched robustness diagnostic.",
        "```",
        "",
        "## Configuration",
        "",
        "```text",
        f"episodes_per_checkpoint_scenario = {args.episodes}",
        f"training_seeds = {list(args.seeds)}",
        f"train_methods = {list(args.train_methods)}",
        f"graph_encoders = {list(args.graph_encoders)}",
        f"graph_relation_ablation = {args.graph_relation_ablation}",
        f"graph_message_ablation = {args.graph_message_ablation}",
        f"graph_input_ablation = {args.graph_input_ablation}",
        f"scenarios = {list(args.scenarios)}",
        f"target_policy = {args.target_policy}",
        f"strict_target_sensing = {args.strict_target_sensing}",
        f"agent_target_info_bottleneck = {args.agent_target_info_bottleneck}",
        f"max_target_message_age_steps = {args.max_target_message_age_steps}",
        f"min_target_confidence = {args.min_target_confidence}",
        f"checkpoint_kind = {args.checkpoint_kind}",
        "```",
        "",
        "## Seed-Mean Summary",
        "",
        "| Scenario | Graph | Train Method | Success | Chain | Tracking | Connectivity | Message Age | Timeout | Steps |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for key in sorted(aggregate):
        scenario, graph_encoder, train_method = key
        metrics = aggregate[key]

        def mean_std(metric: str) -> str:
            values = metrics[metric]
            return f"{float(np.mean(values)):.3f} +/- {float(np.std(values, ddof=0)):.3f}"

        lines.append(
            f"| {scenario} | {graph_encoder} | {train_method} | {mean_std('success')} | {mean_std('chain_closed')} | "
            f"{mean_std('tracking_rate')} | {mean_std('comm_connectivity')} | {mean_std('mean_message_age')} | "
            f"{mean_std('timeout')} | {mean_std('steps')} |"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "```text",
            "A paper robustness claim requires matched training budgets, fixed evaluation seeds, and enough episodes per checkpoint-scenario.",
            "Use small-episode runs for diagnostics only; reserve 30+ episode runs for formal tables.",
            "```",
            "",
        ]
    )
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    rows = run_suite(args)
    if not rows:
        raise RuntimeError("no robustness rows were produced")
    out_csv = args.out_dir / "episode_metrics.csv"
    out_md = args.out_dir / "summary.md"
    write_episode_csv(rows, out_csv)
    write_summary(rows, out_md, args)
    print(out_csv)
    print(out_md)
    print(f"episodes: {len(rows)}")


if __name__ == "__main__":
    main()
