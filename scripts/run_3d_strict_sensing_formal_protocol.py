from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.evaluate_3d_topology_robustness import SCENARIOS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the formal strict-sensing relay-failure protocol with checkpoint snapshots and validation selection."
    )
    parser.add_argument("--seeds", nargs="+", type=int, default=(0, 1, 2))
    parser.add_argument(
        "--graph-encoders",
        nargs="+",
        choices=("no_graph", "single", "multi_relation"),
        default=("single", "multi_relation"),
    )
    parser.add_argument("--source-single-root", type=Path, default=ROOT / "results" / "intercept_3d_node_failure_curriculum_pilot_seed0" / "runs" / "single")
    parser.add_argument("--source-multi-root", type=Path, default=ROOT / "results" / "intercept_3d_node_failure_curriculum_pilot_seed0" / "runs" / "multi_relation")
    parser.add_argument("--source-no-graph-root", type=Path, default=ROOT / "results" / "intercept_3d_strict_sensing_fair_baselines" / "runs" / "no_graph")
    parser.add_argument("--source-checkpoint-kind", choices=("actor_critic_best.pt", "actor_critic_latest.pt"), default="actor_critic_best.pt")
    parser.add_argument("--updates", type=int, default=120)
    parser.add_argument("--num-envs", type=int, default=4)
    parser.add_argument("--rollout-steps", type=int, default=64)
    parser.add_argument("--hidden-dim", type=int, default=64)
    parser.add_argument("--lr", type=float, default=5e-5)
    parser.add_argument("--entropy-coef", type=float, default=0.001)
    parser.add_argument("--save-interval", type=int, default=10)
    parser.add_argument("--target-policy", type=str, default="straight")
    parser.add_argument("--strict-target-sensing", action="store_true", default=True)
    parser.add_argument("--no-strict-target-sensing", dest="strict_target_sensing", action="store_false")
    parser.add_argument("--agent-target-info-bottleneck", action="store_true")
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
    parser.add_argument("--validation-episodes", type=int, default=50)
    parser.add_argument("--test-episodes", type=int, default=100)
    parser.add_argument("--validation-base-seed", type=int, default=120_000)
    parser.add_argument("--test-base-seed", type=int, default=130_000)
    parser.add_argument(
        "--max-selection-collision-rate",
        type=float,
        default=None,
        help="Reject validation checkpoints above this collision rate before final testing. Use 0.0 for formal runs.",
    )
    parser.add_argument("--scenarios", nargs="+", choices=tuple(SCENARIOS), default=("relay_failure",))
    parser.add_argument("--device", type=str, default="cpu")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "results" / "intercept_3d_strict_sensing_formal")
    parser.add_argument("--skip-existing", action="store_true")
    parser.add_argument("--train-only", action="store_true")
    parser.add_argument("--eval-only", action="store_true")
    parser.add_argument("--test-only", action="store_true")
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


def run_dir(args: argparse.Namespace, graph_encoder: str, seed: int) -> Path:
    return args.out_dir / "runs" / graph_encoder / f"bc_ppo_seed{seed}"


def snapshot_path(args: argparse.Namespace, graph_encoder: str, seed: int) -> Path:
    return run_dir(args, graph_encoder, seed) / f"actor_critic_update_{args.updates:04d}.pt"


def train_one(args: argparse.Namespace, graph_encoder: str, seed: int) -> None:
    src = source_checkpoint(args, graph_encoder, seed)
    if not src.exists():
        raise FileNotFoundError(f"missing source checkpoint: {src}")
    final_snapshot = snapshot_path(args, graph_encoder, seed)
    if args.skip_existing and final_snapshot.exists():
        print(f"skip existing strict-sensing run: {final_snapshot}", flush=True)
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
            *(["--strict-target-sensing"] if args.strict_target_sensing else ["--no-strict-target-sensing"]),
            *(["--agent-target-info-bottleneck"] if args.agent_target_info_bottleneck else []),
            "--graph-encoder",
            graph_encoder,
            "--updates",
            str(args.updates),
            "--num-envs",
            str(args.num_envs),
            "--rollout-steps",
            str(args.rollout_steps),
            "--eval-episodes",
            "5",
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
            str(src),
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
        *(["--strict-target-sensing"] if args.strict_target_sensing else ["--no-strict-target-sensing"]),
        *(["--agent-target-info-bottleneck"] if args.agent_target_info_bottleneck else []),
        "--single-root",
        str(args.out_dir / "runs" / "single"),
        "--multi-root",
        str(args.out_dir / "runs" / "multi_relation"),
        "--no-graph-root",
        str(args.out_dir / "runs" / "no_graph"),
        "--device",
        args.device,
        "--out-dir",
        str(args.out_dir / "checkpoint_sweep"),
    ]
    if selection_csv is not None:
        command.extend(["--selection-csv", str(selection_csv)])
    if split == "validation" and args.max_selection_collision_rate is not None:
        command.extend(["--max-selection-collision-rate", str(args.max_selection_collision_rate)])
    run_command(command)


def write_protocol(args: argparse.Namespace) -> None:
    args.out_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Formal Strict-Sensing 3DOF Protocol",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "Purpose:",
        "",
        "```text",
        "Formalize the strict-sensing relay-failure main experiment.",
        "Training saves snapshots every save interval.",
        "Validation split selects checkpoints.",
        "Test split evaluates only selected validation checkpoints.",
        "```",
        "",
        "## Configuration",
        "",
        "```text",
        f"seeds = {list(args.seeds)}",
        f"graph_encoders = {list(args.graph_encoders)}",
        f"updates = {args.updates}",
        f"save_interval = {args.save_interval}",
        f"validation_episodes = {args.validation_episodes}",
        f"test_episodes = {args.test_episodes}",
        f"validation_base_seed = {args.validation_base_seed}",
        f"test_base_seed = {args.test_base_seed}",
        f"max_selection_collision_rate = {args.max_selection_collision_rate}",
        f"scenarios = {list(args.scenarios)}",
        f"strict_target_sensing = {args.strict_target_sensing}",
        f"agent_target_info_bottleneck = {args.agent_target_info_bottleneck}",
        f"lr = {args.lr}",
        f"entropy_coef = {args.entropy_coef}",
        f"communication_range_random = [{args.communication_range_random_min}, {args.communication_range_random_max}]",
        f"communication_dropout_random = [{args.communication_dropout_random_min}, {args.communication_dropout_random_max}]",
        f"message_delay_random = [{args.message_delay_random_min}, {args.message_delay_random_max}]",
        f"radar_dropout_random = [{args.radar_dropout_random_min}, {args.radar_dropout_random_max}]",
        f"node_failure_random_prob = {args.node_failure_random_prob}",
        f"node_failure_start_random = [{args.node_failure_start_random_min}, {args.node_failure_start_random_max}]",
        f"node_failure_duration_random = [{args.node_failure_duration_random_min}, {args.node_failure_duration_random_max}]",
        "```",
        "",
        "## Paper Boundary",
        "",
        "- Validation rows are for checkpoint selection and training-budget diagnosis only.",
        "- If configured, validation checkpoints above `max_selection_collision_rate` are rejected before final testing.",
        "- Test rows are used only after checkpoint selection is frozen.",
        "- The paper claim should prioritize relay failure; scout failure remains supporting unless separated.",
        "- This protocol does not add 4v2, missile, JSBSim, or self-play complexity.",
        "- The default uses the currently available source seeds 0--2. For the final main result, extend to `--seeds 0 1 2 3 4` after preparing seed-3/4 source checkpoints.",
        "",
    ]
    (args.out_dir / "protocol.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    write_protocol(args)
    if not args.eval_only and not args.test_only:
        for graph_encoder in args.graph_encoders:
            for seed in args.seeds:
                print(f"=== strict sensing {graph_encoder} seed {seed} ===", flush=True)
                train_one(args, graph_encoder, seed)
    if not args.train_only and not args.test_only:
        evaluate_split(args, "validation", args.validation_episodes, args.validation_base_seed, None)
    if not args.train_only:
        selection_csv = args.out_dir / "checkpoint_sweep" / "validation_selected_checkpoints.csv"
        evaluate_split(args, "test", args.test_episodes, args.test_base_seed, selection_csv)
    print(args.out_dir / "protocol.md")


if __name__ == "__main__":
    main()
