from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the 3DOF no-role-pair-gate ablation through matched baseline, topology curriculum, and node-failure evaluation."
    )
    parser.add_argument("--seeds", nargs="+", type=int, default=(0, 1, 2))
    parser.add_argument("--target-policy", type=str, default="straight")
    parser.add_argument("--bc-episodes", type=int, default=200)
    parser.add_argument("--bc-epochs", type=int, default=80)
    parser.add_argument("--baseline-ppo-updates", type=int, default=60)
    parser.add_argument("--topology-updates", type=int, default=20)
    parser.add_argument("--num-envs", type=int, default=4)
    parser.add_argument("--rollout-steps", type=int, default=64)
    parser.add_argument("--hidden-dim", type=int, default=64)
    parser.add_argument("--lr", type=float, default=5e-5)
    parser.add_argument("--entropy-coef", type=float, default=0.001)
    parser.add_argument("--eval-episodes", type=int, default=30)
    parser.add_argument("--eval-base-seed", type=int, default=91_000)
    parser.add_argument("--eval-scenarios", nargs="+", default=("relay_failure", "scout_failure"))
    parser.add_argument("--device", type=str, default="cpu")
    parser.add_argument("--baseline-dir", type=Path, default=ROOT / "results" / "intercept_3d_no_role_pair_gate_baseline_formal")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "results" / "intercept_3d_no_role_pair_gate_topology_formal")
    parser.add_argument("--skip-existing", action="store_true")
    parser.add_argument("--baseline-only", action="store_true")
    parser.add_argument("--topology-only", action="store_true")
    parser.add_argument("--eval-only", action="store_true")
    return parser.parse_args()


def run_command(command: list[str]) -> None:
    print("$", " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def write_manifest(args: argparse.Namespace) -> None:
    args.out_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        "# 3DOF Role-Pair Gate Ablation Protocol",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "Purpose:",
        "",
        "```text",
        "Train and evaluate a no-role-pair-gate ablation for the multi-relation role graph.",
        "The ablation keeps perception, communication, task-support relations, and the union residual path, but replaces receiver-sender role-pair message gates with identity gates.",
        "```",
        "",
        "## Configuration",
        "",
        "```text",
        f"seeds = {list(args.seeds)}",
        "graph_encoder = multi_relation",
        "graph_relation_ablation = none",
        "graph_message_ablation = no_role_pair_gate",
        f"target_policy = {args.target_policy}",
        f"bc = {args.bc_episodes} episodes, {args.bc_epochs} epochs",
        f"baseline PPO = {args.baseline_ppo_updates} updates",
        f"topology PPO = {args.topology_updates} updates",
        f"num_envs = {args.num_envs}",
        f"rollout_steps = {args.rollout_steps}",
        f"lr = {args.lr}",
        f"entropy_coef = {args.entropy_coef}",
        "topology curriculum = range 0.65--1.0, dropout 0--0.25, delay 0--3, radar dropout 0--0.15, random node failure",
        f"eval_scenarios = {list(args.eval_scenarios)}",
        f"eval_episodes = {args.eval_episodes}",
        f"eval_base_seed = {args.eval_base_seed}",
        "```",
        "",
    ]
    (args.out_dir / "protocol.md").write_text("\n".join(lines), encoding="utf-8")


def run_baseline(args: argparse.Namespace) -> None:
    run_command(
        [
            sys.executable,
            "-B",
            "scripts/run_3d_baseline_protocol.py",
            "--seeds",
            *[str(seed) for seed in args.seeds],
            "--methods",
            "bc_ppo",
            "--eval-episodes",
            "30",
            "--eval-base-seed",
            "40000",
            "--target-policy",
            args.target_policy,
            "--graph-encoder",
            "multi_relation",
            "--graph-message-ablation",
            "no_role_pair_gate",
            "--bc-episodes",
            str(args.bc_episodes),
            "--bc-epochs",
            str(args.bc_epochs),
            "--ppo-updates",
            str(args.baseline_ppo_updates),
            "--ppo-lr",
            str(args.lr),
            "--entropy-coef",
            str(args.entropy_coef),
            "--num-envs",
            str(args.num_envs),
            "--rollout-steps",
            str(args.rollout_steps),
            "--device",
            args.device,
            "--out-dir",
            str(args.baseline_dir),
            *(["--skip-existing"] if args.skip_existing else []),
        ]
    )


def run_topology(args: argparse.Namespace) -> None:
    command = [
        sys.executable,
        "-B",
        "scripts/run_3d_topology_curriculum_protocol.py",
        "--seeds",
        *[str(seed) for seed in args.seeds],
        "--graph-encoders",
        "multi_relation",
        "--graph-message-ablation",
        "no_role_pair_gate",
        "--source-multi-root",
        str(args.baseline_dir / "runs"),
        "--source-checkpoint-kind",
        "actor_critic_best.pt",
        "--target-policy",
        args.target_policy,
        "--updates",
        str(args.topology_updates),
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
        "--communication-range-random-min",
        "0.65",
        "--communication-range-random-max",
        "1.0",
        "--communication-dropout-random-min",
        "0.0",
        "--communication-dropout-random-max",
        "0.25",
        "--message-delay-random-min",
        "0",
        "--message-delay-random-max",
        "3",
        "--radar-dropout-random-min",
        "0.0",
        "--radar-dropout-random-max",
        "0.15",
        "--failed-blue-agent",
        "-1",
        "--node-failure-random-prob",
        "0.5",
        "--node-failure-start-step",
        "40",
        "--node-failure-start-random-min",
        "30",
        "--node-failure-start-random-max",
        "70",
        "--node-failure-duration-steps",
        "80",
        "--node-failure-duration-random-min",
        "40",
        "--node-failure-duration-random-max",
        "100",
        "--eval-episodes",
        str(args.eval_episodes),
        "--eval-base-seed",
        str(args.eval_base_seed),
        "--eval-scenarios",
        *args.eval_scenarios,
        "--device",
        args.device,
        "--out-dir",
        str(args.out_dir),
    ]
    if args.skip_existing:
        command.append("--skip-existing")
    if args.eval_only:
        command.append("--eval-only")
    run_command(command)


def main() -> None:
    args = parse_args()
    write_manifest(args)
    if not args.topology_only and not args.eval_only:
        run_baseline(args)
    if not args.baseline_only:
        run_topology(args)
    print(args.out_dir / "protocol.md")
    print(args.out_dir / "robustness_eval" / "episode_metrics.csv")


if __name__ == "__main__":
    main()
