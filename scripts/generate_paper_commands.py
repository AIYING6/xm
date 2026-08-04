from __future__ import annotations

import argparse
import csv
import json
import shlex
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "configs" / "paper"
FORMAL_MAIN_METHODS = (
    "mappo",
    "single_graph",
    "param_matched_single",
    "ea_rg_mappo_gate_prior",
    "happo",
)
DEVELOPMENT_METHODS = (
    "mappo",
    "single_graph",
    "ea_rg_mappo",
    "param_matched_single",
    "ablation_no_role_pair",
    "ablation_no_task_support",
    "ablation_no_role_identity",
)
DEFAULT_METHODS = FORMAL_MAIN_METHODS
EXTERNAL_OR_PENDING = {"ippo"}


def load_config(name: str) -> dict:
    path = CONFIG_DIR / f"{name}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"missing config: {path}")
    cfg = json.loads(path.read_text(encoding="utf-8"))
    inherit_from = cfg.get("inherit_hyperparameters_from")
    if "ppo" not in cfg and inherit_from:
        parent = json.loads((CONFIG_DIR / f"{inherit_from}.yaml").read_text(encoding="utf-8"))
        if "ppo" in parent:
            cfg["ppo"] = parent["ppo"]
    return cfg


def bool_flag(enabled: bool, flag: str) -> list[str]:
    return [flag] if enabled else []


def mode_budget(main_cfg: dict, mode: str) -> tuple[int, int, int, int, int]:
    rollout = main_cfg["rollout"]
    seeds = main_cfg["seeds"]
    if mode == "smoke":
        return 1, 1, 8, 1, 1
    if mode == "probe_20":
        return 20, 1, 16, 2, 10
    if mode == "freeze_rehearsal":
        updates_1m = int(rollout["updates_for_1m_steps"])
        rehearsal_updates = max(20, int(round((updates_1m * 0.05) / 20.0)) * 20)
        return rehearsal_updates, int(rollout["num_envs"]), int(rollout["rollout_steps"]), 5, 20
    if mode == "dev_1m":
        return int(rollout["updates_for_1m_steps"]), int(rollout["num_envs"]), int(rollout["rollout_steps"]), 5, 100
    if mode == "formal_bstar":
        return int(rollout["updates_for_1m_steps"]), int(rollout["num_envs"]), int(rollout["rollout_steps"]), int(seeds["validation_episodes_per_seed"]), 100
    raise ValueError(f"unsupported mode: {mode}")


def sweep_episode_count(main_cfg: dict, mode: str, split: str) -> int:
    if mode in {"smoke", "probe_20", "freeze_rehearsal"}:
        return 5
    seed_cfg = main_cfg["seeds"]
    return int(seed_cfg["validation_episodes_per_seed"] if split == "validation" else seed_cfg["test_episodes_per_seed"])


def command_quote(parts: list[str]) -> str:
    return " ".join(shlex.quote(str(part)) for part in parts)


def sweep_scenarios(main_cfg: dict, split: str) -> list[str]:
    scenario = main_cfg["scenario"]
    key = f"{split}_scenarios"
    scenarios = scenario.get(key)
    if scenarios:
        return [str(name) for name in scenarios]
    return ["relay_failure"]


def method_train_command(
    *,
    main_cfg: dict,
    method_name: str,
    method_cfg: dict,
    mode: str,
    seed: int,
    device: str,
    out_root: Path,
) -> list[str]:
    scenario = main_cfg["scenario"]
    updates, num_envs, rollout_steps, eval_episodes, save_interval = mode_budget(main_cfg, mode)
    output_method_name = method_cfg.get("output_method_name", method_name)
    out_dir = out_root / mode / "runs" / output_method_name / f"bc_ppo_seed{seed}"
    ppo = method_cfg.get("ppo", {})
    lr = ppo.get("learning_rate_candidates", [5e-5])[0]
    entropy = ppo.get("entropy_coef_candidates", [0.001])[-1]
    trainer_script = method_cfg.get("trainer_script", "scripts/train_ri_gmappo.py")
    is_happo = trainer_script.endswith("train_happo_baseline.py")

    base_command = [
        "python",
        "-B",
        trainer_script,
        "--seed",
        str(seed),
        "--target-policy",
        scenario["target_policy"],
        *bool_flag(bool(scenario["strict_target_sensing"]), "--strict-target-sensing"),
        *bool_flag(bool(scenario["agent_target_info_bottleneck"]), "--agent-target-info-bottleneck"),
        "--target-prior-position",
        *[str(x) for x in scenario.get("target_prior_position", [10_000.0, 0.0, 5_000.0])],
        "--communication-dropout-prob",
        str(scenario["communication_dropout_prob_test"]),
        "--message-delay-steps",
        str(scenario["message_delay_steps_test"]),
        "--failed-blue-agent",
        str(scenario["failed_blue_agent"]),
        "--node-failure-start-step",
        str(scenario["node_failure_start_step"]),
        "--node-failure-duration-steps",
        str(scenario["node_failure_duration_steps"]),
        "--max-target-message-age-steps",
        str(scenario["max_target_message_age_steps"]),
        "--min-target-confidence",
        str(scenario["min_target_confidence"]),
        "--safety-proximity-distance",
        str(scenario["safety_proximity_distance"]),
        "--safety-proximity-penalty-weight",
        str(scenario["safety_proximity_penalty_weight"]),
        "--hidden-dim",
        str(method_cfg.get("hidden_dim", 64)),
        "--role-dim",
        str(method_cfg.get("role_dim", 8)),
        "--intent-dim",
        str(method_cfg.get("intent_dim", 8)),
        "--intent-coef",
        "0.0",
        "--lr",
        str(lr),
        "--entropy-coef",
        str(entropy),
        "--updates",
        str(updates),
        "--num-envs",
        str(num_envs),
        "--rollout-steps",
        str(rollout_steps),
        "--eval-episodes",
        str(eval_episodes),
        "--eval-interval",
        str(save_interval),
        "--save-interval",
        str(save_interval),
        "--save-snapshots",
        "--device",
        device,
        "--out-dir",
        out_dir.as_posix(),
    ]
    if not is_happo:
        base_command[3:3] = ["--env-name", scenario["env_name"]]
        insert_at = base_command.index("--hidden-dim")
        base_command[insert_at:insert_at] = [
            "--graph-encoder",
            method_cfg["graph_encoder"],
            "--graph-relation-ablation",
            method_cfg.get("graph_relation_ablation", "none"),
            "--graph-message-ablation",
            method_cfg.get("graph_message_ablation", "none"),
            "--graph-input-ablation",
            method_cfg.get("graph_input_ablation", "none"),
            "--chain-aux-coef",
            str(method_cfg.get("chain_aux_coef", 0.0)),
            "--chain-aux-warmup-updates",
            str(method_cfg.get("chain_aux_warmup_updates", 0)),
            "--role-gate-prior-strength",
            str(method_cfg.get("role_gate_prior_strength", 0.0)),
        ]
    return base_command


def method_sweep_command(
    *,
    main_cfg: dict,
    method_name: str,
    method_cfg: dict,
    mode: str,
    split: str,
    seeds: list[int],
    device: str,
    out_root: Path,
) -> list[str]:
    scenario = main_cfg["scenario"]
    scenarios = sweep_scenarios(main_cfg, split)
    seed_cfg = main_cfg["seeds"]
    episodes = sweep_episode_count(main_cfg, mode, split)
    base_seed = seed_cfg["validation_base_seed"] if split == "validation" else seed_cfg["test_base_seed"]
    out_dir = out_root / mode / "checkpoint_sweeps" / method_name
    method_root = out_root / mode / "runs" / method_cfg.get("output_method_name", method_name)
    graph_encoder = method_cfg["graph_encoder"]
    root_arg = {
        "no_graph": "--no-graph-root",
        "single": "--single-root",
        "multi_relation": "--multi-root",
    }[graph_encoder]
    command = [
        "python",
        "-B",
        "scripts/evaluate_3d_checkpoint_sweep.py",
        "--split",
        split,
        "--seeds",
        *[str(seed) for seed in seeds],
        "--graph-encoders",
        graph_encoder,
        "--scenarios",
        *scenarios,
        "--episodes",
        str(episodes),
        "--base-seed",
        str(base_seed),
        "--target-policy",
        scenario["target_policy"],
        *bool_flag(bool(scenario["strict_target_sensing"]), "--strict-target-sensing"),
        *bool_flag(bool(scenario["agent_target_info_bottleneck"]), "--agent-target-info-bottleneck"),
        "--target-prior-position",
        *[str(x) for x in scenario.get("target_prior_position", [10_000.0, 0.0, 5_000.0])],
        "--graph-relation-ablation",
        method_cfg.get("graph_relation_ablation", "none"),
        "--graph-message-ablation",
        method_cfg.get("graph_message_ablation", "none"),
        "--graph-input-ablation",
        method_cfg.get("graph_input_ablation", "none"),
        "--max-target-message-age-steps",
        str(scenario["max_target_message_age_steps"]),
        "--min-target-confidence",
        str(scenario["min_target_confidence"]),
        root_arg,
        method_root.as_posix(),
        "--checkpoint-glob",
        "actor_critic_update_*.pt",
        "--device",
        device,
        "--out-dir",
        out_dir.as_posix(),
        "--max-selection-collision-rate",
        "0.0",
        "--selection-metric",
        "legacy_recovery",
        "--selection-success-weight",
        "100",
    ]
    if len(scenarios) > 1:
        command.extend(["--selection-group", "suite"])
    if split == "test":
        command.extend(
            [
                "--selection-csv",
                (out_dir / "validation_selected_checkpoints.csv").as_posix(),
            ]
        )
    return command


def happo_sweep_command(
    *,
    main_cfg: dict,
    method_name: str,
    mode: str,
    split: str,
    seeds: list[int],
    device: str,
    out_root: Path,
    output_method_name: str | None = None,
) -> list[str]:
    scenario = main_cfg["scenario"]
    scenarios = sweep_scenarios(main_cfg, split)
    seed_cfg = main_cfg["seeds"]
    episodes = sweep_episode_count(main_cfg, mode, split)
    base_seed = seed_cfg["validation_base_seed"] if split == "validation" else seed_cfg["test_base_seed"]
    out_dir = out_root / mode / "checkpoint_sweeps" / method_name
    run_method_name = output_method_name or method_name
    command = [
        "python",
        "-B",
        "scripts/evaluate_happo_checkpoint_sweep.py",
        "--split",
        split,
        "--seeds",
        *[str(seed) for seed in seeds],
        "--scenarios",
        *scenarios,
        "--episodes",
        str(episodes),
        "--base-seed",
        str(base_seed),
        "--target-policy",
        scenario["target_policy"],
        *bool_flag(bool(scenario["strict_target_sensing"]), "--strict-target-sensing"),
        *bool_flag(bool(scenario["agent_target_info_bottleneck"]), "--agent-target-info-bottleneck"),
        "--target-prior-position",
        *[str(x) for x in scenario.get("target_prior_position", [10_000.0, 0.0, 5_000.0])],
        "--max-target-message-age-steps",
        str(scenario["max_target_message_age_steps"]),
        "--min-target-confidence",
        str(scenario["min_target_confidence"]),
        "--happo-root",
        (out_root / mode / "runs" / run_method_name).as_posix(),
        "--checkpoint-glob",
        "happo_update_*.pt",
        "--device",
        device,
        "--out-dir",
        out_dir.as_posix(),
        "--max-selection-collision-rate",
        "0.0",
        "--selection-metric",
        "legacy_recovery",
        "--selection-success-weight",
        "100",
    ]
    if len(scenarios) > 1:
        command.extend(["--selection-group", "suite"])
    if split == "test":
        command.extend(["--selection-csv", (out_dir / "validation_selected_checkpoints.csv").as_posix()])
    return command


def write_outputs(rows: list[dict], out_csv: Path, out_md: Path) -> None:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=("kind", "mode", "method", "seed", "status", "command", "note"))
        writer.writeheader()
        writer.writerows(rows)

    lines = [
        "# Paper Command Manifest",
        "",
        "Generated from `configs/paper/`.",
        "",
        "| Kind | Mode | Method | Seed | Status | Command / Note |",
        "|---|---|---|---:|---|---|",
    ]
    for row in rows:
        command_or_note = row["command"] if row["command"] else row["note"]
        lines.append(
            f"| {row['kind']} | {row['mode']} | {row['method']} | {row['seed']} | {row['status']} | `{command_or_note}` |"
        )
    lines.append("")
    out_md.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate config-driven paper training commands.")
    parser.add_argument(
        "--mode",
        choices=("smoke", "probe_20", "freeze_rehearsal", "dev_1m", "formal_bstar"),
        default="smoke",
    )
    parser.add_argument("--method-set", choices=("formal_main", "development"), default="formal_main")
    parser.add_argument("--methods", nargs="+", default=None)
    parser.add_argument("--seeds", nargs="+", type=int, default=(0,))
    parser.add_argument("--include-sweeps", action="store_true")
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--out-root", type=Path, default=ROOT / "results" / "paper_config_runs")
    parser.add_argument("--out-csv", type=Path, default=ROOT / "results" / "paper_command_manifest.csv")
    parser.add_argument("--out-md", type=Path, default=ROOT / "docs" / "paper_command_manifest.md")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.methods is None:
        args.methods = list(FORMAL_MAIN_METHODS if args.method_set == "formal_main" else DEVELOPMENT_METHODS)
    main_cfg = load_config("main_gate1")
    rows: list[dict] = []
    for method_name in args.methods:
        method_cfg = load_config(method_name)
        if method_name in EXTERNAL_OR_PENDING or ("graph_encoder" not in method_cfg and "trainer_script" not in method_cfg):
            rows.append(
                {
                    "kind": "train",
                    "mode": args.mode,
                    "method": method_name,
                    "seed": -1,
                    "status": "pending_implementation",
                    "command": "",
                    "note": method_cfg.get("stop_rule", method_cfg.get("implementation_status", "pending")),
                }
            )
            continue
        is_happo = str(method_cfg.get("trainer_script", "")).endswith("train_happo_baseline.py")
        ready_for_sweep = method_name not in EXTERNAL_OR_PENDING and "graph_encoder" in method_cfg and not is_happo
        for seed in args.seeds:
            command = method_train_command(
                main_cfg=main_cfg,
                method_name=method_name,
                method_cfg=method_cfg,
                mode=args.mode,
                seed=seed,
                device=args.device,
                out_root=args.out_root,
            )
            rows.append(
                {
                    "kind": "train",
                    "mode": args.mode,
                    "method": method_name,
                    "seed": seed,
                    "status": "ready",
                    "command": command_quote(command),
                    "note": "",
                }
            )
        if args.include_sweeps and ready_for_sweep:
            for split in ("validation", "test"):
                command = method_sweep_command(
                    main_cfg=main_cfg,
                    method_name=method_name,
                    method_cfg=method_cfg,
                    mode=args.mode,
                    split=split,
                    seeds=list(args.seeds),
                    device=args.device,
                    out_root=args.out_root,
                )
                rows.append(
                    {
                        "kind": f"{split}_sweep",
                        "mode": args.mode,
                        "method": method_name,
                        "seed": -1,
                        "status": "ready_after_training",
                        "command": command_quote(command),
                        "note": "",
                    }
                )
        elif args.include_sweeps and is_happo:
            for split in ("validation", "test"):
                command = happo_sweep_command(
                    main_cfg=main_cfg,
                    method_name=method_name,
                    mode=args.mode,
                    split=split,
                    seeds=list(args.seeds),
                    device=args.device,
                    out_root=args.out_root,
                    output_method_name=method_cfg.get("output_method_name", method_name),
                )
                rows.append(
                    {
                        "kind": f"{split}_sweep",
                        "mode": args.mode,
                        "method": method_name,
                        "seed": -1,
                        "status": "ready_after_training",
                        "command": command_quote(command),
                        "note": "",
                    }
                )
    write_outputs(rows, args.out_csv, args.out_md)
    print(args.out_csv)
    print(args.out_md)
    print(f"commands: {len(rows)}")


if __name__ == "__main__":
    main()
