from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fine-tune matched 3DOF checkpoints with topology-domain randomization and evaluate robustness."
    )
    parser.add_argument("--seeds", nargs="+", type=int, default=(0, 1, 2))
    parser.add_argument(
        "--graph-encoders",
        nargs="+",
        choices=("no_graph", "single", "multi_relation"),
        default=("single", "multi_relation"),
    )
    parser.add_argument("--graph-relation-ablation", choices=("none", "no_task_support"), default="none")
    parser.add_argument("--graph-message-ablation", choices=("none", "no_role_pair_gate"), default="none")
    parser.add_argument("--graph-input-ablation", choices=("none", "no_edge_features", "no_role_identity"), default="none")
    parser.add_argument("--source-single-root", type=Path, default=ROOT / "results" / "intercept_3d_single_matched_protocol" / "runs")
    parser.add_argument("--source-multi-root", type=Path, default=ROOT / "results" / "intercept_3d_multirelation_matched_protocol" / "runs")
    parser.add_argument("--source-no-graph-root", type=Path, default=ROOT / "results" / "intercept_3d_no_graph_matched_protocol" / "runs")
    parser.add_argument("--source-checkpoint-kind", choices=("actor_critic_best.pt", "actor_critic_latest.pt"), default="actor_critic_best.pt")
    parser.add_argument("--target-policy", type=str, default="straight")
    parser.add_argument("--strict-target-sensing", action="store_true")
    parser.add_argument("--updates", type=int, default=60)
    parser.add_argument("--num-envs", type=int, default=4)
    parser.add_argument("--rollout-steps", type=int, default=64)
    parser.add_argument("--hidden-dim", type=int, default=64)
    parser.add_argument("--lr", type=float, default=5e-5)
    parser.add_argument("--entropy-coef", type=float, default=0.001)
    parser.add_argument("--communication-range-random-min", type=float, default=0.50)
    parser.add_argument("--communication-range-random-max", type=float, default=1.00)
    parser.add_argument("--communication-dropout-random-min", type=float, default=0.00)
    parser.add_argument("--communication-dropout-random-max", type=float, default=0.25)
    parser.add_argument("--message-delay-random-min", type=int, default=0)
    parser.add_argument("--message-delay-random-max", type=int, default=3)
    parser.add_argument("--radar-dropout-random-min", type=float, default=0.00)
    parser.add_argument("--radar-dropout-random-max", type=float, default=0.15)
    parser.add_argument("--failed-blue-agent", type=int, default=-1)
    parser.add_argument("--node-failure-random-prob", type=float, default=0.0)
    parser.add_argument("--node-failure-start-step", type=int, default=40)
    parser.add_argument("--node-failure-start-random-min", type=int, default=None)
    parser.add_argument("--node-failure-start-random-max", type=int, default=None)
    parser.add_argument("--node-failure-duration-steps", type=int, default=80)
    parser.add_argument("--node-failure-duration-random-min", type=int, default=None)
    parser.add_argument("--node-failure-duration-random-max", type=int, default=None)
    parser.add_argument("--eval-episodes", type=int, default=30)
    parser.add_argument("--eval-base-seed", type=int, default=90_000)
    parser.add_argument("--eval-scenarios", nargs="+", default=("nominal", "range_075", "range_050", "dropout_015", "dropout_030", "delay_2", "delay_5", "radar_010", "radar_025", "relay_failure", "scout_failure"))
    parser.add_argument("--device", type=str, default="cpu")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "results" / "intercept_3d_topology_curriculum_protocol")
    parser.add_argument("--skip-existing", action="store_true")
    parser.add_argument("--train-only", action="store_true")
    parser.add_argument("--eval-only", action="store_true")
    return parser.parse_args()


def run_command(command: list[str]) -> None:
    print("$", " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def source_checkpoint(args: argparse.Namespace, graph_encoder: str, seed: int) -> Path:
    if graph_encoder == "no_graph":
        root = args.source_no_graph_root
    elif graph_encoder == "single":
        root = args.source_single_root
    elif graph_encoder == "multi_relation":
        root = args.source_multi_root
    else:
        raise ValueError(f"Unsupported graph_encoder: {graph_encoder}")
    return root / f"bc_ppo_seed{seed}" / args.source_checkpoint_kind


def output_run_dir(args: argparse.Namespace, graph_encoder: str, seed: int) -> Path:
    return args.out_dir / "runs" / graph_encoder / f"bc_ppo_seed{seed}"


def output_checkpoint(args: argparse.Namespace, graph_encoder: str, seed: int) -> Path:
    return output_run_dir(args, graph_encoder, seed) / "actor_critic_best.pt"


def optional_pair(flag: str, value: object | None) -> list[str]:
    return [] if value is None else [flag, str(value)]


def train_one(args: argparse.Namespace, graph_encoder: str, seed: int) -> None:
    src = source_checkpoint(args, graph_encoder, seed)
    if not src.exists():
        raise FileNotFoundError(f"missing source checkpoint: {src}")
    dst = output_checkpoint(args, graph_encoder, seed)
    if args.skip_existing and dst.exists():
        print(f"skip existing topology checkpoint: {dst}", flush=True)
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
            *(("--strict-target-sensing",) if args.strict_target_sensing else ()),
            "--graph-encoder",
            graph_encoder,
            "--graph-relation-ablation",
            args.graph_relation_ablation,
            "--graph-message-ablation",
            args.graph_message_ablation,
            "--graph-input-ablation",
            args.graph_input_ablation,
            "--updates",
            str(args.updates),
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
            "--failed-blue-agent",
            str(args.failed_blue_agent),
            "--node-failure-random-prob",
            str(args.node_failure_random_prob),
            "--node-failure-start-step",
            str(args.node_failure_start_step),
            *optional_pair("--node-failure-start-random-min", args.node_failure_start_random_min),
            *optional_pair("--node-failure-start-random-max", args.node_failure_start_random_max),
            "--node-failure-duration-steps",
            str(args.node_failure_duration_steps),
            *optional_pair("--node-failure-duration-random-min", args.node_failure_duration_random_min),
            *optional_pair("--node-failure-duration-random-max", args.node_failure_duration_random_max),
            "--device",
            args.device,
            "--resume",
            str(src),
            "--out-dir",
            str(output_run_dir(args, graph_encoder, seed)),
        ]
    )


def evaluate_protocol(args: argparse.Namespace) -> None:
    command = [
        sys.executable,
        "-B",
        "scripts/evaluate_3d_topology_robustness.py",
        "--seeds",
        *[str(seed) for seed in args.seeds],
        "--train-methods",
        "bc_ppo",
        "--graph-encoders",
        *args.graph_encoders,
        "--scenarios",
        *args.eval_scenarios,
        "--episodes",
        str(args.eval_episodes),
        "--eval-base-seed",
        str(args.eval_base_seed),
        "--target-policy",
        args.target_policy,
        *(("--strict-target-sensing",) if args.strict_target_sensing else ()),
        "--checkpoint-kind",
        "actor_critic_best.pt",
        "--single-root",
        str(args.out_dir / "runs" / "single"),
        "--multi-root",
        str(args.out_dir / "runs" / "multi_relation"),
        "--graph-relation-ablation",
        args.graph_relation_ablation,
        "--graph-message-ablation",
        args.graph_message_ablation,
        "--graph-input-ablation",
        args.graph_input_ablation,
        "--device",
        args.device,
        "--out-dir",
        str(args.out_dir / "robustness_eval"),
    ]
    run_command(command)


def write_manifest(args: argparse.Namespace) -> None:
    args.out_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        "# 3DOF Topology Curriculum Protocol",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "```text",
        f"seeds = {list(args.seeds)}",
        f"graph_encoders = {list(args.graph_encoders)}",
        f"graph_relation_ablation = {args.graph_relation_ablation}",
        f"graph_message_ablation = {args.graph_message_ablation}",
        f"graph_input_ablation = {args.graph_input_ablation}",
        f"strict_target_sensing = {args.strict_target_sensing}",
        f"updates = {args.updates}",
        f"num_envs = {args.num_envs}",
        f"rollout_steps = {args.rollout_steps}",
        f"lr = {args.lr}",
        f"entropy_coef = {args.entropy_coef}",
        f"communication_range_random = [{args.communication_range_random_min}, {args.communication_range_random_max}]",
        f"communication_dropout_random = [{args.communication_dropout_random_min}, {args.communication_dropout_random_max}]",
        f"message_delay_random = [{args.message_delay_random_min}, {args.message_delay_random_max}]",
        f"radar_dropout_random = [{args.radar_dropout_random_min}, {args.radar_dropout_random_max}]",
        f"failed_blue_agent = {args.failed_blue_agent}",
        f"node_failure_random_prob = {args.node_failure_random_prob}",
        f"node_failure_start_random = [{args.node_failure_start_random_min}, {args.node_failure_start_random_max}]",
        f"node_failure_duration_random = [{args.node_failure_duration_random_min}, {args.node_failure_duration_random_max}]",
        f"eval_episodes = {args.eval_episodes}",
        f"eval_scenarios = {list(args.eval_scenarios)}",
        "```",
        "",
        "Boundary:",
        "",
        "```text",
        "This protocol fine-tunes already trained straight-target checkpoints under topology-domain randomization.",
        "It is the first matched topology-curriculum experiment chain; final paper evidence still requires completed seeds and fixed evaluation budgets.",
        "```",
        "",
    ]
    (args.out_dir / "protocol.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    write_manifest(args)
    if not args.eval_only:
        for graph_encoder in args.graph_encoders:
            for seed in args.seeds:
                print(f"=== topology curriculum {graph_encoder} seed {seed} ===", flush=True)
                train_one(args, graph_encoder, seed)
    if not args.train_only:
        evaluate_protocol(args)
    print(args.out_dir / "protocol.md")
    if not args.train_only:
        print(args.out_dir / "robustness_eval" / "summary.md")


if __name__ == "__main__":
    main()
