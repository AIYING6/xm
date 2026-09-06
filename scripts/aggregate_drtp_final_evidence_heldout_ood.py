"""Summarize final held-out/OOD evidence without an automatic pass/fail gate."""
from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path


PROTOCOL = "DRTP-FINAL-EVIDENCE-HELDOUT-OOD-REPORT-V1"
STRUCTURAL = ("structural_scout_node", "structural_symmetric_longest_edge", "structural_directed_longest_edge", "structural_scout_node_plus_edge")
PARAMETER = ("parameter_early_relay", "parameter_long_relay")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict]) -> None:
    fields = list(dict.fromkeys(field for row in rows for field in row))
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader(); writer.writerows(rows)


def mean(values: list[float]) -> float:
    values = [value for value in values if math.isfinite(value)]
    return sum(values) / len(values) if values else math.nan


def seed_endpoints(rows: list[dict[str, str]]) -> list[dict]:
    cells: dict[tuple[str, str, int], dict[str, dict[str, str]]] = defaultdict(dict)
    for row in rows:
        cells[(row["cohort"], row["method"], int(row["train_seed"]))][row["condition"]] = row
    endpoints: list[dict] = []
    required = {"nominal_reference", *PARAMETER, *STRUCTURAL}
    for (cohort, method, seed), condition in sorted(cells.items()):
        if set(condition) != required:
            raise RuntimeError(f"incomplete held-out cell {cohort}/{method}/seed{seed}")
        entry = {"cohort": cohort, "method": method, "train_seed": seed}
        for family, names in (("parameter", PARAMETER), ("structural", STRUCTURAL)):
            for field in ("J", "success", "collision", "timeout", "constraint_violation"):
                values = [float(condition[name][field]) for name in names]
                entry[f"{family}_{field}_mean"] = mean(values)
                entry[f"{family}_{field}_worst"] = min(values) if field in {"J", "success"} else max(values)
        for field in ("J", "success", "collision", "timeout", "constraint_violation"):
            entry[f"nominal_{field}"] = float(condition["nominal_reference"][field])
        entry["structural_minus_parameter_J"] = entry["structural_J_mean"] - entry["parameter_J_mean"]
        endpoints.append(entry)
    return endpoints


def summary(endpoints: list[dict]) -> list[dict]:
    report: list[dict] = []
    metrics = ("nominal_J", "parameter_J_mean", "parameter_J_worst", "structural_J_mean", "structural_J_worst", "structural_minus_parameter_J", "structural_collision_mean", "structural_timeout_mean")
    for cohort in ("A", "B"):
        for method in ("utr_sg", "drtp_sg"):
            rows = [row for row in endpoints if row["cohort"] == cohort and row["method"] == method]
            for metric in metrics:
                values = [float(row[metric]) for row in rows]
                report.append({"cohort": cohort, "method": method, "metric": metric, "n_training_seeds": len(values), "mean": mean(values), "median": statistics.median(values), "min": min(values), "max": max(values), "sample_sd": statistics.stdev(values) if len(values) > 1 else 0.0})
    return report


def paired(endpoints: list[dict]) -> list[dict]:
    lookup = {(row["cohort"], row["method"], row["train_seed"]): row for row in endpoints}
    result: list[dict] = []
    for cohort in ("A", "B"):
        seeds = sorted(seed for c, method, seed in lookup if c == cohort and method == "utr_sg")
        for seed in seeds:
            utr, drtp = lookup[(cohort, "utr_sg", seed)], lookup[(cohort, "drtp_sg", seed)]
            result.append({
                "cohort": cohort, "train_seed": seed,
                "delta_parameter_J_mean": float(drtp["parameter_J_mean"]) - float(utr["parameter_J_mean"]),
                "delta_structural_J_mean": float(drtp["structural_J_mean"]) - float(utr["structural_J_mean"]),
                "delta_structural_J_worst": float(drtp["structural_J_worst"]) - float(utr["structural_J_worst"]),
                "delta_structural_collision_mean": float(drtp["structural_collision_mean"]) - float(utr["structural_collision_mean"]),
                "delta_structural_timeout_mean": float(drtp["structural_timeout_mean"]) - float(utr["structural_timeout_mean"]),
            })
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evaluation-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("explicit --execute is required")
    if args.output_root.exists():
        raise FileExistsError(f"refusing to overwrite {args.output_root}")
    manifest = json.loads((args.evaluation_root / "evaluation_manifest.json").read_text(encoding="utf-8"))
    if manifest.get("protocol") != "DRTP-FINAL-EVIDENCE-HELDOUT-OOD-EVALUATION-V1" or manifest.get("status") != "completed":
        raise RuntimeError("incomplete or incompatible final held-out/OOD evaluation")
    endpoints = seed_endpoints(read_csv(args.evaluation_root / "per_seed_condition_summary.csv"))
    summaries, paired_rows = summary(endpoints), paired(endpoints)
    args.output_root.mkdir(parents=True)
    write_csv(args.output_root / "DRTP_FINAL_EVIDENCE_PER_SEED_ENDPOINTS.csv", endpoints)
    write_csv(args.output_root / "DRTP_FINAL_EVIDENCE_COHORT_SUMMARY.csv", summaries)
    write_csv(args.output_root / "DRTP_FINAL_EVIDENCE_PAIRED_DELTAS.csv", paired_rows)
    report = {
        "protocol": PROTOCOL, "verdict": "DRTP_FINAL_EVIDENCE_HELDOUT_OOD_REPORTED",
        "primary_unit": "training_seed", "cohorts_separate_for_inference": True, "pooled_n10_descriptive_only": True,
        "automatic_method_selection": False, "automatic_algorithm_revision": False,
        "interpretation": "This is a complete descriptive held-out/OOD report, not a single-metric hard gate. Claims must jointly consider central tendency, lower tail, paired seed direction and safety.",
    }
    (args.output_root / "DRTP_FINAL_EVIDENCE_HELDOUT_OOD_REPORT.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (args.output_root / "DRTP_FINAL_EVIDENCE_HELDOUT_OOD_REPORT.md").write_text(
        "# DRTP final held-out/OOD report\n\n"
        "**Verdict:** `DRTP_FINAL_EVIDENCE_HELDOUT_OOD_REPORTED`.\n\n"
        "This report does not automatically promote, revise, or close an algorithm. A and B remain separate inference cohorts; any pooled n=10 quantity is descriptive only. "
        "Interpret return, lower-tail, paired direction, collision and timeout jointly.\n",
        encoding="utf-8",
    )
    print(json.dumps({"verdict": report["verdict"], "training_started": False}, indent=2))


if __name__ == "__main__":
    main()
