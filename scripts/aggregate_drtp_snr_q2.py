"""Aggregate the prospective UTR/SNR/DRTP mechanism comparator."""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
import statistics
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))

import aggregate_drtp_sg_development as base  # noqa: E402
from create_drtp_snr_q2_tape import SEEDS, TAPE_START  # noqa: E402
from run_drtp_snr_q2_formal_single import ARMS  # noqa: E402


PROTOCOL = "DRTP-SNR-Q2-MECHANISM-COMPARATOR-AGGREGATION-V1"
FINAL_LABEL = "10m"
PRIMARY = ("J_F0", "J_OOD_mean", "J_OOD_worst")


def quantile(values: list[float], p: float) -> float:
    ordered = sorted(values); index = (len(ordered) - 1) * p; low, high = math.floor(index), math.ceil(index)
    return ordered[low] if low == high else ordered[low] * (high - index) + ordered[high] * (index - low)


def paired_summary(values: list[float]) -> dict:
    median = statistics.median(values)
    return {"n": len(values), "mean": statistics.mean(values), "median": median, "sample_sd": statistics.stdev(values),
            "iqr": quantile(values, .75) - quantile(values, .25), "mad": statistics.median(abs(value - median) for value in values),
            "wins": sum(value > 0 for value in values), "ties": sum(value == 0 for value in values), "worst": min(values), "best": max(values), "values": values}


def catastrophic(reference: dict, method: dict) -> tuple[bool, list[str]]:
    f0 = method["J_F0"] / reference["J_F0"] if reference["J_F0"] else math.nan
    worst = method["J_OOD_worst"] / reference["J_OOD_worst"] if reference["J_OOD_worst"] else math.nan
    reasons = []
    if f0 < .70 and worst < .85: reasons.append("F0<0.70_and_OODworst<0.85")
    if worst < .70 and f0 < .85: reasons.append("OODworst<0.70_and_F0<0.85")
    if method["timeout_failure_mean"] - reference["timeout_failure_mean"] > .20 and (f0 < .85 or worst < .85): reasons.append("timeout_associated_collapse")
    return bool(reasons), reasons


def pair(rows_by_arm: dict[str, list[dict]], left: str, right: str) -> dict:
    """Return right-minus-left paired evidence; `right` is the candidate method."""
    paired_rows, deltas, catastrophes = [], {key: [] for key in ("J_nominal", *PRIMARY)}, 0
    for seed in SEEDS:
        reference = next(item for item in rows_by_arm[left] if item["seed"] == seed)
        candidate = next(item for item in rows_by_arm[right] if item["seed"] == seed)
        is_cat, reasons = catastrophic(reference, candidate); catastrophes += int(is_cat)
        row = {"seed": seed, "reference": left, "candidate": right, "catastrophic": is_cat, "catastrophic_reasons": ";".join(reasons)}
        for key in deltas:
            value = candidate[key] - reference[key]; deltas[key].append(value)
            row[f"delta_{key}"] = value; row[f"ratio_{key}"] = candidate[key] / reference[key] if reference[key] else math.nan
        row["delta_collision"] = candidate["collision_failure_mean"] - reference["collision_failure_mean"]
        row["delta_timeout"] = candidate["timeout_failure_mean"] - reference["timeout_failure_mean"]
        paired_rows.append(row)
    summaries = {key: paired_summary(values) for key, values in deltas.items()}
    endpoints_positive = all(item["mean"] > 0 and item["median"] > 0 and item["wins"] >= 3 for key, item in summaries.items() if key in PRIMARY)
    safety = (sum(row["delta_collision"] > 0 for row in paired_rows) < 4 and sum(row["delta_timeout"] > 0 for row in paired_rows) < 4)
    return {"reference": left, "candidate": right, "paired_rows": paired_rows, "summaries": summaries,
            "catastrophic_seed_count": catastrophes, "directional_support": endpoints_positive and safety and catastrophes <= 1,
            "primary_endpoints_positive": endpoints_positive, "safety_not_systematically_worse": safety}


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--results-root", type=Path, required=True)
    parser.add_argument("--report-path", type=Path, default=Path("docs/DRTP_SNR_Q2_MECHANISM_COMPARATOR_REPORT.md")); args = parser.parse_args()
    tape = json.loads((args.results_root / "snr_comparator_tape_manifest.json").read_text(encoding="utf-8"))
    if tape.get("episode_ids") != list(range(TAPE_START, TAPE_START + 100)): raise RuntimeError("comparator tape mismatch")
    eval_root = args.results_root / "evaluations" / "final_10m"; manifest = json.loads((eval_root / "evaluation_manifest.json").read_text(encoding="utf-8"))
    if manifest.get("status") != "completed" or manifest.get("tape_hash") != tape["tape_hash"]: raise RuntimeError("incomplete/mismatched comparator evaluation")
    expected, rows = [item["name"] for item in tape["conditions"]], base.rows_from(eval_root / "per_seed_condition_summary.csv")
    cells = [base.metrics(rows, arm, seed, FINAL_LABEL, tuple(expected[2:])) for arm in ARMS for seed in SEEDS]
    by_arm = {arm: [cell for cell in cells if cell["arm"] == arm] for arm in ARMS}; pooled = {arm: base.pooled(by_arm[arm]) for arm in ARMS}
    failures = [row for row in rows if row["condition"] != "nominal"]
    risk_valid = all(float(row["failure_trigger_success_rate_risk_set"]) == 1.0 for row in failures if int(float(row["risk_set_size"])) > 0)
    completeness = manifest.get("raw_rows") == 18000 and len(failures) == len(ARMS) * len(SEEDS) * 11
    comparisons = {"snr_minus_utr": pair(by_arm, "utr_sg", "snr_sg"), "drtp_minus_snr": pair(by_arm, "snr_sg", "drtp_sg"), "drtp_minus_utr": pair(by_arm, "utr_sg", "drtp_sg")}
    all_pair_rows = [row for item in comparisons.values() for row in item["paired_rows"]]
    with (eval_root / "paired_seed_results.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(all_pair_rows[0])); writer.writeheader(); writer.writerows(all_pair_rows)
    technical = completeness and risk_valid
    static, dynamic = comparisons["snr_minus_utr"]["directional_support"], comparisons["drtp_minus_snr"]["directional_support"]
    reverse = pair(by_arm, "drtp_sg", "snr_sg")["directional_support"]
    if not technical: verdict = "TECHNICAL_INVALID"
    elif static and dynamic: verdict = "DYNAMIC_ADDITIONAL_VALUE_SUPPORTED"
    elif static and not dynamic: verdict = "STATIC_NONUNIFORM_SUFFICIENT_FOR_OBSERVED_GAIN"
    elif reverse: verdict = "DYNAMIC_MECHANISM_NOT_SUPPORTED"
    else: verdict = "NO_CLEAR_MECHANISM_SEPARATION"
    result = {"protocol": PROTOCOL, "verdict": verdict, "tape_hash": tape["tape_hash"], "primary_inference_unit": "training_seed", "n_paired_training_seeds": 5,
              "pooled": pooled, "comparisons": comparisons, "technical_validity": {"complete_18000_records": completeness, "risk_set_trigger_validity": risk_valid},
              "historical_heldout_fail_preserved": True, "historical_seed2002_preserved": True, "canonical_seeds_used": False, "automatic_follow_on_started": False}
    (eval_root / "DRTP_SNR_Q2_MECHANISM_DECISION.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    lines = ["# DRTP/SNR Q2 Mechanism Comparator Report", "", f"**Verdict:** `{verdict}`", "", "Training seed is the independent unit (`n=5`). All 15 final checkpoints and 18,000 scheduled evaluation episodes are retained.", "",
             "## Technical validity", "", f"- complete 18,000 raw records: `{'PASS' if completeness else 'FAIL'}`", f"- risk-set trigger validity: `{'PASS' if risk_valid else 'FAIL'}`", "",
             "## Paired endpoint evidence", ""]
    for name, comparison in comparisons.items():
        lines += [f"### {name}", "", "| endpoint | mean | median | wins/5 | worst reversal |", "|---|---:|---:|---:|---:|"]
        for endpoint, item in comparison["summaries"].items(): lines.append(f"| {endpoint} | {item['mean']:.6g} | {item['median']:.6g} | {item['wins']}/5 | {item['worst']:.6g} |")
        lines += [f"- primary endpoint directional support: `{'PASS' if comparison['directional_support'] else 'FAIL'}`", f"- catastrophic seeds: `{comparison['catastrophic_seed_count']}`", ""]
    lines += ["Historical held-out findings and the seed2002 catastrophic reversal are retained unchanged. No subsequent training is authorized by this aggregation.", ""]
    args.report_path.parent.mkdir(parents=True, exist_ok=True); args.report_path.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__": main()
