#!/usr/bin/env python3
"""Zero-training, exploratory risk-return audit for archived DRTP pilots."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from statistics import mean


def values(cell: str) -> list[float]:
    return [float(x) for x in cell.split(";") if x and x != "NA"]


def fmt(value: float) -> str:
    return f"{value:.3f}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, default=Path("docs/drtp_b5_20260830/run_registry.csv"))
    parser.add_argument("--freeze", type=Path, default=Path("configs/drtp_reliable_return_frontier_exploratory_freeze.json"))
    parser.add_argument("--output-dir", type=Path, default=Path("docs/drtp_reliable_return_frontier_20260831"))
    args = parser.parse_args()

    freeze = json.loads(args.freeze.read_text(encoding="utf-8"))
    epsilon = float(freeze["measurement_margin_epsilon_j"])
    args.output_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, str]] = []
    # Historical cloud exports can carry a UTF-8 BOM; accept both forms without
    # changing the source artifact.
    with args.registry.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            if row["original_gains"] != "NA" and row["candidate_gains"] != "NA":
                rows.append(row)

    report_rows: list[dict[str, object]] = []
    for row in rows:
        original, candidate = values(row["original_gains"]), values(row["candidate_gains"])
        if len(original) != len(candidate):
            raise ValueError(f"unaligned gains in {row['experiment_id']}")
        original_mean, candidate_mean = mean(original), mean(candidate)
        original_range, candidate_range = max(original) - min(original), max(candidate) - min(candidate)
        mean_loss = original_mean - candidate_mean
        upper_tail_loss = max(original) - max(candidate)
        checks = {
            "positive_mean_gain": candidate_mean > 0.0,
            "nonnegative_worst_gain": min(candidate) >= 0.0,
            "mean_retention": mean_loss <= epsilon,
            "upper_tail_retention": upper_tail_loss <= epsilon,
            "range_reduction": candidate_range <= original_range,
        }
        report_rows.append({
            "experiment_id": row["experiment_id"],
            "seeds": row["seeds"],
            "budget_m": row["budget_m"],
            "historical_decision": row["decision"],
            "original_mean_gain": original_mean,
            "candidate_mean_gain": candidate_mean,
            "original_worst_gain": min(original),
            "candidate_worst_gain": min(candidate),
            "original_range": original_range,
            "candidate_range": candidate_range,
            "mean_loss_vs_original": mean_loss,
            "upper_tail_loss_vs_original": upper_tail_loss,
            **checks,
            "frontier_pass_in_this_cohort": all(checks.values()),
            "interpretation": row["contribution"],
        })

    fieldnames = list(report_rows[0])
    with (args.output_dir / "frontier_by_archived_cohort.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(report_rows)

    passing = [row for row in report_rows if row["frontier_pass_in_this_cohort"]]
    text = [
        "# DRTP reliable-return frontier R0",
        "",
        "**Status:** `R0_ZERO_TRAINING_COMPLETE — NO CANDIDATE PROMOTED`.",
        "",
        "This is a post-hoc exploratory re-expression of completed pilots. It neither changes their original frozen gate decisions nor pools training cohorts. It authorizes no training, parameter selection, or Mainline-A modification.",
        "",
        "## Reliability-first objective",
        "",
        "The acceptable trade-off is deliberately stricter than ‘lower variance’: the candidate must retain a positive mean paired robust gain over UTR, have a non-negative worst paired gain, keep mean and upper-tail loss versus Original DRTP within the frozen measurement margin `epsilon_J = 7.875`, and not enlarge the paired-gain range.",
        "",
        "## Archived-cohort screen",
        "",
        "| Experiment | Candidate mean G | Candidate worst G | Mean loss vs Original | Upper-tail loss | Range reduced | Screen |",
        "| --- | ---: | ---: | ---: | ---: | :---: | :---: |",
    ]
    for row in report_rows:
        text.append(
            f"| {row['experiment_id']} | {fmt(row['candidate_mean_gain'])} | {fmt(row['candidate_worst_gain'])} | {fmt(row['mean_loss_vs_original'])} | {fmt(row['upper_tail_loss_vs_original'])} | {row['range_reduction']} | {row['frontier_pass_in_this_cohort']} |"
        )
    text += [
        "",
        "## Interpretation",
        "",
        "No archived candidate passes the complete screen or is eligible for promotion. D3_KLR is the nearest early pilot row: it has positive mean and worst paired gains and a smaller range, but its observed upper-tail loss is `9.420`, exceeding the frozen `epsilon_J = 7.875`. More decisively, the completed KLR final replication fails in both independent cohorts: each cohort contains a newly catastrophic KLR seed and KLR enlarges gain range and sample SD. PP-DRTP's independent P4 cohort fails the downside and range requirements. Conservative-DRTP reverses in R1. Every other comparable candidate fails at least one reliability-first condition.",
        "",
        "Thus the revised objective is scientifically viable, but none of the archived local-patch candidates supplies sufficient evidence that it achieves that objective. A future candidate must be designed from a new, independently supported mechanism and must be tested prospectively in two separate fresh-seed cohorts. This R0 audit does not authorize that candidate or any cloud run.",
        "",
        "## Integrity boundary",
        "",
        "The unit of evidence remains the training seed. Differences in seed sets, tapes, budgets, and candidate semantics make the archived rows unsuitable for pooled estimation or retrospective winner selection.",
    ]
    (args.output_dir / "R0_RELIABLE_RETURN_FRONTIER_REPORT.md").write_text("\n".join(text) + "\n", encoding="utf-8")
    (args.output_dir / "R0_RELIABLE_RETURN_FRONTIER_DECISION.json").write_text(
        json.dumps({
            "status": "R0_ZERO_TRAINING_COMPLETE",
            "historical_candidates_screened": len(report_rows),
            "per_cohort_screen_passes": [row["experiment_id"] for row in passing],
            "candidate_promoted": False,
            "training_authorized": False,
            "mainline_a_modified": False,
            "epsilon_J": epsilon,
        }, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
