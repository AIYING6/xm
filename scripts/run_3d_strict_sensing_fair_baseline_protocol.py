from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Smoke-validate fair strict-sensing 3DOF baselines with the same BC, "
            "topology curriculum, validation selection, and disjoint test protocol."
        )
    )
    parser.add_argument("--seeds", nargs="+", type=int, default=(0,))
    parser.add_argument(
        "--graph-encoders",
        nargs="+",
        choices=("no_graph", "single", "multi_relation"),
        default=("no_graph", "single", "multi_relation"),
    )
    parser.add_argument("--bc-episodes", type=int, default=12)
    parser.add_argument("--bc-epochs", type=int, default=2)
    parser.add_argument("--updates", type=int, default=2)
    parser.add_argument("--num-envs", type=int, default=2)
    parser.add_argument("--rollout-steps", type=int, default=16)
    parser.add_argument("--hidden-dim", type=int, default=64)
    parser.add_argument("--lr", type=float, default=5e-5)
    parser.add_argument("--entropy-coef", type=float, default=0.001)
    parser.add_argument("--save-interval", type=int, default=1)
    parser.add_argument("--target-policy", type=str, default="straight")
    parser.add_argument("--communication-range-random-min", type=float, default=0.65)
    parser.add_argument("--communication-range-random-max", type=float, default=1.00)
    parser.add_argument("--communication-dropout-random-min", type=float, default=0.00)
    parser.add_argument("--communication-dropout-random-max", type=float, default=0.20)
    parser.add_argument("--message-delay-random-min", type=int, default=0)
    parser.add_argument("--message-delay-random-max", type=int, default=2)
    parser.add_argument("--radar-dropout-random-min", type=float, default=0.00)
    parser.add_argument("--radar-dropout-random-max", type=float, default=0.15)
    parser.add_argument("--node-failure-random-prob", type=float, default=0.75)
    parser.add_argument("--node-failure-start-random-min", type=int, default=30)
    parser.add_argument("--node-failure-start-random-max", type=int, default=60)
    parser.add_argument("--node-failure-duration-random-min", type=int, default=60)
    parser.add_argument("--node-failure-duration-random-max", type=int, default=100)
    parser.add_argument("--validation-episodes", type=int, default=3)
    parser.add_argument("--test-episodes", type=int, default=3)
    parser.add_argument("--validation-base-seed", type=int, default=220_000)
    parser.add_argument("--test-base-seed", type=int, default=230_000)
    parser.add_argument("--scenarios", nargs="+", choices=("relay_failure", "scout_failure"), default=("relay_failure",))
    parser.add_argument("--device", type=str, default="cpu")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "results" / "intercept_3d_strict_sensing_fair_baselines")
    parser.add_argument("--skip-existing", action="store_true")
    parser.add_argument("--train-only", action="store_true")
    parser.add_argument("--eval-only", action="store_true")
    parser.add_argument("--test-only", action="store_true")
    return parser.parse_args()


def run_command(command: list[str]) -> None:
    print("$", " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def bc_dir(args: argparse.Namespace, graph_encoder: str, seed: int) -> Path:
    return args.out_dir / "bc" / graph_encoder / f"seed{seed}"


def run_dir(args: argparse.Namespace, graph_encoder: str, seed: int) -> Path:
    return args.out_dir / "runs" / graph_encoder / f"bc_ppo_seed{seed}"


def final_snapshot(args: argparse.Namespace, graph_encoder: str, seed: int) -> Path:
    return run_dir(args, graph_encoder, seed) / f"actor_critic_update_{args.updates:04d}.pt"


def train_one(args: argparse.Namespace, graph_encoder: str, seed: int) -> None:
    bc_checkpoint = bc_dir(args, graph_encoder, seed) / "actor_critic_best.pt"
    if not (args.skip_existing and bc_checkpoint.exists()):
        run_command(
            [
                sys.executable,
                "-B",
                "scripts/pretrain_ri_gmappo_3d_bc.py",
                "--seed",
                str(seed),
                "--episodes",
                str(args.bc_episodes),
                "--epochs",
                str(args.bc_epochs),
                "--hidden-dim",
                str(args.hidden_dim),
                "--target-policy",
                args.target_policy,
                "--strict-target-sensing",
                "--graph-encoder",
                graph_encoder,
                "--device",
                args.device,
                "--out-dir",
                str(bc_dir(args, graph_encoder, seed)),
            ]
        )
    if args.skip_existing and final_snapshot(args, graph_encoder, seed).exists():
        print(f"skip existing fair-baseline PPO run: {final_snapshot(args, graph_encoder, seed)}", flush=True)
        return
    run_command(
        [
            sys.executable,
            "-B",
            "scripts/train_ri_gmappo.py",
            "--seed",
            str(seed),
            "--env-name",
            "3d_intercept",
            "--target-policy",
            args.target_policy,
            "--strict-target-sensing",
            "--graph-encoder",
            graph_encoder,
            "--updates",
            str(args.updates),
            "--num-envs",
            str(args.num_envs),
            "--rollout-steps",
            str(args.rollout_steps),
            "--eval-episodes",
            "2",
            "--eval-interval",
            str(args.save_interval),
            "--save-interval",
            str(args.save_interval),
            "--save-snapshots",
            "--hidden-dim",
            str(args.hidden_dim),
            "--intent-coef",
            "0.0",
            "--lr",
            str(args.lr),
            "--entropy-coef",
            str(args.entropy_coef),
            "--communication-range-random-min",
            str(args.communication_range_random_min),
            "--communication-range-random-max",
            str(args.communication_range_random_max),
            "--communication-dropout-random-min",
            str(args.communication_dropout_random_min),
            "--communication-dropout-random-max",
            str(args.communication_dropout_random_max),
            "--message-delay-random-min",
            str(args.message_delay_random_min),
            "--message-delay-random-max",
            str(args.message_delay_random_max),
            "--radar-dropout-random-min",
            str(args.radar_dropout_random_min),
            "--radar-dropout-random-max",
            str(args.radar_dropout_random_max),
            "--node-failure-random-prob",
            str(args.node_failure_random_prob),
            "--node-failure-start-random-min",
            str(args.node_failure_start_random_min),
            "--node-failure-start-random-max",
            str(args.node_failure_start_random_max),
            "--node-failure-duration-random-min",
            str(args.node_failure_duration_random_min),
            "--node-failure-duration-random-max",
            str(args.node_failure_duration_random_max),
            "--device",
            args.device,
            "--resume",
            str(bc_checkpoint),
            "--out-dir",
            str(run_dir(args, graph_encoder, seed)),
        ]
    )


def evaluate_split(args: argparse.Namespace, split: str, episodes: int, base_seed: int, selection_csv: Path | None) -> None:
    command = [
        sys.executable,
        "-B",
        "scripts/evaluate_3d_checkpoint_sweep.py",
        "--split",
        split,
        "--seeds",
        *[str(seed) for seed in args.seeds],
        "--graph-encoders",
        *args.graph_encoders,
        "--scenarios",
        *args.scenarios,
        "--episodes",
        str(episodes),
        "--base-seed",
        str(base_seed),
        "--target-policy",
        args.target_policy,
        "--strict-target-sensing",
        "--no-graph-root",
        str(args.out_dir / "runs" / "no_graph"),
        "--single-root",
        str(args.out_dir / "runs" / "single"),
        "--multi-root",
        str(args.out_dir / "runs" / "multi_relation"),
        "--device",
        args.device,
        "--out-dir",
        str(args.out_dir / "checkpoint_sweep"),
    ]
    if selection_csv is not None:
        command.extend(["--selection-csv", str(selection_csv)])
    run_command(command)


def write_protocol(args: argparse.Namespace) -> None:
    args.out_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Fair Strict-Sensing 3DOF Baseline Protocol",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "This protocol is smoke-scale by default. It exists to validate that `no_graph`, `single`, and `multi_relation` baselines can use the same BC initialization, topology curriculum, validation checkpoint selection, and disjoint test split.",
        "",
        "## Configuration",
        "",
        "```text",
        f"seeds = {list(args.seeds)}",
        f"graph_encoders = {list(args.graph_encoders)}",
        f"bc_episodes = {args.bc_episodes}",
        f"bc_epochs = {args.bc_epochs}",
        f"updates = {args.updates}",
        f"save_interval = {args.save_interval}",
        f"validation_episodes = {args.validation_episodes}",
        f"test_episodes = {args.test_episodes}",
        f"scenarios = {list(args.scenarios)}",
        "strict_target_sensing = True",
        "```",
        "",
        "## Baseline Meaning",
        "",
        "- `no_graph`: centralized-training/decentralized-execution MAPPO-style actor without graph message passing.",
        "- `single`: single union-graph GAT-MAPPO baseline.",
        "- `multi_relation`: proposed multi-relation EA-RG-MAPPO-S variant.",
        "",
        "## Formal Expansion",
        "",
        "After this smoke path passes, increase to at least five training seeds, 100--120 PPO updates, validation episodes 50, and test episodes 100. Do not use test rows for checkpoint selection.",
        "",
    ]
    (args.out_dir / "protocol.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    write_protocol(args)
    if not args.eval_only and not args.test_only:
        for graph_encoder in args.graph_encoders:
            for seed in args.seeds:
                print(f"=== fair strict sensing {graph_encoder} seed {seed} ===", flush=True)
                train_one(args, graph_encoder, seed)
    if not args.train_only and not args.test_only:
        evaluate_split(args, "validation", args.validation_episodes, args.validation_base_seed, None)
    if not args.train_only:
        selection_csv = args.out_dir / "checkpoint_sweep" / "validation_selected_checkpoints.csv"
        evaluate_split(args, "test", args.test_episodes, args.test_base_seed, selection_csv)
    print(args.out_dir / "protocol.md")


if __name__ == "__main__":
    main()
