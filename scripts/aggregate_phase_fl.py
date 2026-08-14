"""Aggregate and classify the frozen Phase-FL diagnostic."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


ARMS = ("fl_nominal_expert", "fl_f0_expert")
SEEDS = (1801, 1802)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def mean(rows: list[dict[str, str]], key: str) -> float:
    return sum(float(row[key]) for row in rows) / len(rows)


def validate_run(run: Path, arm: str, seed: int, tape_hash: str) -> tuple[dict, list[dict[str, str]]]:
    manifest = json.loads((run / "run_manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "completed", manifest
    assert manifest["arm"] == arm and manifest["seed"] == seed, manifest
    assert manifest["environment_steps"] == 300032 and manifest["updates"] == 1172, manifest
    assert manifest["graph_encoder"] == "single" and manifest["parameter_count"] == 116728, manifest
    assert manifest["checkpoint_selection"] == "fixed_final_update_only", manifest
    assert not manifest["resume"] and not manifest["early_stopping"] and not manifest["checkpoint_promotion"], manifest
    assert manifest["canonical_seeds_used"] is False, manifest
    assert manifest["tape_hash"] == tape_hash and manifest["tape_start"] == 370000, manifest
    paired = read_csv(run / "paired_metrics.csv")
    raw = read_csv(run / "raw_episode_metrics.csv")
    assert len(paired) == 50 and len(raw) == 100, (len(paired), len(raw))
    assert all(float(row["failure_exposed"]) == 1.0 for row in paired), arm
    return manifest, paired


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
    parser.add_argument("--results-root", type=Path, default=Path("results/development/phase_fl_failure_learnability"))
    args = parser.parse_args()
    tape = json.loads((args.results_root / "tape_manifest.json").read_text(encoding="utf-8"))
    rows, manifests = [], []
    for arm in ARMS:
        for seed in SEEDS:
            manifest, paired = validate_run(args.results_root / "runs" / arm / f"seed{seed}", arm, seed, tape["tape_hash"])
            manifests.append(manifest)
            rows.append(summarize(arm, seed, paired))
    fields = list(rows[0])
    with (args.results_root / "per_seed_summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader(); writer.writerows(rows)
    pooled = {}
    for arm in ARMS:
        cells = [row for row in rows if row["arm"] == arm]
        pooled[arm] = {key: sum(row[key] for row in cells) / len(cells) for key in fields if key not in {"arm", "seed"}}
    seed_comparisons = []
    for seed in SEEDS:
        nominal = next(row for row in rows if row["arm"] == "fl_nominal_expert" and row["seed"] == seed)
        f0 = next(row for row in rows if row["arm"] == "fl_f0_expert" and row["seed"] == seed)
        gf = f0["J_failure"] - nominal["J_failure"]
        gn = f0["J_nominal"] - nominal["J_nominal"]
        seed_comparisons.append({"seed": seed, "G_F": gf, "G_N": gn,
                                 "R_F": gf / (abs(nominal["J_failure"]) + 1e-8),
                                 "R_N": gn / (abs(nominal["J_nominal"]) + 1e-8)})
    gf = pooled["fl_f0_expert"]["J_failure"] - pooled["fl_nominal_expert"]["J_failure"]
    gn = pooled["fl_f0_expert"]["J_nominal"] - pooled["fl_nominal_expert"]["J_nominal"]
    rf = gf / (abs(pooled["fl_nominal_expert"]["J_failure"]) + 1e-8)
    rn = gn / (abs(pooled["fl_nominal_expert"]["J_nominal"]) + 1e-8)
    failure_clear = rf >= 0.10 and all(row["G_F"] >= 0 for row in seed_comparisons)
    nominal_decline = rn <= -0.10 and all(row["G_N"] <= 0 for row in seed_comparisons)
    category = "C" if failure_clear and nominal_decline else "A" if failure_clear else "B"
    result = {
        "protocol": "PHASE-FL-V1", "complete": True, "training_runs": 4,
        "pooled": pooled, "seed_comparisons": seed_comparisons,
        "pooled_G_F": gf, "pooled_G_N": gn, "pooled_R_F": rf, "pooled_R_N": rn,
        "thresholds": {"failure_relative_gain": 0.10, "nominal_relative_decline": -0.10},
        "failure_clearly_improves": failure_clear,
        "nominal_materially_declines": nominal_decline,
        "diagnostic_category": category,
        "category_label": {"A": "failure_learnable_shared_policy_interference",
                           "B": "failure_not_shown_learnable_current_formulation",
                           "C": "failure_learnable_nominal_failure_tradeoff"}[category],
        "tape_start": 370000, "episodes_per_condition": 50, "tape_hash": tape["tape_hash"],
        "canonical_seeds_used": False, "tp2_started": False,
        "new_algorithm_started": False, "manifest_count": len(manifests),
    }
    (args.results_root / "FL_RESULT.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
