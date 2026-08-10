"""Frozen hierarchical paired analysis for completed v1.9 F2-R2 records."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np

from check_v1_9_f2_r2_artifacts import validate
from f2_r2_common import (
    BOOTSTRAP_RESAMPLES,
    BOOTSTRAP_SEED,
    F2_EPISODE_IDS,
    F2_PROTOCOL,
    METHOD_SPECS,
    PRIMARY_COMPARATOR,
    PRIMARY_SESOI_DELTA_RMTE80,
    SECONDARY_COMPARATOR,
    write_new_json,
)


METRICS = (
    "rmte80", "establishment_probability80", "terminal_failure_incidence80",
    "active_not_established_probability80", "rmte220", "establishment_probability220",
    "terminal_failure_incidence220", "active_not_established_probability220", "rmpe80",
    "physical_engagement_probability80", "rmpe220", "physical_engagement_probability220",
)


def event_metric_vectors(records: list[dict]) -> dict[str, np.ndarray]:
    values: dict[str, list[float]] = {metric: [] for metric in METRICS}
    for row in records:
        event_time = float(row["event_time"])
        established80 = float(bool(int(row["event_observed"])) and 0.0 <= event_time <= 80.0)
        established220 = float(bool(int(row["event_observed"])) and 0.0 <= event_time <= 220.0)
        terminal_time = float(row["terminal_failure_time"])
        terminal80 = float(bool(int(row["terminal_failure_observed"])) and 0.0 <= terminal_time <= 80.0)
        terminal220 = float(bool(int(row["terminal_failure_observed"])) and 0.0 <= terminal_time <= 220.0)
        physical_time = float(row["physical_event_time"])
        physical80 = float(bool(int(row["physical_event_observed"])) and 0.0 <= physical_time <= 80.0)
        physical220 = float(bool(int(row["physical_event_observed"])) and 0.0 <= physical_time <= 220.0)
        values["rmte80"].append(event_time if established80 else 80.0)
        values["establishment_probability80"].append(established80)
        values["terminal_failure_incidence80"].append(terminal80)
        values["active_not_established_probability80"].append(1.0 - established80 - terminal80)
        values["rmte220"].append(event_time if established220 else 220.0)
        values["establishment_probability220"].append(established220)
        values["terminal_failure_incidence220"].append(terminal220)
        values["active_not_established_probability220"].append(1.0 - established220 - terminal220)
        values["rmpe80"].append(physical_time if physical80 else 80.0)
        values["physical_engagement_probability80"].append(physical80)
        values["rmpe220"].append(physical_time if physical220 else 220.0)
        values["physical_engagement_probability220"].append(physical220)
    return {metric: np.asarray(vector, dtype=float) for metric, vector in values.items()}


def load_vectors(root: Path) -> dict[str, np.ndarray]:
    result: dict[str, list[np.ndarray]] = {metric: [] for metric in METRICS}
    for method, _, _ in METHOD_SPECS:
        for seed in range(8):
            records_path = root / f"{method}_seed{seed}" / "episode_event_records.csv"
            with records_path.open(encoding="utf-8", newline="") as handle:
                records = list(csv.DictReader(handle))
            if [int(row["episode_seed"]) for row in records] != list(F2_EPISODE_IDS):
                raise RuntimeError(f"F2 analysis pairing error in {method}/seed{seed}")
            vectors = event_metric_vectors(records)
            for metric in METRICS:
                result.setdefault(f"{method}:{metric}", []).append(vectors[metric])
    return {
        key: np.stack(rows, axis=0)
        for key, rows in result.items()
        if key.startswith(("pcrf_r2:", "single_r2:", "matched_nongraph_r2:"))
    }


def hierarchical_paired_bootstrap(left: np.ndarray, right: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Resample matched training seeds, then matched episodes within each seed."""
    if left.shape != right.shape or left.shape != (8, 300):
        raise ValueError("paired F2 metric matrices must be exactly 8 training seeds x 300 episodes")
    samples = np.empty(BOOTSTRAP_RESAMPLES, dtype=float)
    for index in range(BOOTSTRAP_RESAMPLES):
        selected_seeds = rng.integers(0, left.shape[0], size=left.shape[0])
        per_seed = []
        for seed in selected_seeds:
            episode_indices = rng.integers(0, left.shape[1], size=left.shape[1])
            per_seed.append(float(np.mean(left[seed, episode_indices] - right[seed, episode_indices])))
        samples[index] = float(np.mean(per_seed))
    return samples


def comparison_summary(left: np.ndarray, right: np.ndarray, metric: str, rng: np.random.Generator) -> dict:
    bootstrap = hierarchical_paired_bootstrap(left, right, rng)
    seed_effects = np.mean(left - right, axis=1)
    return {
        "metric": metric,
        "direction": "pcrf_minus_comparator",
        "pcrf_mean": float(np.mean(left)),
        "comparator_mean": float(np.mean(right)),
        "delta_pcrf_minus_comparator": float(np.mean(left - right)),
        "seed_level_deltas": [float(value) for value in seed_effects],
        "same_direction_seed_count": int(np.sum(seed_effects < 0.0)) if metric.startswith(("rmte", "rmpe", "terminal", "active")) else int(np.sum(seed_effects > 0.0)),
        "bootstrap_ci95": [float(np.quantile(bootstrap, 0.025)), float(np.quantile(bootstrap, 0.975))],
        "bootstrap_probability_delta_lt_zero": float(np.mean(bootstrap < 0.0)),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--expected-f1-source-commit", required=True)
    parser.add_argument("--expected-evaluator-source-commit", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    validate(args.root, args.expected_f1_source_commit, args.expected_evaluator_source_commit)
    matrices = load_vectors(args.root)
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    comparisons = {}
    for comparator in (PRIMARY_COMPARATOR, SECONDARY_COMPARATOR):
        comparisons[comparator] = {
            metric: comparison_summary(
                matrices[f"pcrf_r2:{metric}"], matrices[f"{comparator}:{metric}"], metric, rng
            )
            for metric in METRICS
        }
    primary = comparisons[PRIMARY_COMPARATOR]["rmte80"]
    result = {
        "status": "F2_R2_CONFIRMATORY_ANALYSIS_COMPLETE__AUTHOR_REVIEW_REQUIRED",
        "protocol_version": F2_PROTOCOL,
        "f1_source_commit": args.expected_f1_source_commit,
        "f2_evaluator_source_commit": args.expected_evaluator_source_commit,
        "bootstrap": {
            "resamples": BOOTSTRAP_RESAMPLES,
            "seed": BOOTSTRAP_SEED,
            "hierarchy": "paired_training_seed_then_matched_episode",
        },
        "primary": {
            "comparator": PRIMARY_COMPARATOR,
            "endpoint": "rmte80",
            "delta_definition": "pcrf_r2_minus_single_r2",
            "sesoi_delta_rmte80": PRIMARY_SESOI_DELTA_RMTE80,
            "result": primary,
            "automatic_claim_verdict": "NOT_ASSIGNED__AUTHOR_MUST_REVIEW_ALL_FROZEN_CONDITIONS",
        },
        "comparisons": comparisons,
    }
    write_new_json(args.output, result)
    print("F2_R2_CONFIRMATORY_ANALYSIS_COMPLETE: complete results written for author review")


if __name__ == "__main__":
    main()
