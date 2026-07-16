from __future__ import annotations

import argparse
import csv
import math
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.simple_ri_gmappo import RIGMAPPOConfig, make_env
from scripts.evaluate_ri_gmappo_3d import CSV_COLUMNS
from scripts.pretrain_ri_gmappo_3d_bc import geometric_policy


LEARNED_METHODS = ("from_scratch", "bc_only", "bc_ppo")
ALL_METHODS = ("geometric", *LEARNED_METHODS)
METHOD_LABELS = {
    "geometric": "Geometric controller",
    "from_scratch": "RI-GMAPPO from scratch",
    "bc_only": "RI-GMAPPO BC-only",
    "bc_ppo": "RI-GMAPPO BC-to-PPO",
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run matched-seed 3DOF straight-target baseline diagnostics."
    )
    parser.add_argument("--seeds", nargs="+", type=int, default=(0, 1, 2))
    parser.add_argument("--methods", nargs="+", choices=ALL_METHODS, default=ALL_METHODS)
    parser.add_argument("--eval-episodes", type=int, default=30)
    parser.add_argument("--eval-base-seed", type=int, default=40_000)
    parser.add_argument("--target-policy", type=str, default="straight")
    parser.add_argument("--strict-target-sensing", action="store_true")
    parser.add_argument("--graph-encoder", choices=("single", "multi_relation"), default="single")
    parser.add_argument("--graph-relation-ablation", choices=("none", "no_task_support"), default="none")
    parser.add_argument("--graph-message-ablation", choices=("none", "no_role_pair_gate"), default="none")
    parser.add_argument("--graph-input-ablation", choices=("none", "no_edge_features", "no_role_identity"), default="none")
    parser.add_argument("--bc-episodes", type=int, default=200)
    parser.add_argument("--bc-epochs", type=int, default=80)
    parser.add_argument("--ppo-updates", type=int, default=60)
    parser.add_argument("--ppo-lr", type=float, default=1e-4)
    parser.add_argument("--entropy-coef", type=float, default=0.01)
    parser.add_argument("--num-envs", type=int, default=4)
    parser.add_argument("--rollout-steps", type=int, default=64)
    parser.add_argument("--device", type=str, default="cpu")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "results" / "intercept_3d_baseline_protocol")
    parser.add_argument("--skip-existing", action="store_true")
    return parser.parse_args()


def run_command(command: list[str]) -> None:
    print("$", " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def checkpoint_path(out_dir: Path, method: str, seed: int) -> Path:
    return out_dir / "runs" / f"{method}_seed{seed}" / "actor_critic_best.pt"


def latest_checkpoint_path(out_dir: Path, method: str, seed: int) -> Path:
    return out_dir / "runs" / f"{method}_seed{seed}" / "actor_critic_latest.pt"


def evaluate_geometric(args: argparse.Namespace, seed: int) -> list[dict[str, float | int | str | bool]]:
    cfg = RIGMAPPOConfig(
        env_name="3d_intercept",
        seed=seed,
        target_policy=args.target_policy,
        strict_target_sensing=args.strict_target_sensing,
    )
    rows: list[dict[str, float | int | str | bool]] = []
    for episode in range(args.eval_episodes):
        eval_seed = args.eval_base_seed + seed * 1_000 + episode
        env = make_env(cfg, eval_seed, training=False)
        _, _, _ = env.reset()
        infos: list[dict[str, float]] = []
        reward_sum = 0.0
        while True:
            _, _, _, rewards, dones, info = env.step(geometric_policy(env))
            infos.append(info)
            reward_sum += float(np.sum(rewards))
            if np.all(dones):
                rows.append(
                    {
                        "method": METHOD_LABELS["geometric"],
                        "checkpoint": "not_applicable",
                        "policy_source": "geometric_controller",
                        "seed": seed,
                        "episode": episode,
                        "episodes": args.eval_episodes,
                        "target_policy": args.target_policy,
                        "communication_dropout_prob": 0.0,
                        "message_delay_steps": 0,
                        "radar_dropout_prob": 0.0,
                        "deterministic": True,
                        "success": float(info["success"]),
                        "chain_closed": float(info["chain_closed"]),
                        "attack_window_formed": float(max(x["attack_window_rate"] for x in infos) > 0.0),
                        "attack_window_rate": float(np.mean([x["attack_window_rate"] for x in infos])),
                        "tracking_rate": float(np.mean([x["tracking_rate"] for x in infos])),
                        "comm_connectivity": float(np.mean([x["comm_connectivity"] for x in infos])),
                        "mean_message_age": float(np.mean([x["mean_message_age"] for x in infos])),
                        "collision": float(info["collision"]),
                        "timeout": float(info["timeout"]),
                        "constraint_violation": float(info["constraint_violation"]),
                        "steps": float(info["step"]),
                        "avg_mean_range": float(np.mean([x["mean_range"] for x in infos])),
                        "final_mean_range": float(info["mean_range"]),
                        "reward_sum": reward_sum,
                    }
                )
                break
    return rows


def read_rows(path: Path, method: str, training_seed: int) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        row["method"] = METHOD_LABELS[method]
        row["seed"] = str(training_seed)
    return rows


def train_seed(args: argparse.Namespace, seed: int) -> dict[str, list[dict[str, str]]]:
    run_root = args.out_dir / "runs"
    bc_dir = run_root / f"bc_only_seed{seed}"
    ppo_dir = run_root / f"bc_ppo_seed{seed}"
    scratch_dir = run_root / f"from_scratch_seed{seed}"

    needs_bc = "bc_only" in args.methods or "bc_ppo" in args.methods
    if needs_bc and not (args.skip_existing and latest_checkpoint_path(args.out_dir, "bc_only", seed).exists()):
        run_command(
            [
                sys.executable,
                "-B",
                "scripts/pretrain_ri_gmappo_3d_bc.py",
                "--seed",
                str(seed),
                "--target-policy",
                args.target_policy,
                *(("--strict-target-sensing",) if args.strict_target_sensing else ()),
                "--graph-encoder",
                args.graph_encoder,
                "--graph-relation-ablation",
                args.graph_relation_ablation,
                "--graph-message-ablation",
                args.graph_message_ablation,
                "--graph-input-ablation",
                args.graph_input_ablation,
                "--episodes",
                str(args.bc_episodes),
                "--epochs",
                str(args.bc_epochs),
                "--hidden-dim",
                "64",
                "--no-balanced-loss",
                "--device",
                args.device,
                "--out-dir",
                str(bc_dir),
            ]
        )

    common_train = [
        "--seed",
        str(seed),
        "--env-name",
        "3d_intercept",
        "--target-policy",
        args.target_policy,
        *(("--strict-target-sensing",) if args.strict_target_sensing else ()),
        "--graph-encoder",
        args.graph_encoder,
        "--graph-relation-ablation",
        args.graph_relation_ablation,
        "--graph-message-ablation",
        args.graph_message_ablation,
        "--graph-input-ablation",
        args.graph_input_ablation,
        "--updates",
        str(args.ppo_updates),
        "--num-envs",
        str(args.num_envs),
        "--rollout-steps",
        str(args.rollout_steps),
        "--eval-episodes",
        "5",
        "--eval-interval",
        "10",
        "--save-interval",
        "10",
        "--hidden-dim",
        "64",
        "--intent-coef",
        "0.0",
        "--lr",
        str(args.ppo_lr),
        "--entropy-coef",
        str(args.entropy_coef),
        "--device",
        args.device,
    ]
    if "from_scratch" in args.methods and not (args.skip_existing and latest_checkpoint_path(args.out_dir, "from_scratch", seed).exists()):
        run_command([sys.executable, "-B", "scripts/train_ri_gmappo.py", *common_train, "--out-dir", str(scratch_dir)])
    if "bc_ppo" in args.methods and not (args.skip_existing and latest_checkpoint_path(args.out_dir, "bc_ppo", seed).exists()):
        run_command(
            [
                sys.executable,
                "-B",
                "scripts/train_ri_gmappo.py",
                *common_train,
                "--resume",
                str(checkpoint_path(args.out_dir, "bc_only", seed)),
                "--out-dir",
                str(ppo_dir),
            ]
        )

    rows: dict[str, list[dict[str, str]]] = {}
    for method in LEARNED_METHODS:
        if method not in args.methods:
            continue
        csv_path = args.out_dir / "per_seed" / f"{method}_seed{seed}.csv"
        summary_path = args.out_dir / "per_seed" / f"{method}_seed{seed}.md"
        if not (args.skip_existing and csv_path.exists()):
            run_command(
                [
                    sys.executable,
                    "-B",
                    "scripts/evaluate_ri_gmappo_3d.py",
                    "--checkpoint",
                    str(checkpoint_path(args.out_dir, method, seed)),
                    "--episodes",
                    str(args.eval_episodes),
                    "--seed",
                    str(seed),
                    "--base-seed",
                    str(args.eval_base_seed + seed * 1_000),
                    "--target-policy",
                    args.target_policy,
                    *(("--strict-target-sensing",) if args.strict_target_sensing else ()),
                    "--graph-encoder",
                    args.graph_encoder,
                    "--graph-relation-ablation",
                    args.graph_relation_ablation,
                    "--graph-message-ablation",
                    args.graph_message_ablation,
                    "--graph-input-ablation",
                    args.graph_input_ablation,
                    "--device",
                    args.device,
                    "--out-csv",
                    str(csv_path),
                    "--summary-md",
                    str(summary_path),
                ]
            )
        rows[method] = read_rows(csv_path, method, seed)
    return rows


def write_outputs(args: argparse.Namespace, rows: list[dict[str, str | float | int | bool]]) -> None:
    args.out_dir.mkdir(parents=True, exist_ok=True)
    raw_path = args.out_dir / "episode_metrics.csv"
    with raw_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    grouped: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    by_seed: dict[tuple[str, str], list[dict[str, str | float | int | bool]]] = defaultdict(list)
    for row in rows:
        by_seed[(str(row["method"]), str(row["seed"]))].append(row)
    for (method, _), items in by_seed.items():
        for metric in METRICS:
            grouped[method][metric].append(float(np.mean([float(row[metric]) for row in items])))

    summary_path = args.out_dir / "summary.csv"
    fields = ["method", "replicates", "episodes_per_replicate"] + [f"{metric}_{suffix}" for metric in METRICS for suffix in ("mean", "std")]
    summary_rows = []
    for method in dict.fromkeys(METHOD_LABELS[name] for name in args.methods):
        values = grouped[method]
        row: dict[str, str | float | int] = {
            "method": method,
            "replicates": len(by_seed) and len({seed for name, seed in by_seed if name == method}),
            "episodes_per_replicate": args.eval_episodes,
        }
        for metric in METRICS:
            samples = values[metric]
            row[f"{metric}_mean"] = float(np.mean(samples))
            row[f"{metric}_std"] = float(np.std(samples, ddof=1)) if len(samples) > 1 else 0.0
        summary_rows.append(row)
    with summary_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(summary_rows)

    lines = [
        "# 3DOF Straight-Target Baseline Protocol",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "## Protocol",
        "",
        "```text",
        f"training/evaluation replicate seeds = {list(args.seeds)}",
        f"methods = {list(args.methods)}",
        f"evaluation episodes per replicate = {args.eval_episodes}",
        f"target policy = {args.target_policy}",
        f"strict target sensing = {args.strict_target_sensing}",
        f"graph encoder = {args.graph_encoder}",
        f"graph relation ablation = {args.graph_relation_ablation}",
        f"graph message ablation = {args.graph_message_ablation}",
        f"graph input ablation = {args.graph_input_ablation}",
        f"BC = {args.bc_episodes} demonstration episodes, {args.bc_epochs} epochs, unweighted cross entropy",
        f"PPO = {args.ppo_updates} updates, {args.num_envs} environments, {args.rollout_steps} rollout steps, learning rate {args.ppo_lr}",
        f"PPO entropy coefficient = {args.entropy_coef}",
        "All learned methods use the same 64-dimensional network and 3DOF environment settings.",
        "The geometric controller has no training seed; its replicate rows use the same evaluation seed blocks.",
        "```",
        "",
        "## Aggregate Results",
        "",
        "| Method | Success | Chain Closed | Attack Window | Tracking | Collision | Constraint | Steps |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary_rows:
        lines.append(
            f"| {row['method']} | {row['success_mean']:.3f} +/- {row['success_std']:.3f} | "
            f"{row['chain_closed_mean']:.3f} +/- {row['chain_closed_std']:.3f} | "
            f"{row['attack_window_formed_mean']:.3f} +/- {row['attack_window_formed_std']:.3f} | "
            f"{row['tracking_rate_mean']:.3f} +/- {row['tracking_rate_std']:.3f} | "
            f"{row['collision_mean']:.3f} +/- {row['collision_std']:.3f} | "
            f"{row['constraint_violation_mean']:.3f} +/- {row['constraint_violation_std']:.3f} | "
            f"{row['steps_mean']:.1f} +/- {row['steps_std']:.1f} |"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "```text",
            "This protocol validates the 3DOF straight-target training curriculum only.",
            "It is a baseline prerequisite, not evidence for the multi-relation graph or topology-curriculum contribution.",
            "```",
            "",
        ]
    )
    (args.out_dir / "summary.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    all_rows: list[dict[str, str | float | int | bool]] = []
    for seed in args.seeds:
        print(f"=== replicate seed {seed} ===", flush=True)
        if "geometric" in args.methods:
            all_rows.extend(evaluate_geometric(args, seed))
        learned = train_seed(args, seed)
        for method in LEARNED_METHODS:
            if method in args.methods:
                all_rows.extend(learned[method])
    write_outputs(args, all_rows)
    print(args.out_dir / "episode_metrics.csv")
    print(args.out_dir / "summary.csv")
    print(args.out_dir / "summary.md")


if __name__ == "__main__":
    main()
