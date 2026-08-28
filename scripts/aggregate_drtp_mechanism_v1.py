"""Conservative zero-inference aggregation for Mechanism V1 evidence."""
from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "diagnostics/drtp_mechanism_v1/08_report"
ARMS = ("utr_sg", "drtp_sg")
SEEDS = (2601, 2602, 2603)


def mean(rows, key: str) -> float:
    values = []
    for row in rows:
        try:
            value = float(row[key])
        except (KeyError, TypeError, ValueError):
            continue
        if math.isfinite(value):
            values.append(value)
    return sum(values) / len(values) if values else math.nan


def read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("NO-GO: --execute is required")
    eval_root = args.output_root / "evaluations" / "final_1m"
    manifest = json.loads((eval_root / "evaluation_manifest.json").read_text(encoding="utf-8"))
    rows = read_csv(eval_root / "raw_episode_metrics.csv")
    grouped = defaultdict(list)
    for row in rows:
        grouped[(row["method"], int(row["train_seed"]), row["topology_condition"])].append(row)
    seed_rows = []
    for arm in ARMS:
        for seed in SEEDS:
            condition_rows = [row for key, values in grouped.items() if key[0] == arm and key[1] == seed for row in values]
            seed_rows.append({
                "method": arm, "seed": seed,
                "J_nominal": mean(grouped[(arm, seed, "nominal")], "J"),
                "J_F0": mean(grouped[(arm, seed, "F0")], "J"),
                "J_T28": mean(grouped[(arm, seed, "T28")], "J"),
                "J_D120": mean(grouped[(arm, seed, "D120")], "J"),
                "J_C28_120": mean(grouped[(arm, seed, "C28-120")], "J"),
                "collision": mean(condition_rows, "collision"),
                "timeout": mean(condition_rows, "timeout"),
                "constraint_violation": mean(condition_rows, "constraint_violation"),
                "failure_exposure": mean(condition_rows, "failure_exposed"),
            })
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "seed_level_summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(seed_rows[0])); writer.writeheader(); writer.writerows(seed_rows)

    telemetry_rows = []
    for arm in ARMS:
        for seed in SEEDS:
            summary_path = args.output_root / "runs" / arm / f"seed{seed}" / "failure_telemetry" / "episode_summary.jsonl"
            window_path = summary_path.with_name("failure_event_window.jsonl")
            summaries = [json.loads(line) for line in summary_path.read_text(encoding="utf-8").splitlines()] if summary_path.exists() else []
            windows = [json.loads(line) for line in window_path.read_text(encoding="utf-8").splitlines()] if window_path.exists() else []
            for tau in range(-20, 61):
                tau_rows = [row for row in windows if row.get("failure_relative_time") == tau]
                telemetry_rows.append({
                    "method": arm, "seed": seed, "tau": tau,
                    "window_records": len(tau_rows), "summary_records": len(summaries),
                    "failure_active_rate": mean(tau_rows, "failure_active"),
                    "task_support_rate": mean(tau_rows, "task_support_state"),
                    "direct_path_rate": mean(tau_rows, "direct_information_path"),
                    "relay_path_rate": mean(tau_rows, "relay_information_path"),
                })
    with (OUT / "divergence_timeline.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(telemetry_rows[0]) if telemetry_rows else ["method", "seed", "tau"])
        writer.writeheader(); writer.writerows(telemetry_rows)

    matrix = [
        {"layer": "sampler", "evidence": "drtp_topology_sampler_log.csv", "status": "available", "interpretation": "descriptive only"},
        {"layer": "exposure", "evidence": "failure_telemetry/episode_summary.jsonl", "status": "available", "interpretation": "descriptive only"},
        {"layer": "behavior", "evidence": "failure_telemetry/failure_event_window.jsonl", "status": "available", "interpretation": "requires UTR-controlled comparison"},
        {"layer": "outcome", "evidence": "evaluations/final_1m/raw_episode_metrics.csv", "status": "available", "interpretation": "final checkpoint only"},
    ]
    with (OUT / "mechanism_evidence_matrix.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(matrix[0])); writer.writeheader(); writer.writerows(matrix)
    (OUT / "go_no_go.md").write_text(
        "# Mechanism V1 decision\n\n"
        "`PENDING_REVIEW`\n\n"
        "The data products are complete only when all six training manifests and the fixed evaluation manifest pass integrity checks. "
        "A mechanism is not declared from correlation alone; P9 requires time-leading, DRTP-specific, UTR-controlled evidence across three contiguous layers.\n",
        encoding="utf-8")
    (OUT / "mechanism_experiment_report.md").write_text(
        "# DRTP Training-Failure Mechanism Experiment V1\n\n"
        "This report is generated from the six exploratory paired trajectories and the independent development-only tape. "
        "It retains every seed and every episode; it does not promote checkpoints or infer a mechanism from pooled correlation.\n\n"
        f"Evaluation rows: {manifest.get('raw_rows')}\n\n"
        "The final Mechanism GO/NO-GO remains governed by the frozen P9 rule.\n",
        encoding="utf-8")
    (OUT / "missing_evidence.md").write_text(
        "# Missing evidence\n\n"
        "No evidence is treated as a proven mechanism unless the P9 time-leading, repetition, UTR-control and three-layer conditions are explicitly demonstrated.\n",
        encoding="utf-8")
    (OUT / "proposed_intervention.md").write_text(
        "# Proposed intervention\n\n"
        "No algorithm modification is scientifically authorized unless Mechanism V1 receives a valid Mechanism GO.\n",
        encoding="utf-8")


if __name__ == "__main__":
    main()
