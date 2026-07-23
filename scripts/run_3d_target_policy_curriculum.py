from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def parse_updates(text: str, policies: list[str]) -> list[int]:
    values = [int(part) for part in text.split(",") if part.strip()]
    if len(values) == 1:
        values = values * len(policies)
    if len(values) != len(policies):
        raise ValueError(
            f"--stage-updates must contain one value or {len(policies)} comma-separated values"
        )
    if any(value <= 0 for value in values):
        raise ValueError("--stage-updates values must be positive")
    return values


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run nominal 3DOF target-policy curriculum fine-tuning, e.g. "
            "straight-source -> weaving_tiny -> weaving_mild."
        )
    )
    parser.add_argument("--seeds", nargs="+", type=int, default=(0,))
    parser.add_argument(
        "--graph-encoders",
        nargs="+",
        choices=("no_graph", "single", "multi_relation"),
        default=("multi_relation",),
    )
    parser.add_argument("--source-single-root", type=Path, default=ROOT / "results" / "intercept_3d_gate1_hardened_safety_5seed_formal_candidate" / "runs" / "single")
    parser.add_argument("--source-multi-root", type=Path, default=ROOT / "results" / "intercept_3d_gate1_hardened_safety_5seed_formal_candidate" / "runs" / "multi_relation")
    parser.add_argument("--source-no-graph-root", type=Path, default=ROOT / "results" / "intercept_3d_gate1_hardened_safety_5seed_formal_candidate" / "runs" / "no_graph")
    parser.add_argument("--source-checkpoint-kind", type=str, default="actor_critic_update_0060.pt")
    parser.add_argument("--stage-policies", nargs="+", default=("weaving_tiny", "weaving_mild"))
    parser.add_argument(
        "--stage-updates",
        type=str,
        default="30,30",
        help="One value applied to every stage, or comma-separated values matching --stage-policies.",
    )
    parser.add_argument("--num-envs", type=int, default=4)
    parser.add_argument("--rollout-steps", type=int, default=64)
    parser.add_argument("--hidden-dim", type=int, default=64)
    parser.add_argument("--lr", type=float, default=1e-5)
    parser.add_argument("--entropy-coef", type=float, default=0.001)
    parser.add_argument("--eval-episodes", type=int, default=4)
    parser.add_argument("--save-interval", type=int, default=10)
    parser.add_argument("--graph-relation-ablation", choices=("none", "no_task_support"), default="none")
    parser.add_argument("--graph-message-ablation", choices=("none", "no_role_pair_gate"), default="none")
    parser.add_argument("--graph-input-ablation", choices=("none", "no_edge_features", "no_role_identity"), default="none")
    parser.add_argument("--safety-proximity-distance", type=float, default=0.0)
    parser.add_argument("--safety-proximity-penalty-weight", type=float, default=0.0)
    parser.add_argument("--attack-geometry-reward-weight", type=float, default=0.0)
    parser.add_argument("--device", type=str, default="cpu")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "results" / "intercept_3d_target_policy_curriculum")
    parser.add_argument("--skip-existing", action="store_true")
    args = parser.parse_args()
    args.stage_updates_list = parse_updates(args.stage_updates, list(args.stage_policies))
    return args


def run_command(command: list[str]) -> None:
    print("$", " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def source_root(args: argparse.Namespace, graph_encoder: str) -> Path:
    if graph_encoder == "no_graph":
        return args.source_no_graph_root
    if graph_encoder == "single":
        return args.source_single_root
    if graph_encoder == "multi_relation":
        return args.source_multi_root
    raise ValueError(f"Unsupported graph_encoder: {graph_encoder}")


def source_checkpoint(args: argparse.Namespace, graph_encoder: str, seed: int) -> Path:
    return source_root(args, graph_encoder) / f"bc_ppo_seed{seed}" / args.source_checkpoint_kind


def stage_name(index: int, policy: str) -> str:
    return f"stage{index:02d}_{policy}"


def run_dir(args: argparse.Namespace, stage_index: int, policy: str, graph_encoder: str, seed: int) -> Path:
    return args.out_dir / stage_name(stage_index, policy) / "runs" / graph_encoder / f"bc_ppo_seed{seed}"


def final_snapshot(args: argparse.Namespace, stage_index: int, policy: str, graph_encoder: str, seed: int) -> Path:
    updates = args.stage_updates_list[stage_index - 1]
    return run_dir(args, stage_index, policy, graph_encoder, seed) / f"actor_critic_update_{updates:04d}.pt"


def train_stage(
    args: argparse.Namespace,
    stage_index: int,
    policy: str,
    updates: int,
    graph_encoder: str,
    seed: int,
    resume: Path,
) -> Path:
    if not resume.exists():
        raise FileNotFoundError(f"missing resume checkpoint: {resume}")
    output_snapshot = final_snapshot(args, stage_index, policy, graph_encoder, seed)
    if args.skip_existing and output_snapshot.exists():
        print(f"skip existing curriculum stage: {output_snapshot}", flush=True)
        return output_snapshot
    out_dir = run_dir(args, stage_index, policy, graph_encoder, seed)
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
            policy,
            "--graph-encoder",
            graph_encoder,
            "--graph-relation-ablation",
            args.graph_relation_ablation,
            "--graph-message-ablation",
            args.graph_message_ablation,
            "--graph-input-ablation",
            args.graph_input_ablation,
            "--updates",
            str(updates),
            "--num-envs",
            str(args.num_envs),
            "--rollout-steps",
            str(args.rollout_steps),
            "--eval-episodes",
            str(args.eval_episodes),
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
            "--safety-proximity-distance",
            str(args.safety_proximity_distance),
            "--safety-proximity-penalty-weight",
            str(args.safety_proximity_penalty_weight),
            "--attack-geometry-reward-weight",
            str(args.attack_geometry_reward_weight),
            "--device",
            args.device,
            "--resume",
            str(resume),
            "--out-dir",
            str(out_dir),
        ]
    )
    return output_snapshot


def write_protocol(args: argparse.Namespace) -> None:
    args.out_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        "# 3DOF Target-Policy Curriculum Run",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "This run performs nominal target-policy curriculum fine-tuning only.",
        "It intentionally does not enable strict sensing, target-information bottlenecks, or node failure.",
        "",
        "```text",
        f"seeds = {list(args.seeds)}",
        f"graph_encoders = {list(args.graph_encoders)}",
        f"stage_policies = {list(args.stage_policies)}",
        f"stage_updates = {args.stage_updates_list}",
        f"source_checkpoint_kind = {args.source_checkpoint_kind}",
        f"hidden_dim = {args.hidden_dim}",
        f"lr = {args.lr}",
        f"entropy_coef = {args.entropy_coef}",
        f"num_envs = {args.num_envs}",
        f"rollout_steps = {args.rollout_steps}",
        f"eval_episodes = {args.eval_episodes}",
        f"save_interval = {args.save_interval}",
        f"graph_relation_ablation = {args.graph_relation_ablation}",
        f"graph_message_ablation = {args.graph_message_ablation}",
        f"graph_input_ablation = {args.graph_input_ablation}",
        f"safety_proximity_distance = {args.safety_proximity_distance}",
        f"safety_proximity_penalty_weight = {args.safety_proximity_penalty_weight}",
        f"attack_geometry_reward_weight = {args.attack_geometry_reward_weight}",
        "```",
        "",
    ]
    (args.out_dir / "protocol.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    write_protocol(args)
    for graph_encoder in args.graph_encoders:
        for seed in args.seeds:
            resume = source_checkpoint(args, graph_encoder, seed)
            for stage_index, (policy, updates) in enumerate(
                zip(args.stage_policies, args.stage_updates_list), start=1
            ):
                print(
                    f"=== target-policy curriculum {graph_encoder} seed={seed} "
                    f"stage={stage_index} policy={policy} ===",
                    flush=True,
                )
                resume = train_stage(args, stage_index, policy, updates, graph_encoder, seed, resume)
    print(args.out_dir / "protocol.md")


if __name__ == "__main__":
    main()
