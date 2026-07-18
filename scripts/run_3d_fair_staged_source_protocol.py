from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare fair staged source checkpoints for strict-sensing 3DOF baselines."
    )
    parser.add_argument("--seeds", nargs="+", type=int, default=(0,))
    parser.add_argument(
        "--graph-encoders",
        nargs="+",
        choices=("no_graph", "single", "multi_relation"),
        default=("no_graph", "single", "multi_relation"),
    )
    parser.add_argument("--target-policy", type=str, default="straight")
    parser.add_argument("--bc-episodes", type=int, default=8)
    parser.add_argument("--bc-epochs", type=int, default=1)
    parser.add_argument("--nominal-updates", type=int, default=1)
    parser.add_argument("--curriculum-updates", type=int, default=1)
    parser.add_argument("--strict-updates", type=int, default=1)
    parser.add_argument("--num-envs", type=int, default=1)
    parser.add_argument("--rollout-steps", type=int, default=8)
    parser.add_argument("--hidden-dim", type=int, default=64)
    parser.add_argument("--lr", type=float, default=5e-5)
    parser.add_argument("--entropy-coef", type=float, default=0.001)
    parser.add_argument("--save-interval", type=int, default=1)
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
    parser.add_argument("--strict-validation-episodes", type=int, default=1)
    parser.add_argument("--strict-test-episodes", type=int, default=1)
    parser.add_argument("--strict-validation-base-seed", type=int, default=320_000)
    parser.add_argument("--strict-test-base-seed", type=int, default=330_000)
    parser.add_argument("--device", type=str, default="cpu")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "results" / "intercept_3d_fair_staged_source_smoke")
    parser.add_argument("--skip-existing", action="store_true")
    parser.add_argument("--skip-strict-smoke", action="store_true")
    return parser.parse_args()


def run_command(command: list[str]) -> None:
    print("$", " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def bc_dir(args: argparse.Namespace, graph_encoder: str, seed: int) -> Path:
    return args.out_dir / "stage1_bc" / graph_encoder / f"seed{seed}"


def nominal_dir(args: argparse.Namespace, graph_encoder: str, seed: int) -> Path:
    return args.out_dir / "stage2_nominal" / "runs" / graph_encoder / f"bc_ppo_seed{seed}"


def curriculum_dir(args: argparse.Namespace, graph_encoder: str, seed: int) -> Path:
    return args.out_dir / "stage3_curriculum" / "runs" / graph_encoder / f"bc_ppo_seed{seed}"


def train_bc(args: argparse.Namespace, graph_encoder: str, seed: int) -> Path:
    checkpoint = bc_dir(args, graph_encoder, seed) / "actor_critic_best.pt"
    if args.skip_existing and checkpoint.exists():
        print(f"skip existing BC checkpoint: {checkpoint}", flush=True)
        return checkpoint
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
            "--graph-encoder",
            graph_encoder,
            "--device",
            args.device,
            "--out-dir",
            str(bc_dir(args, graph_encoder, seed)),
        ]
    )
    return checkpoint


def train_nominal(args: argparse.Namespace, graph_encoder: str, seed: int, checkpoint: Path) -> Path:
    output = nominal_dir(args, graph_encoder, seed) / "actor_critic_best.pt"
    if args.skip_existing and output.exists():
        print(f"skip existing nominal checkpoint: {output}", flush=True)
        return output
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
            "--graph-encoder",
            graph_encoder,
            "--updates",
            str(args.nominal_updates),
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
            "--hidden-dim",
            str(args.hidden_dim),
            "--intent-coef",
            "0.0",
            "--lr",
            str(args.lr),
            "--entropy-coef",
            str(args.entropy_coef),
            "--device",
            args.device,
            "--resume",
            str(checkpoint),
            "--out-dir",
            str(nominal_dir(args, graph_encoder, seed)),
        ]
    )
    return output


def train_curriculum(args: argparse.Namespace, graph_encoder: str, seed: int, checkpoint: Path) -> Path:
    output = curriculum_dir(args, graph_encoder, seed) / "actor_critic_best.pt"
    if args.skip_existing and output.exists():
        print(f"skip existing curriculum checkpoint: {output}", flush=True)
        return output
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
            "--graph-encoder",
            graph_encoder,
            "--updates",
            str(args.curriculum_updates),
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
            str(checkpoint),
            "--out-dir",
            str(curriculum_dir(args, graph_encoder, seed)),
        ]
    )
    return output


def run_strict_smoke(args: argparse.Namespace) -> None:
    strict_dir = args.out_dir / "stage4_strict_smoke"
    run_command(
        [
            sys.executable,
            "-B",
            "scripts/run_3d_strict_sensing_formal_protocol.py",
            "--seeds",
            *[str(seed) for seed in args.seeds],
            "--graph-encoders",
            *args.graph_encoders,
            "--source-no-graph-root",
            str(args.out_dir / "stage3_curriculum" / "runs" / "no_graph"),
            "--source-single-root",
            str(args.out_dir / "stage3_curriculum" / "runs" / "single"),
            "--source-multi-root",
            str(args.out_dir / "stage3_curriculum" / "runs" / "multi_relation"),
            "--updates",
            str(args.strict_updates),
            "--num-envs",
            str(args.num_envs),
            "--rollout-steps",
            str(args.rollout_steps),
            "--hidden-dim",
            str(args.hidden_dim),
            "--lr",
            str(args.lr),
            "--entropy-coef",
            str(args.entropy_coef),
            "--save-interval",
            str(args.save_interval),
            "--validation-episodes",
            str(args.strict_validation_episodes),
            "--test-episodes",
            str(args.strict_test_episodes),
            "--validation-base-seed",
            str(args.strict_validation_base_seed),
            "--test-base-seed",
            str(args.strict_test_base_seed),
            "--target-policy",
            args.target_policy,
            "--device",
            args.device,
            "--out-dir",
            str(strict_dir),
            "--skip-existing",
        ]
    )


def write_protocol(args: argparse.Namespace) -> None:
    args.out_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Fair Staged Source Protocol Run",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "This run prepares comparable source checkpoints before strict-sensing fine-tuning.",
        "",
        "```text",
        f"seeds = {list(args.seeds)}",
        f"graph_encoders = {list(args.graph_encoders)}",
        f"bc_episodes = {args.bc_episodes}",
        f"bc_epochs = {args.bc_epochs}",
        f"nominal_updates = {args.nominal_updates}",
        f"curriculum_updates = {args.curriculum_updates}",
        f"strict_updates = {args.strict_updates}",
        f"num_envs = {args.num_envs}",
        f"rollout_steps = {args.rollout_steps}",
        f"skip_strict_smoke = {args.skip_strict_smoke}",
        "```",
        "",
        "Directory layout:",
        "",
        "```text",
        "stage1_bc/<graph_encoder>/seed<seed>/actor_critic_best.pt",
        "stage2_nominal/runs/<graph_encoder>/bc_ppo_seed<seed>/actor_critic_best.pt",
        "stage3_curriculum/runs/<graph_encoder>/bc_ppo_seed<seed>/actor_critic_best.pt",
        "stage4_strict_smoke/...",
        "```",
        "",
    ]
    (args.out_dir / "protocol.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    write_protocol(args)
    for graph_encoder in args.graph_encoders:
        for seed in args.seeds:
            print(f"=== staged source {graph_encoder} seed {seed} ===", flush=True)
            bc_checkpoint = train_bc(args, graph_encoder, seed)
            nominal_checkpoint = train_nominal(args, graph_encoder, seed, bc_checkpoint)
            train_curriculum(args, graph_encoder, seed, nominal_checkpoint)
    if not args.skip_strict_smoke:
        run_strict_smoke(args)
    print(args.out_dir / "protocol.md")


if __name__ == "__main__":
    main()
