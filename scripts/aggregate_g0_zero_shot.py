"""Aggregate the frozen G0 zero-shot evidence without policy re-evaluation."""
from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
PRIMARY = ("U1_scout_node_failure", "U2_static_symmetric_direct_prune", "U3_static_directed_scout_to_attacker_prune", "U4_scout_failure_symmetric_direct_prune", "U5_relay_failure_directed_direct_prune")
PARAMETER = ("parameter_timing_20_80", "parameter_duration_44_140")


def mean(values: Iterable[float]) -> float:
    data = list(values)
    return sum(data) / len(data) if data else math.nan


def number(value: str) -> float:
    return float(value) if value not in ("", None) else math.nan


def read_rows(path: Path) -> list[dict[str, Any]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        for key in ("J", "terminal_step", "success", "collision", "timeout", "constraint_violation", "failure_exposed", "alive_at_onset", "pre_trigger_collision", "episode_length", "traveled_distance", "control_effort", "direct_path_fraction_during_failure", "relay_path_fraction_during_failure", "task_support_fraction_during_failure", "legal_information_fraction_during_failure", "path_switch_count"):
            row[key] = number(row[key])
        row["training_seed"] = int(row["training_seed"])
    return rows


def aggregate(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, int, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[(row["method"], row["training_contract"], row["training_seed"], row["condition"])].append(row)
    output = []
    for (method, contract, seed, condition), data in sorted(groups.items()):
        first = data[0]
        risk = [row for row in data if row["alive_at_onset"] == 1]
        output.append({
            "method": method, "training_contract": contract, "training_seed": seed,
            "condition": condition, "family": first["family"], "episodes": len(data),
            "J": mean(row["J"] for row in data), "J_sd_episode_descriptive": statistics.pstdev(row["J"] for row in data),
            "collision": mean(row["collision"] for row in data), "timeout": mean(row["timeout"] for row in data),
            "constraint_violation": mean(row["constraint_violation"] for row in data),
            "failure_exposure_all_episodes": mean(row["failure_exposed"] for row in data),
            "survival_to_onset_fraction": mean(row["alive_at_onset"] for row in data) if first["family"] != "reference" else math.nan,
            "trigger_success_among_risk_set": mean(row["failure_exposed"] for row in risk) if risk else math.nan,
            "pre_trigger_collision": mean(row["pre_trigger_collision"] for row in data),
            "episode_length": mean(row["episode_length"] for row in data),
            "traveled_distance": mean(row["traveled_distance"] for row in data),
            "control_effort": mean(row["control_effort"] for row in data),
            "direct_path_fraction": mean(row["direct_path_fraction_during_failure"] for row in data),
            "relay_path_fraction": mean(row["relay_path_fraction_during_failure"] for row in data),
            "task_support_fraction": mean(row["task_support_fraction_during_failure"] for row in data),
            "legal_information_fraction": mean(row["legal_information_fraction_during_failure"] for row in data),
            "path_switch_count": mean(row["path_switch_count"] for row in data),
        })
    return output


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def utr_decision(seed_rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_seed: dict[int, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in seed_rows:
        if row["method"] == "UTR-SG-MAPPO":
            by_seed[row["training_seed"]][row["condition"]] = row
    stats = []
    for seed, conditions in sorted(by_seed.items()):
        seen = conditions["seen_f0_44_80"]["J"]
        structural = mean(conditions[item]["J"] for item in PRIMARY)
        parameter = mean(conditions[item]["J"] for item in PARAMETER)
        sgap, pgap = seen - structural, seen - parameter
        stats.append({"seed": seed, "J_seen_F0": seen, "J_structural_primary_mean": structural, "J_parameter_mean": parameter, "structural_gap": sgap, "parameter_gap": pgap, "structural_minus_parameter_gap": sgap - pgap})
    pooled = {row["condition"]: mean(row["J"] for row in seed_rows if row["method"] == "UTR-SG-MAPPO" and row["condition"] == row["condition"]) for row in []}
    # Compute pooled topology gaps from the independent training-seed means.
    topology_mean = {condition: mean(conditions[condition]["J"] for conditions in by_seed.values()) for condition in ("seen_f0_44_80", *PRIMARY, *PARAMETER)}
    pooled_seen = topology_mean["seen_f0_44_80"]
    pooled_threshold_a = max(10.0, .15 * abs(pooled_seen))
    seed_threshold_a = [max(10.0, .15 * abs(row["J_seen_F0"])) for row in stats]
    seed_threshold_b = [max(5.0, .05 * abs(row["J_seen_F0"])) for row in stats]
    med_structural = statistics.median(row["structural_gap"] for row in stats)
    med_delta = statistics.median(row["structural_minus_parameter_gap"] for row in stats)
    a = (med_structural > statistics.median(seed_threshold_a) and med_delta > max(5.0, .10 * abs(statistics.median(row["J_seen_F0"] for row in stats))) and sum(row["structural_minus_parameter_gap"] > 0 for row in stats) >= 4 and sum(pooled_seen - topology_mean[condition] > pooled_threshold_a for condition in PRIMARY) >= 3)
    b = (not a and med_structural > statistics.median(seed_threshold_b) and med_delta > 0 and sum(row["structural_minus_parameter_gap"] > 0 for row in stats) >= 3)
    decision = "A — TOPOLOGY_GENERALIZATION_GAP_VALIDATED" if a else "B — MODERATE_TOPOLOGY_GENERALIZATION_GAP" if b else "C — NO_ACTIONABLE_TOPOLOGY_GENERALIZATION_GAP"
    return {"decision": decision, "utr_seed_statistics": stats, "utr_topology_seed_mean_J": topology_mean, "primary_topology_count_above_A_threshold": sum(pooled_seen - topology_mean[condition] > pooled_threshold_a for condition in PRIMARY), "pooled_A_threshold": pooled_threshold_a, "median_structural_gap": med_structural, "median_structural_minus_parameter_gap": med_delta, "seed_positive_structural_minus_parameter_gap": sum(row["structural_minus_parameter_gap"] > 0 for row in stats)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifacts", type=Path, default=ROOT / "artifacts/g0")
    args = parser.parse_args()
    raw = read_rows(args.artifacts / "g0_episode_results.csv")
    if len(raw) != 5000:
        raise RuntimeError(f"expected 5000 frozen G0 records, found {len(raw)}")
    seed_rows = aggregate(raw)
    if len(seed_rows) != 100:
        raise RuntimeError(f"expected 100 policy-seed-condition aggregates, found {len(seed_rows)}")
    write_csv(args.artifacts / "seed_topology_results.csv", seed_rows)
    topology_rows = []
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in seed_rows:
        groups[(row["method"], row["training_contract"], row["condition"])].append(row)
    for (method, contract, condition), data in sorted(groups.items()):
        numeric_keys = {
            "episodes", "J", "collision", "timeout", "constraint_violation",
            "failure_exposure_all_episodes", "survival_to_onset_fraction",
            "trigger_success_among_risk_set", "pre_trigger_collision",
            "episode_length", "traveled_distance", "control_effort",
            "direct_path_fraction", "relay_path_fraction", "task_support_fraction",
            "legal_information_fraction", "path_switch_count",
        }
        result = {key: mean(row[key] for row in data) for key in numeric_keys}
        result.update({"method": method, "training_contract": contract, "condition": condition, "family": data[0]["family"], "training_seeds": len(data), "J_seed_sd": statistics.pstdev(row["J"] for row in data)})
        topology_rows.append(result)
    write_csv(args.artifacts / "topology_results.csv", topology_rows)
    decision = utr_decision(seed_rows)
    decision.update({"protocol": "G0-TOPOLOGY-GENERALIZABLE-MARL-V1", "raw_records": len(raw), "seed_condition_records": len(seed_rows), "topology_records": len(topology_rows), "primary_training_unit": "training seed", "DRTP_pooling": "reported separately by historical contract; not pooled for primary inference"})
    (args.artifacts / "generalization_summary.json").write_text(json.dumps(decision, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
