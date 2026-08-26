"""Aggregate the prospective paired five-seed formal confirmation."""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
import statistics
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import aggregate_drtp_sg_development as base  # noqa: E402
from create_drtp_utr_q2_formal_tape import SEEDS, TAPE_START  # noqa: E402
from run_drtp_utr_q2_formal_single import ARMS  # noqa: E402


PROTOCOL = "DRTP-UTR-Q2-FORMAL-PAIRED-5SEED-AGGREGATION-V1"
FINAL_LABEL = "10m"
PRIMARY = ("J_F0", "J_OOD_mean", "J_OOD_worst")


def quantile(values: list[float], p: float) -> float:
    ordered = sorted(values)
    index = (len(ordered) - 1) * p
    low, high = math.floor(index), math.ceil(index)
    if low == high:
        return ordered[low]
    return ordered[low] * (high - index) + ordered[high] * (index - low)


def paired_summary(values: list[float]) -> dict:
    median = statistics.median(values)
    return {
        "n": len(values), "mean": statistics.mean(values), "median": median,
        "sample_sd": statistics.stdev(values),
        "iqr": quantile(values, .75) - quantile(values, .25),
        "mad": statistics.median([abs(value - median) for value in values]),
        "wins": sum(value > 0 for value in values), "ties": sum(value == 0 for value in values),
        "worst": min(values), "best": max(values), "values": values,
    }


def catastrophic(utr: dict, drtp: dict) -> tuple[bool, list[str]]:
    f0 = drtp["J_F0"] / utr["J_F0"] if utr["J_F0"] else math.nan
    worst = drtp["J_OOD_worst"] / utr["J_OOD_worst"] if utr["J_OOD_worst"] else math.nan
    reasons = []
    if f0 < .70 and worst < .85:
        reasons.append("F0<0.70_and_OODworst<0.85")
    if worst < .70 and f0 < .85:
        reasons.append("OODworst<0.70_and_F0<0.85")
    if drtp["timeout_failure_mean"] - utr["timeout_failure_mean"] > .20 and (f0 < .85 or worst < .85):
        reasons.append("timeout_associated_collapse")
    return bool(reasons), reasons


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-root", type=Path, required=True)
    parser.add_argument("--report-path", type=Path,
                        default=Path("docs/DRTP_UTR_Q2_FORMAL_FIVE_SEED_CONFIRMATION_REPORT.md"))
    args = parser.parse_args()
    tape = json.loads((args.results_root / "formal_tape_manifest.json").read_text(encoding="utf-8"))
    if tape.get("episode_ids") != list(range(TAPE_START, TAPE_START + 100)):
        raise RuntimeError("formal tape mismatch")
    expected = [item["name"] for item in tape["conditions"]]
    eval_root = args.results_root / "evaluations" / "final_10m"
    manifest = json.loads((eval_root / "evaluation_manifest.json").read_text(encoding="utf-8"))
    if manifest.get("status") != "completed" or manifest.get("tape_hash") != tape["tape_hash"]:
        raise RuntimeError("incomplete or mismatched formal evaluation")
    rows = base.rows_from(eval_root / "per_seed_condition_summary.csv")
    ood = tuple(expected[2:])
    cells = [base.metrics(rows, arm, seed, FINAL_LABEL, ood) for arm in ARMS for seed in SEEDS]
    by_arm = {arm: [cell for cell in cells if cell["arm"] == arm] for arm in ARMS}
    pooled = {arm: base.pooled(by_arm[arm]) for arm in ARMS}
    paired_rows, deltas = [], {key: [] for key in ("J_nominal", *PRIMARY)}
    catastrophe_count = 0
    for seed in SEEDS:
        utr = next(cell for cell in by_arm["utr_sg"] if cell["seed"] == seed)
        drtp = next(cell for cell in by_arm["drtp_sg"] if cell["seed"] == seed)
        is_catastrophic, reasons = catastrophic(utr, drtp)
        catastrophe_count += int(is_catastrophic)
        row = {"seed": seed, "catastrophic": is_catastrophic,
               "catastrophic_reasons": ";".join(reasons)}
        for key in deltas:
            value = drtp[key] - utr[key]
            deltas[key].append(value)
            row[f"delta_{key}"] = value
            row[f"ratio_{key}"] = drtp[key] / utr[key] if utr[key] else math.nan
        row["delta_collision"] = drtp["collision_failure_mean"] - utr["collision_failure_mean"]
        row["delta_timeout"] = drtp["timeout_failure_mean"] - utr["timeout_failure_mean"]
        paired_rows.append(row)
    with (eval_root / "paired_seed_results.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(paired_rows[0]))
        writer.writeheader(); writer.writerows(paired_rows)
    summaries = {key: paired_summary(values) for key, values in deltas.items()}

    failure_rows = [row for row in rows if row["condition"] != "nominal"]
    risk_valid = all(float(row["failure_trigger_success_rate_risk_set"]) == 1.0
                     for row in failure_rows if int(float(row["risk_set_size"])) > 0)
    full_rows = len(failure_rows) == len(ARMS) * len(SEEDS) * 11
    p_utr, p_drtp = pooled["utr_sg"], pooled["drtp_sg"]
    return_pass = all(summaries[key]["mean"] > 0 and summaries[key]["median"] > 0
                      and summaries[key]["wins"] >= 3 for key in PRIMARY)
    nominal_pass = (p_drtp["J_nominal"] / p_utr["J_nominal"] >= .95
                    and summaries["J_nominal"]["median"] >= 0)
    safety_pass = (
        p_drtp["collision_failure_mean"] - p_utr["collision_failure_mean"] <= .05
        and p_drtp["timeout_failure_mean"] - p_utr["timeout_failure_mean"] <= .05
        and sum(row["delta_collision"] > 0 for row in paired_rows) < 4
        and sum(row["delta_timeout"] > 0 for row in paired_rows) < 4
        and p_drtp["constraint_failure_mean"] == 0.0
    )
    gates = {
        "complete_12000_records": manifest.get("raw_rows") == 12000 and full_rows,
        "risk_set_trigger_validity": risk_valid,
        "primary_mean_median_and_3of5": return_pass,
        "nominal_retention": nominal_pass,
        "catastrophic_seed_count_at_most_one": catastrophe_count <= 1,
        "safety": safety_pass,
    }
    fail_demotion = (
        catastrophe_count >= 2
        or sum(summaries[key]["mean"] <= 0 and summaries[key]["median"] <= 0 for key in PRIMARY) >= 2
        or p_drtp["constraint_failure_mean"] != 0.0
    )
    technical_valid = gates["complete_12000_records"] and gates["risk_set_trigger_validity"]
    if not technical_valid:
        verdict = "FORMAL_CONFIRMATION_TECHNICAL_INVALID"
    elif all(gates.values()):
        verdict = "FORMAL_CONFIRMATION_PASS_SEED_SENSITIVE"
    elif fail_demotion:
        verdict = "FORMAL_CONFIRMATION_FAIL_DEMOTE_DRTP"
    else:
        verdict = "FORMAL_CONFIRMATION_LIMITATION_ONLY"
    result = {
        "protocol": PROTOCOL, "verdict": verdict, "tape_hash": tape["tape_hash"],
        "primary_inference_unit": "training_seed", "n_paired_training_seeds": 5,
        "pooled": pooled, "paired_summaries": summaries, "paired_rows": paired_rows,
        "catastrophic_seed_count": catastrophe_count, "gates": gates,
        "historical_heldout_fail_preserved": True, "historical_seed2002_preserved": True,
        "canonical_seeds_used": False, "automatic_follow_on_started": False,
    }
    decision_path = eval_root / "DRTP_UTR_Q2_FORMAL_DECISION.json"
    decision_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# DRTP/UTR Q2 Formal Five-Seed Confirmation Report", "",
        f"**Verdict:** `{verdict}`", "",
        "Training seed is the independent unit (`n=5`); all ten final checkpoints and all scheduled episodes are retained.", "",
        "## Frozen gates", "",
    ]
    lines += [f"- `{name}`: {'PASS' if passed else 'FAIL'}" for name, passed in gates.items()]
    lines += ["", "## Paired effect summary", "",
              "| endpoint | mean | median | SD | IQR | MAD | wins/5 | worst |",
              "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for key, item in summaries.items():
        lines.append(f"| {key} | {item['mean']:.6g} | {item['median']:.6g} | {item['sample_sd']:.6g} | {item['iqr']:.6g} | {item['mad']:.6g} | {item['wins']}/5 | {item['worst']:.6g} |")
    lines += ["", "Historical development NO-GO, held-out FAIL, and seed2002 reversal remain unchanged. No additional training is authorized by this report.", ""]
    args.report_path.parent.mkdir(parents=True, exist_ok=True)
    args.report_path.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
