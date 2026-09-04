"""Read completed EGTR data only; identify no post-hoc algorithm or threshold."""
from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from pathlib import Path


SEEDS = {"A": (71011, 71012, 71013, 71014, 71015), "B": (71021, 71022, 71023, 71024, 71025)}
FAILURES = ("F0", "TE", "TL", "DS", "DL", "CP")
FEATURES = (
    "mean_q_uniform_distance", "max_q_uniform_distance", "final_q_uniform_distance",
    "mean_q_step_l1", "max_q_step_l1", "trust_region_active_rate", "mean_rho", "final_rho",
)


def number(row: dict[str, str], field: str) -> float:
    value = row.get(field, "")
    return float(value) if value not in {"", None} else float("nan")


def mean(values: list[float]) -> float:
    kept = [value for value in values if math.isfinite(value)]
    if not kept:
        return float("nan")
    return statistics.fmean(kept)


def ranks(values: list[float]) -> list[float]:
    order = sorted(range(len(values)), key=lambda index: values[index])
    output = [0.0] * len(values)
    index = 0
    while index < len(values):
        start = index
        while index + 1 < len(values) and values[order[index + 1]] == values[order[start]]:
            index += 1
        rank = (start + index + 2) / 2.0
        for cursor in range(start, index + 1):
            output[order[cursor]] = rank
        index += 1
    return output


def spearman(xs: list[float], ys: list[float]) -> float:
    if len(xs) != len(ys) or len(xs) < 3 or not all(math.isfinite(value) for value in xs + ys):
        return float("nan")
    rx, ry = ranks(xs), ranks(ys)
    mx, my = mean(rx), mean(ry)
    numerator = sum((x - mx) * (y - my) for x, y in zip(rx, ry))
    denominator = math.sqrt(sum((x - mx) ** 2 for x in rx) * sum((y - my) ** 2 for y in ry))
    return numerator / denominator if denominator else float("nan")


def metrics(rows: list[dict[str, str]], arm: str, seed: int) -> dict[str, float]:
    condition = {row["condition"]: row for row in rows if row["method"] == arm and int(row["train_seed"]) == seed}
    missing = {"nominal", *FAILURES}.difference(condition)
    if missing:
        raise RuntimeError(f"missing final conditions for {arm}/seed{seed}: {sorted(missing)}")
    failures = [condition[name] for name in FAILURES]
    return {
        "J_nominal": number(condition["nominal"], "J"),
        "J_pert_mean": mean([number(row, "J") for row in failures]),
        "J_pert_worst": min(number(row, "J") for row in failures),
        "collision": mean([number(row, "collision") for row in failures]),
        "timeout": mean([number(row, "timeout") for row in failures]),
    }


def sampler_features(path: Path) -> dict[str, float]:
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    updates = [row for row in rows if row.get("record_type") == "weight_update"]
    if not updates:
        raise RuntimeError(f"no sampler weight-update rows: {path}")
    q_uniform = [number(row, "q_uniform_distance") for row in updates]
    q_step = [number(row, "q_step_l1") for row in updates]
    rho = [number(row, "rho") for row in updates]
    active = [1.0 if str(row.get("trust_region_active", "")).lower() == "true" else 0.0 for row in updates]
    return {
        "mean_q_uniform_distance": mean(q_uniform), "max_q_uniform_distance": max(q_uniform),
        "final_q_uniform_distance": q_uniform[-1], "mean_q_step_l1": mean(q_step),
        "max_q_step_l1": max(q_step), "trust_region_active_rate": mean(active),
        "mean_rho": mean(rho), "final_rho": rho[-1], "weight_update_rows": float(len(updates)),
    }


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fields = list(rows[0])
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader(); writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trained-root", type=Path, required=True)
    parser.add_argument("--evaluation-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("--execute required; this audit only reads completed artifacts")
    manifest = json.loads((args.evaluation_root / "evaluation_manifest.json").read_text(encoding="utf-8"))
    if not (manifest.get("status") == "completed" and manifest.get("raw_rows") == 21000 and manifest.get("cells") == 30):
        raise RuntimeError("completed frozen final evaluation is required")
    final_gate = args.trained_root / "diagnostics" / "egtr_double_cohort_final_gate" / "EGTR_DOUBLE_COHORT_GATE_DECISION.json"
    if not final_gate.exists() or json.loads(final_gate.read_text(encoding="utf-8")).get("verdict") != "EGTR_DOUBLE_COHORT_REPLICATION_NO_GO":
        raise RuntimeError("this post-hoc audit is scoped only to the completed EGTR NO-GO result")
    output = args.output_root / "diagnostics" / "egtr_outcome_decomposition"
    if output.exists():
        raise FileExistsError(f"refusing to overwrite {output}")
    output.mkdir(parents=True)
    summaries = list(csv.DictReader((args.evaluation_root / "per_seed_condition_summary.csv").open(encoding="utf-8")))
    per_seed: list[dict[str, object]] = []
    cohorts: dict[str, list[dict[str, object]]] = {"A": [], "B": []}
    for cohort, seeds in SEEDS.items():
        for seed in seeds:
            utr, original, egtr = (metrics(summaries, arm, seed) for arm in ("utr_sg", "drtp_sg", "egtr_sg"))
            log = args.trained_root / "runs" / "egtr_sg" / f"seed{seed}" / "drtp_topology_sampler_log.csv"
            feature = sampler_features(log)
            row: dict[str, object] = {
                "cohort": cohort, "seed": seed,
                "G_original_vs_utr": original["J_pert_mean"] - utr["J_pert_mean"],
                "G_egtr_vs_utr": egtr["J_pert_mean"] - utr["J_pert_mean"],
                "EGTR_minus_original": egtr["J_pert_mean"] - original["J_pert_mean"],
                "EGTR_nominal_minus_utr": egtr["J_nominal"] - utr["J_nominal"],
                "EGTR_timeout_minus_utr": egtr["timeout"] - utr["timeout"],
                "EGTR_collision_minus_utr": egtr["collision"] - utr["collision"],
                **feature,
            }
            per_seed.append(row); cohorts[cohort].append(row)
    write_csv(output / "EGTR_OUTCOME_DECOMPOSITION_PER_SEED.csv", per_seed)
    correlation_rows: list[dict[str, object]] = []
    for feature in FEATURES:
        row: dict[str, object] = {"feature": feature}
        for cohort in ("A", "B"):
            subset = cohorts[cohort]
            row[f"spearman_{cohort}"] = spearman([float(item[feature]) for item in subset], [float(item["G_egtr_vs_utr"]) for item in subset])
        a, b = float(row["spearman_A"]), float(row["spearman_B"])
        row["same_direction"] = bool(math.isfinite(a) and math.isfinite(b) and a * b > 0.0)
        row["both_abs_ge_0_8"] = bool(row["same_direction"] and abs(a) >= 0.8 and abs(b) >= 0.8)
        correlation_rows.append(row)
    write_csv(output / "EGTR_OUTCOME_DECOMPOSITION_COHORT_CORRELATIONS.csv", correlation_rows)
    repeated = [row for row in correlation_rows if bool(row["both_abs_ge_0_8"])]
    verdict = "EGTR_DECOMPOSITION_HYPOTHESIS_ONLY" if repeated else "EGTR_DECOMPOSITION_NO_REPEATED_TRAINING_SIGNAL"
    result = {
        "protocol": "EGTR-OUTCOME-DECOMPOSITION-POSTHOC-V1", "verdict": verdict,
        "source": "completed 30-trajectory 10M EGTR double-cohort evaluation and EGTR training-only sampler logs",
        "posthoc": True, "independent_unit": "training_seed", "cohorts_analyzed_separately": True,
        "pooled_n10_confirmatory_forbidden": True, "repeated_features": [row["feature"] for row in repeated],
        "algorithm_or_threshold_change_authorized": False, "training_started": False, "evaluation_started": False,
    }
    (output / "EGTR_OUTCOME_DECOMPOSITION_RESULT.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    report = ["# EGTR outcome decomposition", "", f"**Verdict:** `{verdict}`.", "", "This is a post-hoc hypothesis audit, not evidence of a new algorithm.", "It reads no evaluation tape online and changes no training artifact.", "", "## Interpretation rule", "", "A feature is listed as repeated only when its within-cohort Spearman association with EGTR-minus-UTR perturbed return has the same direction and absolute value at least 0.8 in both independent five-seed cohorts. Even then, it is hypothesis-generating only and cannot authorize EGTR-v2, parameter tuning, or a performance claim.", "", "## Candidate repeated features", "", ", ".join(result["repeated_features"]) if result["repeated_features"] else "None.", "", "See `EGTR_OUTCOME_DECOMPOSITION_PER_SEED.csv` and `EGTR_OUTCOME_DECOMPOSITION_COHORT_CORRELATIONS.csv`."]
    (output / "EGTR_OUTCOME_DECOMPOSITION_REPORT.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    (output / "EGTR_OUTCOME_DECOMPOSITION_FINAL_VERDICT.md").write_text(f"# EGTR outcome decomposition final verdict\n\n`{verdict}`\n\nNo new algorithm, parameter revision, training, evaluation, or automatic continuation is authorized.\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
