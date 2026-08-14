"""Zero-training MSR sanity/value audit and deterministic cross-tape replay."""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
import statistics
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import run_phase_fl_single as fl  # noqa: E402
import run_phase_rsg1_development_smoke as evaluator  # noqa: E402


MSR_ROOT = ROOT / "archival/results/phase_msr_cloud_20260814/results/development/phase_msr_mature_shared_policy"
MATURITY_ROOT = ROOT / "archival/results/phase_fl_maturity_cloud_20260814/results/development/phase_fl_maturity"
SVA_TAPES = {"fl370": tuple(range(370000, 370010)), "msr380": tuple(range(380000, 380010))}
CHECKPOINTS = {
    "fl_nominal_expert": {
        1801: MATURITY_ROOT / "runs/fl_nominal_expert/seed1801/actor_critic_latest.pt",
        1802: MATURITY_ROOT / "runs/fl_nominal_expert/seed1802/actor_critic_latest.pt",
    },
    "fl_f0_expert": {
        1801: MATURITY_ROOT / "runs/fl_f0_expert/seed1801/actor_critic_latest.pt",
        1802: MATURITY_ROOT / "runs/fl_f0_expert/seed1802/actor_critic_latest.pt",
    },
    "mixed50_sg": {
        1801: MSR_ROOT / "runs/mixed50_sg/seed1801/actor_critic_latest.pt",
        1802: MSR_ROOT / "runs/mixed50_sg/seed1802/actor_critic_latest.pt",
    },
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def mean(rows: list[dict[str, str]], key: str) -> float:
    values = [float(row[key]) for row in rows]
    finite = [value for value in values if math.isfinite(value)]
    return sum(finite) / len(finite) if finite else math.nan


def hash_file(path: Path) -> str:
    return fl.sha256(path)


def load_ms_results() -> tuple[dict, list[dict[str, str]]]:
    result = json.loads((MSR_ROOT / "MSR_RESULT.json").read_text(encoding="utf-8"))
    rows = read_csv(MSR_ROOT / "six_checkpoint_per_seed_metrics.csv")
    return result, rows


def replay_checkpoint(group: str, seed: int, checkpoint: Path, tape_name: str,
                      episode_ids: tuple[int, ...], out_root: Path) -> list[dict]:
    agent = fl.build_agent({"graph_encoder": "single", "hidden_dim": 115}, checkpoint, seed)
    original = evaluator.frozen_env
    evaluator.frozen_env = fl.frozen_env
    rows = []
    try:
        for episode_id in episode_ids:
            for condition in ("nominal", "relay_failure"):
                row, _ = evaluator.evaluate_episode(agent, group, seed, episode_id, condition)
                row.update({"sva_tape": tape_name, "checkpoint_sha256": hash_file(checkpoint)})
                rows.append(row)
    finally:
        evaluator.frozen_env = original
    return rows


def compare_stored_replay(replay_rows: list[dict], stored_root: Path) -> list[dict]:
    comparisons = []
    for (group, seed), cell in {(r["method"], int(r["train_seed"])): [] for r in replay_rows}.items():
        cell.extend(r for r in replay_rows if r["method"] == group and int(r["train_seed"]) == seed)
        for tape_name in {row["sva_tape"] for row in cell}:
            if tape_name == "fl370" and group == "mixed50_sg":
                # No historical Mixed-50 evaluation exists on the FL tape;
                # this replay is retained as a new cross-tape observation.
                continue
            if tape_name == "msr380":
                stored_path = stored_root / "evaluations" / group / f"seed{seed}" / "raw_episode_metrics.csv"
            else:
                stored_path = MATURITY_ROOT / "runs" / group / f"seed{seed}" / "raw_episode_metrics.csv"
            stored = read_csv(stored_path)
            stored_map = {(int(r["development_episode_id"]), r["condition"]): r for r in stored}
            tape_cell = [row for row in cell if row["sva_tape"] == tape_name]
            for row in tape_cell:
                key = (int(row["development_episode_id"]), row["condition"])
                if key not in stored_map:
                    continue
                comparisons.append({
                    "group": group, "seed": seed, "tape": tape_name,
                    "episode_id": key[0], "condition": key[1],
                    "replay_J": float(row["J"]), "stored_J": float(stored_map[key]["J"]),
                    "abs_diff": abs(float(row["J"]) - float(stored_map[key]["J"])),
                })
    return comparisons


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=ROOT / "results/development/post_msr_sva")
    parser.add_argument("--reuse-replay-root", type=Path, default=None,
                        help="reuse an already completed replay CSV; performs no new evaluation")
    args = parser.parse_args()
    if args.output_root.exists() and any(args.output_root.iterdir()):
        raise FileExistsError(f"refusing to overwrite: {args.output_root}")
    args.output_root.mkdir(parents=True, exist_ok=True)

    msr_result, msr_rows = load_ms_results()
    absolute = []
    for row in msr_rows:
        absolute.append({key: row[key] for key in (
            "group", "seed", "J_nominal", "J_failure", "Delta_J", "collision_failure",
            "timeout_failure", "constraint_failure", "failure_exposure", "episode_length_nominal",
            "episode_length_failure")})
    with (args.output_root / "sva_absolute_metrics.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(absolute[0])); writer.writeheader(); writer.writerows(absolute)

    if args.reuse_replay_root is not None:
        replay_rows = read_csv(args.reuse_replay_root / "sva_cross_tape_replay.csv")
        print(f"Reusing completed SVA replay from {args.reuse_replay_root}", flush=True)
    else:
        replay_rows = []
        for tape_name, episode_ids in SVA_TAPES.items():
            for group, cells in CHECKPOINTS.items():
                for seed, checkpoint in cells.items():
                    replay_rows.extend(replay_checkpoint(group, seed, checkpoint, tape_name, episode_ids, args.output_root))
                    print(f"SVA replay complete: {tape_name}/{group}/seed{seed}", flush=True)
    with (args.output_root / "sva_cross_tape_replay.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(replay_rows[0])); writer.writeheader(); writer.writerows(replay_rows)

    comparisons = compare_stored_replay(replay_rows, MSR_ROOT)
    with (args.output_root / "sva_replay_vs_archived.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(comparisons[0])); writer.writeheader(); writer.writerows(comparisons)
    max_replay_diff = max((row["abs_diff"] for row in comparisons), default=math.nan)

    tape_hashes = {m["tape_hash"] for m in msr_result["six_checkpoint_evaluations"]}
    manifest_pass = all(
        m["status"] == "completed" and m["tape_start"] == 380000 and
        m["episodes_per_condition"] == 100 and m["raw_rows"] == 200 and m["paired_rows"] == 100
        for m in msr_result["six_checkpoint_evaluations"]
    ) and len(tape_hashes) == 1
    common_config_keys = (
        "env_name", "num_envs", "rollout_steps", "hidden_dim", "role_dim", "intent_dim",
        "graph_encoder", "role_gate_mode", "target_policy", "strict_target_sensing",
        "agent_target_info_bottleneck", "relay_dependent_task", "business_grounded_geometry",
        "communication_range_scale", "communication_dropout_prob", "message_delay_steps",
        "radar_dropout_prob", "max_steps", "min_success_step", "evaluation_enabled",
    )
    configs = []
    for group, cells in CHECKPOINTS.items():
        for seed in cells:
            if group == "mixed50_sg":
                manifest = json.loads((MSR_ROOT / "runs" / group / f"seed{seed}/run_manifest.json").read_text())
            else:
                manifest = json.loads((MATURITY_ROOT / "runs" / group / f"seed{seed}/run_manifest.json").read_text())
            configs.append({key: manifest.get("config", {}).get(key) for key in common_config_keys})
    config_pass = all(config == configs[0] for config in configs[1:])
    specialist_tape_changes = {}
    for group in ("fl_nominal_expert", "fl_f0_expert"):
        values = []
        for seed in (1801, 1802):
            maturity_rows = read_csv(MATURITY_ROOT / "runs" / group / f"seed{seed}/paired_metrics.csv")
            msr_cell = [r for r in msr_rows if r["group"] == group and int(r["seed"]) == seed][0]
            values.append({"seed": seed, "370_JN": mean(maturity_rows, "J_nominal"), "370_JF": mean(maturity_rows, "J_failure"),
                           "380_JN": float(msr_cell["J_nominal"]), "380_JF": float(msr_cell["J_failure"])})
        specialist_tape_changes[group] = values
    max_relative_change = 0.0
    for values in specialist_tape_changes.values():
        for cell in values:
            for left, right in (("370_JN", "380_JN"), ("370_JF", "380_JF")):
                denom = max(1e-9, abs(cell[left]))
                max_relative_change = max(max_relative_change, abs(cell[right] - cell[left]) / denom)
    # Pre-registered audit rule: >20% specialist change indicates tape-sensitive
    # references (SVA-2); a semantic/config mismatch is SVA-3 regardless of size.
    replay_tolerance = 1e-4
    classification = "SVA-3" if not (manifest_pass and config_pass and max_replay_diff <= replay_tolerance) else (
        "SVA-2" if max_relative_change > 0.20 else "SVA-1"
    )
    result = {
        "protocol": "POST-MSR-SVA-V1", "classification": classification,
        "training_started": False, "enmm_started": False,
        "J_N_star": msr_result["J_N_star"], "J_F_star": msr_result["J_F_star"],
        "mixed50": msr_result["mixed50"], "classification_basis": {
            "C_N": "pooled Mixed-50 J_nominal / pooled nominal-expert J_nominal",
            "C_F": "pooled Mixed-50 J_failure / pooled F0-expert J_failure",
            "C_min": "min(C_N, C_F)",
        },
        "consistency": {"evaluation_manifests": manifest_pass, "common_config": config_pass,
                         "tape_hashes": sorted(tape_hashes), "max_replay_abs_diff": max_replay_diff,
                         "replay_numeric_tolerance": replay_tolerance,
                         "max_specialist_relative_cross_tape_change": max_relative_change},
        "specialist_cross_tape": specialist_tape_changes,
    }
    (args.output_root / "SVA_RESULT.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
