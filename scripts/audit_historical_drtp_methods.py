"""Generate a read-only performance/reliability re-audit of frozen DRTP studies.

The script intentionally reads a committed registry of matched historical effects.  It
does not load models, launch environments, evaluate checkpoints, or edit results.
"""
from __future__ import annotations

import argparse
import csv
import json
import statistics
from pathlib import Path


def performance_verdict(summary: dict[str, float], n: int) -> str:
    mean = summary["mean_effect"]
    median = summary["median_effect"]
    wins = summary["positive_units"]
    if mean > 0 and median > 0 and wins > n / 2:
        return "PERFORMANCE_SUCCESS"
    if mean <= 0 and median <= 0:
        return "NO_CLEAR_PERFORMANCE_VALUE"
    return "PERFORMANCE_MIXED"


def reliability_verdict(hint: str) -> str:
    return {
        "MIXED": "RELIABILITY_MIXED",
        "NOT_IMPROVED": "RELIABILITY_NOT_IMPROVED",
        "IMPROVED": "RELIABILITY_IMPROVED",
    }[hint]


def method_rollup(records: list[dict]) -> tuple[str, str]:
    performance = [record["performance_verdict"] for record in records]
    reliability = [record["reliability_verdict"] for record in records]
    if len(set(performance)) > 1 or "PERFORMANCE_MIXED" in performance:
        perf = "PERFORMANCE_MIXED"
    elif "NO_CLEAR_PERFORMANCE_VALUE" in performance:
        perf = "NO_CLEAR_PERFORMANCE_VALUE"
    else:
        perf = "PERFORMANCE_SUCCESS"
    rel = "RELIABILITY_NOT_IMPROVED" if "RELIABILITY_NOT_IMPROVED" in reliability else "RELIABILITY_MIXED"
    return perf, rel


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, default=Path("configs/historical_method_reaudit_20260902.json"))
    parser.add_argument("--output-dir", type=Path, default=Path("docs/historical_method_reaudit_20260902"))
    args = parser.parse_args()
    registry = json.loads(args.registry.read_text(encoding="utf-8"))
    output = args.output_dir
    output.mkdir(parents=True, exist_ok=True)

    rows: list[dict] = []
    for record in registry["records"]:
        effects = record.get("effects")
        row = dict(record)
        if effects is None:
            summary = dict(record["summary"])
        else:
            summary = {
                "mean_effect": statistics.fmean(effects),
                "median_effect": statistics.median(effects),
                "positive_units": sum(value > 0 for value in effects),
                "nonnegative_units": sum(value >= 0 for value in effects),
                "minimum_effect": min(effects),
                "maximum_effect": max(effects),
            }
        row.update(summary)
        row.update(
            performance_verdict=performance_verdict(summary, record["n"]),
            reliability_verdict=reliability_verdict(record["reliability_hint"]),
        )
        rows.append(row)

    performance_fields = [
        "method", "variant", "cohort", "role", "budget_million_env_steps", "unit", "n", "comparator",
        "mean_effect", "median_effect", "positive_units", "minimum_effect", "maximum_effect",
        "performance_verdict", "historical_status", "evidence",
    ]
    reliability_fields = [
        "method", "variant", "cohort", "role", "n", "comparator", "reliability_verdict",
        "reliability_observation", "historical_status", "evidence",
    ]
    write_csv(output / "HISTORICAL_METHOD_PERFORMANCE_MATRIX.csv", rows, performance_fields)
    write_csv(output / "HISTORICAL_METHOD_RELIABILITY_MATRIX.csv", rows, reliability_fields)

    by_method: dict[str, list[dict]] = {}
    for row in rows:
        by_method.setdefault(row["method"], []).append(row)
    rollups = {method: method_rollup(method_rows) for method, method_rows in by_method.items()}

    contract = f"""# Historical DRTP method re-audit contract

Protocol: `{registry['protocol']}`  
Date: `{registry['date']}`

## Scope and non-interference

{registry['scope']}

## Comparability unit

Every matrix row is one matched cohort. Its independent unit is the recorded `unit`, never an evaluation episode. Cohorts are never pooled for inference. A method is compared only with its stated frozen comparator, budget, and tape context; results across incompatible arms or horizons are not aggregated.

## Reclassification rules

Primary endpoint: {registry['primary_endpoint']}.

- `PERFORMANCE_SUCCESS`: {registry['performance_rule']['success']}.
- `PERFORMANCE_MIXED`: {registry['performance_rule']['mixed']}.
- `NO_CLEAR_PERFORMANCE_VALUE`: {registry['performance_rule']['no_clear']}.
- `RELIABILITY_IMPROVED`: {registry['reliability_rule']['improved']}.
- `RELIABILITY_MIXED`: {registry['reliability_rule']['mixed']}.
- `RELIABILITY_NOT_IMPROVED`: {registry['reliability_rule']['not_improved']}.

`STABILITY_SOLVED` is deliberately not assigned in this audit: no candidate simultaneously met the required fresh-cohort and comparable-horizon reliability standard. Historical gate decisions are preserved verbatim and are not overwritten by this secondary classification.
"""
    (output / "HISTORICAL_METHOD_REAUDIT_CONTRACT.md").write_text(contract, encoding="utf-8")

    cohort_lines = [
        "# Cohort-separated historical analysis", "",
        "The table below is deliberately row-level: a positive development cohort does not cancel an adverse independent cohort.", "",
        "| Method | Cohort | Comparator | Mean effect | Median effect | Wins | Performance | Reliability | Historical status |",
        "| --- | --- | --- | ---: | ---: | ---: | --- | --- | --- |",
    ]
    for row in rows:
        cohort_lines.append(
            f"| {row['method']} | {row['cohort']} | {row['comparator']} | {row['mean_effect']:.3f} | "
            f"{row['median_effect']:.3f} | {row['positive_units']}/{row['n']} | {row['performance_verdict']} | "
            f"{row['reliability_verdict']} | {row['historical_status']} |"
        )
    (output / "HISTORICAL_METHOD_COHORT_ANALYSIS.md").write_text("\n".join(cohort_lines) + "\n", encoding="utf-8")

    reclassification = [
        "# Historical-method reclassification", "",
        "## Method-level view", "",
        "| Method | Cross-cohort performance classification | Reliability classification | Interpretation |",
        "| --- | --- | --- | --- |",
    ]
    descriptions = {
        "Original DRTP": "Formal 10M evidence is performance-positive; independent matched evidence reverses direction, so the publishable claim is bounded performance upside rather than universal reliability.",
        "S1 TR": "A local performance-positive signal did not protect lower-tail reliability.",
        "S2 Conservative": "The strongest local sampler-stabilization signal; it remains development-only and its predeclared reliability gate did not pass.",
        "Conservative-DRTP R1": "Independent replication reversed the local conservative result.",
        "KLR": "A promising pilot did not survive final two-cohort replication.",
        "KLB": "No matched performance value was retained.",
        "PP-DRTP": "The local rescue signal reversed in independent validation.",
        "CV-DRTP": "Both validation cohorts were adverse relative to Original DRTP.",
        "Reliable-DRTP ensemble": "A positive cohort-A mean did not persist in cohort B and did not protect against catastrophic bundles.",
        "Group-weighted PPO": "The same-rollout local mechanism did not accumulate into reliable fresh-seed policy performance.",
    }
    for method, (perf, rel) in rollups.items():
        reclassification.append(f"| {method} | {perf} | {rel} | {descriptions[method]} |")
    reclassification += [
        "", "## No empirical policy-performance classification", "",
        "| Method | Historical status | Reclassification | Reason |",
        "| --- | --- | --- | --- |",
    ]
    for item in registry["non_empirical_methods"]:
        reclassification.append(
            f"| {item['method']} | {item['historical_status']} | NO_EMPIRICAL_PERFORMANCE_EVIDENCE | {item['reason']} |"
        )
    (output / "HISTORICAL_METHOD_RECLASSIFICATION.md").write_text("\n".join(reclassification) + "\n", encoding="utf-8")

    paper = """# Paper-value assessment

## Direct answers

1. **Original DRTP:** it has strong matched 10M formal performance evidence, especially on the frozen fault/OOD endpoints. The independent cohort reverses that direction, so the defensible paper claim is *substantial robustness upside under the formal protocol*, with a clearly bounded reliability claim—not universal cross-seed superiority.
2. **Historical NO-GO methods with performance value:** S1 TR, S2 Conservative, the initial KLR pilot, the PP-DRTP P3 pilot, and ensemble cohort A had positive matched cohort-level performance signals. They are not replacement algorithms because none replicated its reliability claim across independent cohorts.
3. **Better than Original DRTP:** S2 was superior on mean, median, and all three matched development seeds; the KLR and PP pilots were superior on mean, median, and a majority/all local units. No candidate retained that relation in the required independent evidence. These are bounded local findings, not grounds to replace Original DRTP.
4. **Best use of remaining effort:** for the A-line manuscript, evidence-boundary clarity and reproducibility are more valuable than reopening a stability algorithm line. The historical record supports a compact reliability stress-test supplement, not a claim that stability has been solved.

## Placement recommendation

- **Main text:** Original DRTP's formal matched 10M robustness evidence, method, and clearly defined application target.
- **Supplementary reliability section:** cohort sensitivity of Original DRTP; a compact table of representative stabilization outcomes (S2, KLR final, PP P3/P4, CV, and group-weighted PPO) to establish that no unreplicated patch is presented as a solution.
- **Archive only:** S1 mechanics, KLB, PR feasibility, selective-KLR/SR shadow audits, and detailed per-event diagnostics. These support reproducibility and future work but dilute the main paper if foregrounded.

This document is a reporting plan, not a manuscript edit. It neither changes the A-line paper nor alters any historical gate.
"""
    (output / "PAPER_VALUE_ASSESSMENT.md").write_text(paper, encoding="utf-8")

    final = {
        "protocol": registry["protocol"],
        "mode": "read_only",
        "training_started": False,
        "evaluation_started": False,
        "a_line_modified": False,
        "records": [
            {key: row[key] for key in ("method", "cohort", "performance_verdict", "reliability_verdict", "historical_status")}
            for row in rows
        ],
        "method_rollups": {
            method: {"performance": perf, "reliability": rel} for method, (perf, rel) in rollups.items()
        },
        "non_empirical_methods": registry["non_empirical_methods"],
        "stability_solved_methods": [],
        "automatic_continuation_authorized": False,
    }
    (output / "HISTORICAL_METHOD_REAUDIT.json").write_text(json.dumps(final, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "HISTORICAL_METHOD_REAUDIT_COMPLETE", "output_dir": str(output)}, indent=2))


if __name__ == "__main__":
    main()
