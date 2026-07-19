from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.simple_ri_gmappo import RIGMAPPOConfig, make_env
from scripts.evaluate_3d_topology_robustness import EXTRA_COLUMNS
from scripts.evaluate_ri_gmappo_3d import (
    CSV_COLUMNS,
    first_step_where,
    mean_metric,
    post_failure_recovery_metrics,
)
from scripts.pretrain_ri_gmappo_3d_bc import geometric_policy


@dataclass(frozen=True)
class NodeFailureScenario:
    name: str
    failed_blue_agent: int
    node_failure_start_step: int = 40
    node_failure_duration_steps: int = 80


SCENARIOS = {
    "relay_failure": NodeFailureScenario("relay_failure", failed_blue_agent=1),
    "scout_failure": NodeFailureScenario("scout_failure", failed_blue_agent=0),
}

METRICS = (
    "success",
    "post_failure_chain_recovered",
    "post_failure_chain_recovery_steps",
    "tracking_during_failure_rate",
    "connectivity_during_failure",
    "steps",
    "timeout",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate the 3DOF geometric controller under temporary communication-node failures."
    )
    parser.add_argument("--seeds", nargs="+", type=int, default=(0, 1, 2))
    parser.add_argument("--episodes", type=int, default=30)
    parser.add_argument("--eval-base-seed", type=int, default=91_000)
    parser.add_argument("--target-policy", type=str, default="straight")
    parser.add_argument("--strict-target-sensing", action="store_true")
    parser.add_argument("--agent-target-info-bottleneck", action="store_true")
    parser.add_argument("--max-target-message-age-steps", type=int, default=80)
    parser.add_argument("--min-target-confidence", type=float, default=0.2)
    parser.add_argument("--scenarios", nargs="+", choices=tuple(SCENARIOS), default=tuple(SCENARIOS))
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "results" / "intercept_3d_geometric_node_failure_eval",
    )
    return parser.parse_args()


def make_config(args: argparse.Namespace, scenario: NodeFailureScenario, seed: int) -> RIGMAPPOConfig:
    return RIGMAPPOConfig(
        env_name="3d_intercept",
        seed=seed,
        target_policy=args.target_policy,
        strict_target_sensing=args.strict_target_sensing,
        agent_target_info_bottleneck=args.agent_target_info_bottleneck,
        max_target_message_age_steps=args.max_target_message_age_steps,
        min_target_confidence=args.min_target_confidence,
        failed_blue_agent=scenario.failed_blue_agent,
        node_failure_start_step=scenario.node_failure_start_step,
        node_failure_duration_steps=scenario.node_failure_duration_steps,
    )


def evaluate_episode(
    args: argparse.Namespace,
    scenario: NodeFailureScenario,
    train_seed: int,
    episode: int,
) -> dict[str, object]:
    eval_seed = args.eval_base_seed + train_seed * 1_000 + episode
    cfg = make_config(args, scenario, eval_seed)
    env = make_env(cfg, eval_seed, training=False)
    env.reset()
    step_infos: list[dict[str, float]] = []
    reward_sum = 0.0
    final_info: dict[str, float] | None = None

    while True:
        _, _, _, rewards, dones, info = env.step(geometric_policy(env))
        step_infos.append(info)
        reward_sum += float(np.sum(rewards))
        if np.all(dones):
            final_info = info
            break

    assert final_info is not None
    recovery_args = argparse.Namespace(
        failed_blue_agent=scenario.failed_blue_agent,
        node_failure_start_step=scenario.node_failure_start_step,
        node_failure_duration_steps=scenario.node_failure_duration_steps,
    )
    recovery = post_failure_recovery_metrics(step_infos, recovery_args)

    row: dict[str, object] = {
        "scenario": scenario.name,
        "graph_encoder": "geometric",
        "train_method": "rule",
        "train_seed": train_seed,
        "method": "Geometric heuristic",
        "checkpoint": "not_applicable",
        "policy_source": "geometric_controller",
        "seed": eval_seed,
        "episode": episode,
        "episodes": args.episodes,
        "target_policy": args.target_policy,
        "communication_range_scale": 1.0,
        "communication_dropout_prob": 0.0,
        "message_delay_steps": 0,
        "radar_dropout_prob": 0.0,
        "strict_target_sensing": int(args.strict_target_sensing),
        "agent_target_info_bottleneck": int(args.agent_target_info_bottleneck),
        "max_target_message_age_steps": args.max_target_message_age_steps,
        "min_target_confidence": args.min_target_confidence,
        "failed_blue_agent": scenario.failed_blue_agent,
        "node_failure_start_step": scenario.node_failure_start_step,
        "node_failure_duration_steps": scenario.node_failure_duration_steps,
        "graph_relation_ablation": "none",
        "graph_message_ablation": "none",
        "graph_input_ablation": "none",
        "deterministic": True,
        "success": float(final_info["success"]),
        "chain_closed": float(final_info["chain_closed"]),
        "attack_window_formed": float(first_step_where(step_infos, "attack_window_rate") >= 0.0),
        "attack_window_rate": mean_metric(step_infos, "attack_window_rate"),
        "tracking_rate": mean_metric(step_infos, "tracking_rate"),
        "comm_connectivity": mean_metric(step_infos, "comm_connectivity"),
        "mean_message_age": mean_metric(step_infos, "mean_message_age"),
        "collision": float(final_info["collision"]),
        "timeout": float(final_info["timeout"]),
        "constraint_violation": float(final_info["constraint_violation"]),
        "steps": float(final_info["step"]),
        "first_attack_window_step": first_step_where(step_infos, "attack_window_rate"),
        "first_chain_close_step": first_step_where(step_infos, "chain_closed", threshold=0.5),
        "avg_mean_range": mean_metric(step_infos, "mean_range"),
        "final_mean_range": float(final_info["mean_range"]),
        "reward_sum": reward_sum,
    }
    row.update(recovery)
    return row


def run_suite(args: argparse.Namespace) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for scenario_name in args.scenarios:
        scenario = SCENARIOS[scenario_name]
        for train_seed in args.seeds:
            for episode in range(args.episodes):
                rows.append(evaluate_episode(args, scenario, train_seed, episode))
    return rows


def write_episode_csv(rows: list[dict[str, object]], out_csv: Path) -> None:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = (*EXTRA_COLUMNS, *CSV_COLUMNS)
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_summary(rows: list[dict[str, object]], out_md: Path, args: argparse.Namespace) -> None:
    per_seed: dict[tuple[str, int], dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        key = (str(row["scenario"]), int(row["train_seed"]))
        for metric in METRICS:
            per_seed[key][metric].append(float(row[metric]))

    grouped: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for (scenario, _seed), values in per_seed.items():
        for metric, samples in values.items():
            grouped[scenario][metric].append(float(np.mean(samples)))

    lines = [
        "# 3DOF Geometric Node-Failure Evaluation",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "## Protocol",
        "",
        "```text",
        f"target_policy = {args.target_policy}",
        f"strict_target_sensing = {args.strict_target_sensing}",
        f"agent_target_info_bottleneck = {args.agent_target_info_bottleneck}",
        f"max_target_message_age_steps = {args.max_target_message_age_steps}",
        f"min_target_confidence = {args.min_target_confidence}",
        f"scenarios = {list(args.scenarios)}",
        f"replicate_seeds = {list(args.seeds)}",
        f"episodes_per_replicate = {args.episodes}",
        "node_failure = one blue communication node disabled for 80 steps starting at step 40",
        "controller = deterministic geometric pursuit policy, no training",
        "```",
        "",
        "## Seed-Mean Summary",
        "",
        "| Scenario | Success | Recovered | Recovery Steps | Tracking During Failure | Connectivity During Failure | Timeout | Steps |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for scenario in args.scenarios:
        values = grouped[scenario]

        def mean_std(metric: str) -> str:
            samples = values[metric]
            return f"{float(np.mean(samples)):.3f} +/- {float(np.std(samples, ddof=0)):.3f}"

        lines.append(
            f"| {scenario} | {mean_std('success')} | {mean_std('post_failure_chain_recovered')} | "
            f"{mean_std('post_failure_chain_recovery_steps')} | {mean_std('tracking_during_failure_rate')} | "
            f"{mean_std('connectivity_during_failure')} | {mean_std('timeout')} | {mean_std('steps')} |"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "```text",
            "This is a rule-based reference under the same node-failure evaluation protocol.",
            "It should be used as a compact baseline, not as evidence for graph-message mechanisms.",
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
        raise RuntimeError("no geometric node-failure rows were produced")
    out_csv = args.out_dir / "episode_metrics.csv"
    out_md = args.out_dir / "summary.md"
    write_episode_csv(rows, out_csv)
    write_summary(rows, out_md, args)
    print(out_csv)
    print(out_md)
    print(f"episodes: {len(rows)}")


if __name__ == "__main__":
    main()
