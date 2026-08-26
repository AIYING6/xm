"""Aggregate REL-A0 raw records with fixed episode/tape coverage checks."""
from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path


TAPES = ("T0", "T1", "T2", "T3", "T4")
METHODS = ("utr_sg", "drtp_sg")
SEEDS = (1901, 1902, 2001, 2002, 2003)
CONDITIONS = ("nominal", "f0", "timing", "duration", "compound")


def mean(rows, key):
    values = [float(r[key]) for r in rows if r.get(key) not in ("", None) and math.isfinite(float(r[key]))]
    return sum(values) / len(values) if values else math.nan


def pct(rows, key):
    return mean(rows, key)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--evaluation-root", type=Path, required=True)
    p.add_argument("--report-path", type=Path, required=True)
    p.add_argument("--decision-json", type=Path, required=True)
    args = p.parse_args()
    raw_path = args.evaluation_root / "raw_episode_metrics.csv"
    rows = list(csv.DictReader(raw_path.open(encoding="utf-8", newline="")))
    expected = len(TAPES) * len(METHODS) * len(SEEDS) * len(CONDITIONS) * 100
    errors = []
    if len(rows) != expected:
        errors.append(f"raw row count {len(rows)} != expected {expected}")
    groups = defaultdict(list)
    for row in rows:
        groups[(row["method"], int(row["training_seed"]), row["tape_label"], row["condition"])].append(row)
    for method in METHODS:
        for seed in SEEDS:
            for tape in TAPES:
                for condition in CONDITIONS:
                    cell = groups[(method, seed, tape, condition)]
                    if len(cell) != 100:
                        errors.append(f"coverage {method}/seed{seed}/{tape}/{condition}: {len(cell)}")
    if errors:
        decision = {"protocol": "DRTP-REL-A0-AGGREGATION-V1", "status": "TECHNICAL_INVALID", "errors": errors}
        args.decision_json.parent.mkdir(parents=True, exist_ok=True)
        args.decision_json.write_text(json.dumps(decision, indent=2) + "\n", encoding="utf-8")
        raise SystemExit("; ".join(errors[:5]))

    cell_summary = []
    for (method, seed, tape, condition), cell in sorted(groups.items()):
        cell_summary.append({"method": method, "training_seed": seed, "tape": tape,
                             "condition": condition, "J": mean(cell, "J"),
                             "collision": pct(cell, "collision"), "timeout": pct(cell, "timeout"),
                             "constraint_violation": pct(cell, "constraint_violation"),
                             "failure_exposure": pct(cell, "failure_exposed"),
                             "pre_trigger_termination": pct(cell, "pre_trigger_termination"),
                             "survived_to_onset": pct(cell, "survived_to_onset"),
                             "path_switch_count": mean(cell, "path_switch_count"),
                             "direct_path_fraction_failure": mean(cell, "direct_path_fraction_failure"),
                             "relay_path_fraction_failure": mean(cell, "relay_path_fraction_failure"),
                             "task_support_fraction_failure": mean(cell, "task_support_fraction_failure"),
                             "legal_information_fraction_failure": mean(cell, "legal_information_fraction_failure"),
                             "mean_cache_age_failure": mean(cell, "mean_cache_age_failure")})
    by_seed_method_condition = defaultdict(list)
    for row in cell_summary:
        by_seed_method_condition[(row["method"], row["training_seed"], row["condition"])].append(row)
    seed_summary = []
    for method in METHODS:
        for seed in SEEDS:
            result = {"method": method, "training_seed": seed}
            for condition in CONDITIONS:
                c = by_seed_method_condition[(method, seed, condition)]
                result[f"J_{condition}"] = mean(c, "J")
                result[f"collision_{condition}"] = mean(c, "collision")
                result[f"timeout_{condition}"] = mean(c, "timeout")
                result[f"constraint_{condition}"] = mean(c, "constraint_violation")
                result[f"exposure_{condition}"] = mean(c, "failure_exposure")
            for condition in CONDITIONS[1:]:
                result[f"delta_{condition}"] = result["J_nominal"] - result[f"J_{condition}"]
            seed_summary.append(result)

    pooled = {}
    for method in METHODS:
        method_rows = [x for x in cell_summary if x["method"] == method]
        pooled[method] = {f"J_{condition}": mean([x for x in method_rows if x["condition"] == condition], "J")
                         for condition in CONDITIONS}
        pooled[method].update({f"collision_{condition}": mean([x for x in method_rows if x["condition"] == condition], "collision")
                               for condition in CONDITIONS})
        pooled[method].update({f"timeout_{condition}": mean([x for x in method_rows if x["condition"] == condition], "timeout")
                               for condition in CONDITIONS})
        pooled[method].update({f"exposure_{condition}": mean([x for x in method_rows if x["condition"] == condition], "failure_exposure")
                               for condition in CONDITIONS})
        for condition in CONDITIONS[1:]:
            pooled[method][f"delta_{condition}"] = pooled[method]["J_nominal"] - pooled[method][f"J_{condition}"]

    effects = {}
    for condition in CONDITIONS:
        diffs = [next(x for x in seed_summary if x["method"] == "drtp_sg" and x["training_seed"] == seed)[f"J_{condition}"]
                 - next(x for x in seed_summary if x["method"] == "utr_sg" and x["training_seed"] == seed)[f"J_{condition}"]
                 for seed in SEEDS]
        effects[condition] = {"paired_seed_differences_drtp_minus_utr": diffs,
                              "mean": statistics.mean(diffs), "median": statistics.median(diffs),
                              "wins": sum(x > 0 for x in diffs), "worst": min(diffs)}

    decision = {"protocol": "DRTP-REL-A0-AGGREGATION-V1", "status": "completed",
                "training_started": False, "technical_validity": "PASS",
                "raw_rows": len(rows), "expected_rows": expected,
                "pooled": pooled, "effects": effects,
                "seed_summary": seed_summary, "cell_summary": cell_summary,
                "stop_after_report": True}
    args.decision_json.parent.mkdir(parents=True, exist_ok=True)
    args.decision_json.write_text(json.dumps(decision, indent=2, allow_nan=True) + "\n", encoding="utf-8")
    lines = ["# DRTP REL-A0 — Multi-Tape Reliability Audit Report", "",
             "- Protocol: `DRTP-REL-A0-AGGREGATION-V1`", "- Training started: **NO**",
             f"- Raw records: **{len(rows):,}/{expected:,}**", "- Technical coverage: **PASS**", "",
             "## Paired UTR/DRTP absolute performance", "",
             "The following are pooled descriptive means across tapes and episodes; training seed remains the independent unit.", "",
             "| condition | UTR J | DRTP J | DRTP−UTR mean | median | wins/5 | worst |"]
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for condition in CONDITIONS:
        e = effects[condition]
        lines.append(f"| {condition} | {pooled['utr_sg'][f'J_{condition}']:.4f} | {pooled['drtp_sg'][f'J_{condition}']:.4f} | "
                     f"{e['mean']:.4f} | {e['median']:.4f} | {e['wins']}/5 | {e['worst']:.4f} |")
    lines += ["", "## Seed-level table", "", "| method | seed | J_nominal | J_f0 | J_timing | J_duration | J_compound |", "|---|---:|---:|---:|---:|---:|---:|"]
    for row in seed_summary:
        lines.append(f"| {row['method']} | {row['training_seed']} | {row['J_nominal']:.4f} | {row['J_f0']:.4f} | {row['J_timing']:.4f} | {row['J_duration']:.4f} | {row['J_compound']:.4f} |")
    lines += ["", "## Interpretation boundary", "",
              "This audit reports cross-tape reliability and paired effects. It does not rewrite historical NO-GO/TECHNICAL_INVALID conclusions, "
              "does not establish universal DRTP superiority, and does not authorize new training. Weak or reversed seeds remain included.", "",
              "## Stop rule", "", "REL-A0 ends after this report. Any subsequent training or algorithm decision requires separate authorization.", ""]
    args.report_path.parent.mkdir(parents=True, exist_ok=True)
    args.report_path.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"status": "completed", "raw_rows": len(rows), "decision": str(args.decision_json)}))


if __name__ == "__main__":
    main()
