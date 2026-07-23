from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the frozen nominal weaving_mild scenario-depth protocol."
    )
    parser.add_argument("--seeds", nargs="+", type=int, default=(0, 1, 2, 3, 4))
    parser.add_argument(
        "--graph-encoders",
        nargs="+",
        choices=("no_graph", "single", "multi_relation"),
        default=("no_graph", "single", "multi_relation"),
    )
    parser.add_argument(
        "--source-root",
        type=Path,
        default=ROOT / "results" / "intercept_3d_gate1_hardened_safety_5seed_formal_candidate" / "runs",
    )
    parser.add_argument("--source-checkpoint-kind", default="actor_critic_update_0060.pt")
    parser.add_argument("--target-policy", default="weaving_mild")
    parser.add_argument("--bc-episodes", type=int, default=30)
    parser.add_argument("--bc-epochs", type=int, default=12)
    parser.add_argument("--attacker-action-weight", type=float, default=4.0)
    parser.add_argument("--ppo-updates", type=int, default=30)
    parser.add_argument("--lr", type=float, default=1e-5)
    parser.add_argument("--entropy-coef", type=float, default=0.001)
    parser.add_argument("--num-envs", type=int, default=4)
    parser.add_argument("--rollout-steps", type=int, default=64)
    parser.add_argument("--hidden-dim", type=int, default=64)
    parser.add_argument("--role-dim", type=int, default=8)
    parser.add_argument("--intent-dim", type=int, default=8)
    parser.add_argument("--save-interval", type=int, default=5)
    parser.add_argument("--train-eval-episodes", type=int, default=4)
    parser.add_argument("--validation-episodes", type=int, default=30)
    parser.add_argument("--validation-base-seed", type=int, default=509_000)
    parser.add_argument("--test-episodes", type=int, default=100)
    parser.add_argument("--test-base-seed", type=int, default=609_000)
    parser.add_argument("--eval-batch-size", type=int, default=5)
    parser.add_argument("--max-selection-collision-rate", type=float, default=0.0)
    parser.add_argument("--device", default="cpu")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "results" / "gate1_nominal_weaving_mild_formal_protocol",
    )
    parser.add_argument("--skip-existing", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Use a tiny budget for protocol integration testing.",
    )
    args = parser.parse_args()
    if args.smoke:
        args.seeds = args.seeds[:1]
        args.graph_encoders = args.graph_encoders[:1]
        args.bc_episodes = min(args.bc_episodes, 2)
        args.bc_epochs = min(args.bc_epochs, 1)
        args.ppo_updates = min(args.ppo_updates, 1)
        args.save_interval = 1
        args.train_eval_episodes = min(args.train_eval_episodes, 1)
        args.validation_episodes = min(args.validation_episodes, 2)
        args.test_episodes = min(args.test_episodes, 2)
        args.out_dir = args.out_dir.parent / f"{args.out_dir.name}_smoke"
    return args


def display(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def source_checkpoint(args: argparse.Namespace, graph_encoder: str, seed: int) -> Path:
    return args.source_root / graph_encoder / f"bc_ppo_seed{seed}" / args.source_checkpoint_kind


def bc_dir(args: argparse.Namespace, graph_encoder: str, seed: int) -> Path:
    return args.out_dir / "stage1_oracle_bc" / "runs" / graph_encoder / f"bc_ppo_seed{seed}"


def ppo_dir(args: argparse.Namespace, graph_encoder: str, seed: int) -> Path:
    return args.out_dir / "stage2_weaving_mild_ppo" / "runs" / graph_encoder / f"bc_ppo_seed{seed}"


def run_command(command: list[str], dry_run: bool) -> None:
    print("$", " ".join(command), flush=True)
    if not dry_run:
        subprocess.run(command, cwd=ROOT, check=True)


def run_bc(args: argparse.Namespace, graph_encoder: str, seed: int) -> Path:
    out_dir = bc_dir(args, graph_encoder, seed)
    output = out_dir / "actor_critic_best.pt"
    if args.skip_existing and output.exists():
        print(f"skip existing BC: {display(output)}", flush=True)
        return output
    resume = source_checkpoint(args, graph_encoder, seed)
    if not resume.exists():
        raise FileNotFoundError(f"missing source checkpoint: {display(resume)}")
    command = [
        sys.executable,
        "scripts/pretrain_ri_gmappo_3d_bc.py",
        "--graph-encoder",
        graph_encoder,
        "--hidden-dim",
        str(args.hidden_dim),
        "--role-dim",
        str(args.role_dim),
        "--intent-dim",
        str(args.intent_dim),
        "--target-policy",
        args.target_policy,
        "--geometric-policy-mode",
        "offset",
        "--episodes",
        str(args.bc_episodes),
        "--epochs",
        str(args.bc_epochs),
        "--attacker-action-weight",
        str(args.attacker_action_weight),
        "--no-balanced-loss",
        "--seed",
        str(seed),
        "--device",
        args.device,
        "--resume",
        str(resume),
        "--out-dir",
        str(out_dir),
    ]
    run_command(command, args.dry_run)
    return output


def run_ppo(args: argparse.Namespace, graph_encoder: str, seed: int, resume: Path) -> Path:
    out_dir = ppo_dir(args, graph_encoder, seed)
    output = out_dir / f"actor_critic_update_{args.ppo_updates:04d}.pt"
    if args.skip_existing and output.exists():
        print(f"skip existing PPO: {display(output)}", flush=True)
        return output
    command = [
        sys.executable,
        "scripts/train_ri_gmappo.py",
        "--env-name",
        "3d_intercept",
        "--graph-encoder",
        graph_encoder,
        "--hidden-dim",
        str(args.hidden_dim),
        "--role-dim",
        str(args.role_dim),
        "--intent-dim",
        str(args.intent_dim),
        "--target-policy",
        args.target_policy,
        "--updates",
        str(args.ppo_updates),
        "--num-envs",
        str(args.num_envs),
        "--rollout-steps",
        str(args.rollout_steps),
        "--lr",
        str(args.lr),
        "--entropy-coef",
        str(args.entropy_coef),
        "--eval-episodes",
        str(args.train_eval_episodes),
        "--eval-interval",
        str(max(1, min(args.save_interval, args.ppo_updates))),
        "--save-interval",
        str(max(1, min(args.save_interval, args.ppo_updates))),
        "--save-snapshots",
        "--seed",
        str(seed),
        "--device",
        args.device,
        "--resume",
        str(resume),
        "--out-dir",
        str(out_dir),
    ]
    run_command(command, args.dry_run)
    return output


def selection_cases(args: argparse.Namespace) -> list[str]:
    cases = []
    for graph_encoder in args.graph_encoders:
        for seed in args.seeds:
            run_dir = ppo_dir(args, graph_encoder, seed)
            method = graph_encoder
            cases.extend(["--case", f"{method}={graph_encoder}:{seed}:{run_dir}"])
    return cases


def run_selection(args: argparse.Namespace, split: str, selection_csv: Path | None = None) -> Path:
    out_dir = args.out_dir / f"{split}_checkpoint_selection"
    command = [
        sys.executable,
        "scripts/evaluate_3d_nominal_checkpoint_selection.py",
        *selection_cases(args),
        "--split",
        split,
        "--episodes",
        str(args.validation_episodes if split == "validation" else args.test_episodes),
        "--base-seed",
        str(args.validation_base_seed if split == "validation" else args.test_base_seed),
        "--target-policy",
        args.target_policy,
        "--max-selection-collision-rate",
        str(args.max_selection_collision_rate),
        "--hidden-dim",
        str(args.hidden_dim),
        "--role-dim",
        str(args.role_dim),
        "--intent-dim",
        str(args.intent_dim),
        "--eval-batch-size",
        str(args.eval_batch_size),
        "--device",
        args.device,
        "--out-dir",
        str(out_dir),
        "--resume",
    ]
    if selection_csv is not None:
        command.extend(["--selection-csv", str(selection_csv)])
    run_command(command, args.dry_run)
    return out_dir


def write_protocol_summary(args: argparse.Namespace) -> None:
    args.out_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Nominal Weaving Mild Formal Protocol Run",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "```text",
        f"seeds = {list(args.seeds)}",
        f"graph_encoders = {list(args.graph_encoders)}",
        f"target_policy = {args.target_policy}",
        f"bc_episodes = {args.bc_episodes}",
        f"bc_epochs = {args.bc_epochs}",
        f"attacker_action_weight = {args.attacker_action_weight}",
        f"ppo_updates = {args.ppo_updates}",
        f"validation_episodes = {args.validation_episodes}",
        f"validation_base_seed = {args.validation_base_seed}",
        f"test_episodes = {args.test_episodes}",
        f"test_base_seed = {args.test_base_seed}",
        f"eval_batch_size = {args.eval_batch_size}",
        f"dry_run = {args.dry_run}",
        f"smoke = {args.smoke}",
        "```",
        "",
        "Protocol document: `docs/nominal_weaving_mild_frozen_protocol.md`",
        "",
    ]
    (args.out_dir / "protocol_run_summary.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    write_protocol_summary(args)
    for graph_encoder in args.graph_encoders:
        for seed in args.seeds:
            bc_checkpoint = run_bc(args, graph_encoder, seed)
            run_ppo(args, graph_encoder, seed, bc_checkpoint)
    validation_dir = run_selection(args, "validation")
    selection_csv = validation_dir / "validation_selected_checkpoints.csv"
    run_selection(args, "test", selection_csv=selection_csv)


if __name__ == "__main__":
    main()
