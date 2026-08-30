"""Shared frozen helpers for PR-DRTP B4 zero-training feasibility."""
from __future__ import annotations

import hashlib
import math
import statistics
from pathlib import Path
from typing import Iterable, Mapping


PROTOCOL = "PR-DRTP-B4-ZERO-TRAINING-FEASIBILITY-V1"
ARMS = ("utr_sg", "drtp_sg")
OUTCOME_CONDITIONS = (
    "nominal", "F0_44_80", "T28_28_80", "D120_44_120", "C28_120"
)
FAILURE_CONDITIONS = OUTCOME_CONDITIONS[1:]
ENDPOINTS = ("J_nominal", "J_F0", "J_pert_mean", "J_pert_worst")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def mean(values: Iterable[float]) -> float:
    materialized = list(values)
    if not materialized:
        raise ValueError("mean requires at least one value")
    return sum(materialized) / len(materialized)


def dispersion(values: Iterable[float]) -> dict[str, float]:
    materialized = list(values)
    if len(materialized) < 2:
        raise ValueError("dispersion requires at least two values")
    median = statistics.median(materialized)
    ordered = sorted(materialized)
    return {
        "range": max(materialized) - min(materialized),
        "sample_sd": statistics.stdev(materialized),
        "mad": statistics.median(abs(value - median) for value in materialized),
        "iqr": ordered[-2] - ordered[1] if len(ordered) == 5 else math.nan,
    }


def endpoint_cell(rows: Mapping[str, Mapping[str, str]]) -> dict[str, float]:
    if set(rows) != set(OUTCOME_CONDITIONS):
        raise ValueError("incomplete outcome conditions")
    value = lambda condition, key: float(rows[condition][key])
    failures = [value(condition, "J") for condition in FAILURE_CONDITIONS]
    return {
        "J_nominal": value("nominal", "J"),
        "J_F0": value("F0_44_80", "J"),
        "J_pert_mean": mean(failures),
        "J_pert_worst": min(failures),
        "collision": mean(value(condition, "collision") for condition in FAILURE_CONDITIONS),
        "timeout": mean(value(condition, "timeout") for condition in FAILURE_CONDITIONS),
        "constraint_violation": max(
            value(condition, "constraint_violation") for condition in FAILURE_CONDITIONS
        ),
    }


def retention_ratio(candidate: float, reference: float, scale_floor: float) -> float:
    if reference > 0:
        return candidate / reference
    return 1.0 + (candidate - reference) / max(abs(reference), scale_floor)


def catastrophic(
    candidate: Mapping[str, float], reference: Mapping[str, float], scale_floor: float
) -> bool:
    f0_ratio = retention_ratio(candidate["J_F0"], reference["J_F0"], scale_floor)
    worst_ratio = retention_ratio(
        candidate["J_pert_worst"], reference["J_pert_worst"], scale_floor
    )
    performance_collapse = (
        (f0_ratio < 0.70 and worst_ratio < 0.85)
        or (worst_ratio < 0.70 and f0_ratio < 0.85)
    )
    safety_collapse = (
        candidate["timeout"] - reference["timeout"] > 0.20
        and (f0_ratio < 0.85 or worst_ratio < 0.85)
    )
    return performance_collapse or safety_collapse


def selector_score(condition_rows: Mapping[str, Mapping[str, str]]) -> dict[str, float | bool]:
    values = [float(row["J"]) for row in condition_rows.values()]
    eligible = all(float(row["constraint_violation"]) == 0.0 for row in condition_rows.values())
    return {
        "eligible": eligible,
        "minimum_condition_J": min(values),
        "mean_condition_J": mean(values),
    }


def select_seed(
    members: Iterable[int], scores: Mapping[int, Mapping[str, float | bool]]
) -> int:
    eligible = [seed for seed in members if bool(scores[seed]["eligible"])]
    if not eligible:
        raise RuntimeError("population has no selector-eligible member")
    return max(
        eligible,
        key=lambda seed: (
            float(scores[seed]["minimum_condition_J"]),
            float(scores[seed]["mean_condition_J"]),
            -seed,
        ),
    )
