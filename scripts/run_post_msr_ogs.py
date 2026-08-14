"""Zero-training OOD timing/duration/compound gap scan for mature checkpoints."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import run_phase_fl_single as fl  # noqa: E402
import run_phase_rsg1_development_smoke as evaluator  # noqa: E402
from envs.uav_intercept_3d_env import UAVIntercept3DConfig, UAVIntercept3DEnv  # noqa: E402


MSR_ROOT = ROOT / "archival/results/phase_msr_cloud_20260814/results/development/phase_msr_mature_shared_policy"
MATURITY_ROOT = ROOT / "archival/results/phase_fl_maturity_cloud_20260814/results/development/phase_fl_maturity"
TAPE_START = 410000
EPISODES = 100
SEEDS = (1801, 1802)
CONDITIONS = {
    "nominal": None,
    "f0_seen_44_80": (44, 80),
    "timing_28_80": (28, 80), "timing_36_80": (36, 80),
    "timing_52_80": (52, 80), "timing_60_80": (60, 80),
    "duration_44_40": (44, 40), "duration_44_60": (44, 60),
    "duration_44_100": (44, 100), "duration_44_120": (44, 120),
    "compound_28_120": (28, 120), "compound_60_120": (60, 120),
}
OOD_CONDITIONS = tuple(name for name in CONDITIONS if name not in {"nominal", "f0_seen_44_80"})
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


def tape_manifest() -> dict:
    payload = {
        "protocol": "POST-MSR-OGS-TAPE-V1",
        "episode_ids": list(range(TAPE_START, TAPE_START + EPISODES)),
        "conditions": list(CONDITIONS), "episodes_per_condition": EPISODES,
        "same_base_ids_across_conditions": True, "canonical": False,
        "failure_semantics": "relay_node_1_edge_removal_at_onset_for_duration",
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return {**payload, "tape_hash": hashlib.sha256(encoded).hexdigest()}


def variant_env(seed: int, spec: tuple[int, int] | None) -> UAVIntercept3DEnv:
    onset, duration = spec if spec is not None else (0, 0)
    return UAVIntercept3DEnv(UAVIntercept3DConfig(
        seed=seed, target_policy="straight", strict_target_sensing=True,
        agent_target_info_bottleneck=True, relay_dependent_task=True,
        business_grounded_geometry=True, communication_range_scale=1.0,
        communication_dropout_prob=0.0, message_delay_steps=0,
        radar_dropout_prob=0.0, max_steps=260, min_success_step=260,
        failed_blue_agent=1 if spec is not None else -1,
        node_failure_start_step=onset, node_failure_duration_steps=duration,
    ))


def finite_mean(rows: list[dict], key: str) -> float:
    values = [float(row[key]) for row in rows if math.isfinite(float(row[key]))]
    return sum(values) / len(values) if values else math.nan


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=ROOT / "results/development/post_msr_ogs")
    args = parser.parse_args()
    if args.output_root.exists() and any(args.output_root.iterdir()):
        raise FileExistsError(f"refusing to overwrite: {args.output_root}")
    args.output_root.mkdir(parents=True, exist_ok=True)
    tape = tape_manifest()
    (args.output_root / "tape_manifest.json").write_text(json.dumps(tape, indent=2) + "\n", encoding="utf-8")

    raw_rows = []
    total = len(CHECKPOINTS) * len(SEEDS) * len(CONDITIONS) * EPISODES
    done = 0
    for group, cells in CHECKPOINTS.items():
        for seed, checkpoint in cells.items():
            agent = fl.build_agent({"graph_encoder": "single", "hidden_dim": 115}, checkpoint, seed)
            for condition, spec in CONDITIONS.items():
                original = evaluator.frozen_env
                evaluator.frozen_env = lambda episode_seed, failure_on, _spec=spec: variant_env(episode_seed, _spec)
                try:
                    for episode_id in tape["episode_ids"]:
                        eval_condition = "nominal" if spec is None else "relay_failure"
                        row, _ = evaluator.evaluate_episode(agent, group, seed, episode_id, eval_condition)
                        row.update({"ogs_condition": condition, "onset": "" if spec is None else spec[0],
                                    "duration": "" if spec is None else spec[1],
                                    "checkpoint_sha256": fl.sha256(checkpoint), "tape_hash": tape["tape_hash"]})
                        raw_rows.append(row)
                        done += 1
                        if done % 200 == 0:
                            print(f"OGS progress {done}/{total} ({100*done/total:.1f}%)", flush=True)
                finally:
                    evaluator.frozen_env = original
    raw_fields = list(raw_rows[0])
    with (args.output_root / "ogs_raw_episode_metrics.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=raw_fields); writer.writeheader(); writer.writerows(raw_rows)

    per_seed = []
    for group in CHECKPOINTS:
        for seed in SEEDS:
            cell = [r for r in raw_rows if r["method"] == group and int(r["train_seed"]) == seed]
            anchor_nominal = finite_mean([r for r in cell if r["ogs_condition"] == "nominal"], "J")
            anchor_f0 = finite_mean([r for r in cell if r["ogs_condition"] == "f0_seen_44_80"], "J")
            for condition in CONDITIONS:
                condition_rows = [r for r in cell if r["ogs_condition"] == condition]
                score = finite_mean(condition_rows, "J")
                per_seed.append({
                    "group": group, "seed": seed, "condition": condition,
                    "onset": "" if CONDITIONS[condition] is None else CONDITIONS[condition][0],
                    "duration": "" if CONDITIONS[condition] is None else CONDITIONS[condition][1],
                    "J_condition": score, "D_condition": anchor_nominal - score,
                    "R_condition_vs_seen_F0": score / anchor_f0 if anchor_f0 else math.nan,
                    "collision_rate": finite_mean(condition_rows, "collision"),
                    "timeout_rate": finite_mean(condition_rows, "timeout"),
                    "constraint_violation": finite_mean(condition_rows, "constraint_violation"),
                    "failure_exposure": finite_mean(condition_rows, "failure_exposed"),
                    "episode_length": finite_mean(condition_rows, "terminal_step"),
                    "path_switch_count": finite_mean(condition_rows, "path_switch_count"),
                    "direct_path_fraction": finite_mean(condition_rows, "direct_path_fraction_during_failure"),
                    "relay_path_fraction": finite_mean(condition_rows, "relay_path_fraction_during_failure"),
                    "task_support_fraction": finite_mean(condition_rows, "task_support_fraction_during_failure"),
                    "legal_information_fraction": finite_mean(condition_rows, "legal_information_fraction_during_failure"),
                    "mean_cache_age": finite_mean(condition_rows, "mean_cache_age_during_failure"),
                })
    with (args.output_root / "ogs_per_seed_summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(per_seed[0])); writer.writeheader(); writer.writerows(per_seed)

    pooled = []
    for group in CHECKPOINTS:
        for condition in CONDITIONS:
            cells = [r for r in per_seed if r["group"] == group and r["condition"] == condition]
            pooled.append({"group": group, "condition": condition,
                           **{key: sum(float(r[key]) for r in cells) / len(cells)
                              for key in ("J_condition", "D_condition", "R_condition_vs_seen_F0", "collision_rate",
                                          "timeout_rate", "constraint_violation", "failure_exposure", "episode_length",
                                          "path_switch_count", "direct_path_fraction", "relay_path_fraction",
                                          "task_support_fraction", "legal_information_fraction", "mean_cache_age")}})
    with (args.output_root / "ogs_pooled_summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(pooled[0])); writer.writeheader(); writer.writerows(pooled)

    mixed = [r for r in per_seed if r["group"] == "mixed50_sg"]
    ood = [r for r in mixed if r["condition"] in OOD_CONDITIONS]
    ood_by_seed = []
    for seed in SEEDS:
        cells = [r for r in ood if r["seed"] == seed]
        values = [float(r["J_condition"]) for r in cells]
        f0 = float(next(r for r in mixed if r["seed"] == seed and r["condition"] == "f0_seen_44_80")["J_condition"])
        ood_by_seed.append({"seed": seed, "J_F0_seen": f0, "J_OOD_mean": sum(values) / len(values),
                            "J_OOD_worst": min(values), "R_OOD_mean": sum(values) / len(values) / f0,
                            "R_OOD_worst": min(values) / f0})
    pooled_ood = {key: sum(float(row[key]) for row in ood_by_seed) / len(ood_by_seed)
                  for key in ("J_OOD_mean", "J_OOD_worst", "R_OOD_mean", "R_OOD_worst")}
    result = {"protocol": "POST-MSR-OGS-V1", "training_started": False, "enmm_started": False,
              "tape": tape, "ood_conditions": list(OOD_CONDITIONS), "per_seed": ood_by_seed,
              "pooled": pooled_ood, "mixed50_safety": [r for r in pooled if r["group"] == "mixed50_sg"]}
    (args.output_root / "OGS_RESULT.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
