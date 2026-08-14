"""Aggregate final evaluation and fixed-milestone curves for Phase FL maturity."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


ARMS = ("fl_nominal_expert", "fl_f0_expert")
SEEDS = (1801, 1802)
MILESTONES = {1172: "300k", 1953: "500k", 2930: "750k", 3907: "1m"}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def mean(rows: list[dict[str, str]], key: str) -> float:
    return sum(float(row[key]) for row in rows) / len(rows)


def validate_run(run: Path, arm: str, seed: int, tape_hash: str) -> tuple[dict, list[dict[str, str]], list[dict[str, str]]]:
    manifest = json.loads((run / "run_manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "completed", manifest
    assert manifest["protocol"] == "PHASE-FL-MATURITY-V1", manifest
    assert manifest["arm"] == arm and manifest["seed"] == seed, manifest
    assert manifest["environment_steps"] == 1000192 and manifest["updates"] == 3907, manifest
    assert manifest["num_envs"] == 4 and manifest["rollout_steps"] == 64, manifest
    assert manifest["graph_encoder"] == "single" and manifest["parameter_count"] == 116728, manifest
    assert manifest["checkpoint_selection"] == "fixed_final_update_only", manifest
    assert manifest["milestones_for_curve_only"] is True, manifest
    assert not manifest["resume"] and not manifest["early_stopping"] and not manifest["checkpoint_promotion"], manifest
    assert manifest["canonical_seeds_used"] is False, manifest
    assert manifest["tape_hash"] == tape_hash and manifest["tape_start"] == 370000, manifest
    paired = read_csv(run / "paired_metrics.csv")
    train = read_csv(run / "train_log.csv")
    assert len(paired) == 50 and len(train) == 3907, (len(paired), len(train))
    assert all(float(row["failure_exposed"]) == 1.0 for row in paired), arm
    for update, label in MILESTONES.items():
        assert (run / f"actor_critic_milestone_{label}.pt").exists(), label
    return manifest, paired, train


def summarize(arm: str, seed: int, paired: list[dict[str, str]]) -> dict:
    return {
        "arm": arm, "seed": seed,
        "J_nominal": mean(paired, "J_nominal"), "J_failure": mean(paired, "J_failure"),
        "Delta_J": mean(paired, "delta_J"),
        "collision_failure": mean(paired, "collision_failure"),
        "timeout_failure": mean(paired, "timeout_failure"),
        "constraint_failure": mean(paired, "constraint_failure"),
        "failure_exposure": mean(paired, "failure_exposed"),
        "episode_length_nominal": mean(paired, "episode_length_nominal"),
        "episode_length_failure": mean(paired, "episode_length_failure"),
        "path_switch_count_failure": mean(paired, "path_switch_count_failure"),
        "direct_path_fraction_failure": mean(paired, "direct_path_fraction_failure"),
        "relay_path_fraction_failure": mean(paired, "relay_path_fraction_failure"),
        "task_support_fraction_failure": mean(paired, "task_support_fraction_failure"),
        "legal_information_fraction_failure": mean(paired, "legal_information_fraction_failure"),
        "mean_cache_age_failure": mean(paired, "mean_cache_age_failure"),
        "traveled_distance_failure": mean(paired, "traveled_distance_failure"),
        "control_effort_failure": mean(paired, "control_effort_failure"),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-root", type=Path, default=Path("results/development/phase_fl_maturity"))
    args = parser.parse_args()
    tape = json.loads((args.results_root / "tape_manifest.json").read_text(encoding="utf-8"))
    rows, curve_rows, manifests = [], [], []
    for arm in ARMS:
        for seed in SEEDS:
            run = args.results_root / "runs" / arm / f"seed{seed}"
            manifest, paired, train = validate_run(run, arm, seed, tape["tape_hash"])
            manifests.append(manifest)
            rows.append(summarize(arm, seed, paired))
            for update, label in MILESTONES.items():
                log = next(row for row in train if int(row["update"]) == update)
                curve_rows.append({
                    "arm": arm, "seed": seed, "milestone": label,
                    "update": update, "environment_steps": update * 4 * 64,
                    "train_avg_reward": log["train_avg_reward"], "loss": log["loss"],
                    "policy_loss": log["policy_loss"], "value_loss": log["value_loss"],
                    "entropy": log["entropy"], "approx_kl": log["approx_kl"],
                    "clip_fraction": log["clip_fraction"], "grad_norm": log["grad_norm"],
                    "explained_variance": log["explained_variance"],
                    "checkpoint_sha256": manifest["milestone_checkpoint_sha256"][label],
                })
    fields = list(rows[0])
    with (args.results_root / "per_seed_final_summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader(); writer.writerows(rows)
    curve_fields = list(curve_rows[0])
    with (args.results_root / "milestone_learning_curves.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=curve_fields); writer.writeheader(); writer.writerows(curve_rows)
    pooled = {}
    for arm in ARMS:
        cells = [row for row in rows if row["arm"] == arm]
        pooled[arm] = {key: sum(row[key] for row in cells) / len(cells) for key in fields if key not in {"arm", "seed"}}
    result = {
        "protocol": "PHASE-FL-MATURITY-V1", "complete": True, "training_runs": 4,
        "environment_steps_per_run": 1000192, "nominal_maturity_curve": True,
        "f0_maturity_curve": True, "pooled_final": pooled, "per_seed_final": rows,
        "milestone_updates": MILESTONES,
        "milestone_steps": {label: update * 4 * 64 for update, label in MILESTONES.items()},
        "tape_start": 370000, "episodes_per_condition": 50, "tape_hash": tape["tape_hash"],
        "canonical_seeds_used": False, "checkpoint_selection": "1m_final_only",
        "milestones_used_for_selection": False, "new_algorithm_started": False,
        "manifest_count": len(manifests),
    }
    (args.results_root / "FL_MATURITY_RESULT.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
