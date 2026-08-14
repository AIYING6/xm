"""Apply frozen maturity and development-retention decisions to DRTP evaluations."""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path


PROTOCOL = "DRTP-SG-DEVELOPMENT-AGGREGATION-V1"
ARMS = ("utr_sg", "drtp_sg")
SEEDS = (1901, 1902)
LABELS = {"1m": ("750k", "1m"), "2m": ("1500k", "2m"), "3m": ("2500k", "3m")}


def rows_from(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def value(row: dict[str, str], field: str) -> float:
    return float(row[field])


def finite_mean(values: list[float]) -> float:
    values = [item for item in values if math.isfinite(item)]
    return sum(values) / len(values) if values else math.nan


def condition_row(rows: list[dict[str, str]], arm: str, seed: int, label: str, condition: str) -> dict[str, str]:
    matches = [row for row in rows if row["arm"] == arm and int(row["seed"]) == seed
               and row["checkpoint_label"] == label and row["condition"] == condition]
    if len(matches) != 1:
        raise RuntimeError(f"expected one row for {arm}/{seed}/{label}/{condition}, found {len(matches)}")
    return matches[0]


def metrics(rows: list[dict[str, str]], arm: str, seed: int, label: str, ood: tuple[str, ...]) -> dict:
    nominal = condition_row(rows, arm, seed, label, "nominal")
    f0 = condition_row(rows, arm, seed, label, "f0_seen_44_80")
    ood_rows = [condition_row(rows, arm, seed, label, condition) for condition in ood]
    j_f0 = value(f0, "J")
    j_ood = [value(row, "J") for row in ood_rows]
    all_failure = [f0, *ood_rows]
    return {
        "arm": arm, "seed": seed, "checkpoint_label": label,
        "J_nominal": value(nominal, "J"), "J_F0": j_f0,
        "J_OOD_mean": finite_mean(j_ood), "J_OOD_worst": min(j_ood),
        "R_OOD_mean": finite_mean(j_ood) / j_f0 if j_f0 else math.nan,
        "R_OOD_worst": min(j_ood) / j_f0 if j_f0 else math.nan,
        "collision_failure_mean": finite_mean([value(row, "collision") for row in all_failure]),
        "timeout_failure_mean": finite_mean([value(row, "timeout") for row in all_failure]),
        "constraint_failure_mean": finite_mean([value(row, "constraint_violation") for row in all_failure]),
        "failure_exposure_mean": finite_mean([value(row, "failure_exposure") for row in all_failure]),
        "episode_length_failure_mean": finite_mean([value(row, "episode_length") for row in all_failure]),
        "path_switch_count_failure_mean": finite_mean([value(row, "path_switch_count") for row in all_failure]),
        "direct_path_fraction_failure_mean": finite_mean([value(row, "direct_path_fraction") for row in all_failure]),
        "task_support_fraction_failure_mean": finite_mean([value(row, "task_support_fraction") for row in all_failure]),
    }


def pooled(cells: list[dict]) -> dict:
    numeric = [key for key in cells[0] if key not in {"arm", "seed", "checkpoint_label"}]
    return {key: finite_mean([float(cell[key]) for cell in cells]) for key in numeric}


def extension_cell(before: dict, after: dict) -> dict:
    prior = float(before["J_OOD_worst"])
    current = float(after["J_OOD_worst"])
    return {"seed": after["seed"], "before": prior, "after": current,
            "relative_improvement": (current - prior) / (abs(prior) + 1e-8),
            "non_negative_direction": current >= prior}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-root", type=Path, required=True)
    parser.add_argument("--budget", choices=tuple(LABELS), required=True)
    args = parser.parse_args()
    tape = json.loads((args.results_root / "tape_manifest.json").read_text(encoding="utf-8"))
    if tape.get("episode_ids") != list(range(420000, 420100)):
        raise RuntimeError("invalid tape namespace")
    expected_conditions = [item["name"] for item in tape["conditions"]]
    if expected_conditions[:2] != ["nominal", "f0_seen_44_80"] or len(expected_conditions) != 12:
        raise RuntimeError("invalid frozen condition table")
    ood = tuple(expected_conditions[2:])
    eval_root = args.results_root / "evaluations" / args.budget
    manifest = json.loads((eval_root / "evaluation_manifest.json").read_text(encoding="utf-8"))
    if manifest.get("status") != "completed" or manifest.get("tape_hash") != tape["tape_hash"]:
        raise RuntimeError("incomplete or mismatched evaluation")
    rows = rows_from(eval_root / "per_seed_condition_summary.csv")
    before_label, final_label = LABELS[args.budget]
    all_metrics = [metrics(rows, arm, seed, label, ood) for arm in ARMS for seed in SEEDS for label in (before_label, final_label)]
    final_cells = [cell for cell in all_metrics if cell["checkpoint_label"] == final_label]
    previous_cells = [cell for cell in all_metrics if cell["checkpoint_label"] == before_label]
    per_seed_path = eval_root / "per_seed_budget_metrics.csv"
    with per_seed_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(all_metrics[0])); writer.writeheader(); writer.writerows(all_metrics)
    by_arm = {arm: [cell for cell in final_cells if cell["arm"] == arm] for arm in ARMS}
    pooled_final = {arm: pooled(by_arm[arm]) for arm in ARMS}
    maturity = {}
    extension_required = False
    for arm in ARMS:
        per_seed = [extension_cell(next(cell for cell in previous_cells if cell["arm"] == arm and cell["seed"] == seed),
                                   next(cell for cell in final_cells if cell["arm"] == arm and cell["seed"] == seed))
                    for seed in SEEDS]
        pooled_before = pooled([cell for cell in previous_cells if cell["arm"] == arm])["J_OOD_worst"]
        pooled_after = pooled_final[arm]["J_OOD_worst"]
        pooled_relative = (pooled_after - pooled_before) / (abs(pooled_before) + 1e-8)
        triggered = pooled_relative >= 0.05 and all(cell["non_negative_direction"] for cell in per_seed)
        extension_required |= triggered
        maturity[arm] = {"primary_metric": "J_OOD_worst", "previous_label": before_label,
                         "final_label": final_label, "per_seed": per_seed,
                         "pooled_before": pooled_before, "pooled_after": pooled_after,
                         "pooled_relative_improvement": pooled_relative, "triggered": triggered}
    utr, drtp = pooled_final["utr_sg"], pooled_final["drtp_sg"]
    ratios = {key: drtp[key] / utr[key] if utr[key] else math.nan for key in ("J_nominal", "J_F0", "J_OOD_mean", "J_OOD_worst", "R_OOD_mean", "R_OOD_worst")}
    directions = {key: [next(cell for cell in by_arm["drtp_sg"] if cell["seed"] == seed)[key] -
                        next(cell for cell in by_arm["utr_sg"] if cell["seed"] == seed)[key] for seed in SEEDS]
                  for key in ("J_OOD_mean", "J_OOD_worst")}
    seed_condition_safety = []
    for seed in SEEDS:
        for condition in expected_conditions[1:]:
            u = condition_row(rows, "utr_sg", seed, final_label, condition)
            d = condition_row(rows, "drtp_sg", seed, final_label, condition)
            seed_condition_safety.append({"seed": seed, "condition": condition,
                                          "collision_difference": value(d, "collision") - value(u, "collision"),
                                          "timeout_difference": value(d, "timeout") - value(u, "timeout")})
    gate_rows = {
        "nominal_retention": ratios["J_nominal"] >= .95 and all(cell["J_nominal"] / next(ref for ref in by_arm["utr_sg"] if ref["seed"] == cell["seed"])["J_nominal"] >= .90 for cell in by_arm["drtp_sg"]),
        "F0_retention": ratios["J_F0"] >= .98 and all(cell["J_F0"] / next(ref for ref in by_arm["utr_sg"] if ref["seed"] == cell["seed"])["J_F0"] >= .90 for cell in by_arm["drtp_sg"]),
        "OOD_mean": ratios["J_OOD_mean"] >= 1.05 and all(delta >= 0 for delta in directions["J_OOD_mean"]),
        "OOD_worst": ratios["J_OOD_worst"] >= 1.05 and all(delta >= 0 for delta in directions["J_OOD_worst"]),
        "self_reference": ratios["R_OOD_mean"] >= 1.0 and ratios["R_OOD_worst"] >= 1.0,
        "constraints": drtp["constraint_failure_mean"] == 0.0,
        "collision_safety": drtp["collision_failure_mean"] - utr["collision_failure_mean"] <= .05 and all(row["collision_difference"] <= .10 for row in seed_condition_safety),
        "timeout_safety": drtp["timeout_failure_mean"] - utr["timeout_failure_mean"] <= .05 and all(row["timeout_difference"] <= .10 for row in seed_condition_safety),
        "all_planned_pairs_reported": True,
    }
    if extension_required and args.budget != "3m":
        development_verdict = "PENDING_COMMON_BUDGET_EXTENSION"
    elif args.budget == "3m" and extension_required:
        development_verdict = "TRAINING_MATURITY_UNRESOLVED_AT_LE_3M"
    elif all(gate_rows.values()):
        development_verdict = "DEVELOPMENT_RETENTION_PASS_HELD_OUT_REQUIRES_SEPARATE_AUTHORIZATION"
    else:
        development_verdict = "DEVELOPMENT_RETENTION_NO_GO"
    result = {
        "protocol": PROTOCOL, "budget": args.budget, "complete": True, "tape_hash": tape["tape_hash"],
        "primary_maturity_metric": "J_OOD_worst", "maturity": maturity,
        "common_budget_extension_required": extension_required,
        "pooled_final": pooled_final, "ratios_drtp_over_utr": ratios,
        "per_seed_ood_directions_drtp_minus_utr": directions,
        "seed_condition_safety": seed_condition_safety, "development_gate_rows": gate_rows,
        "development_verdict": development_verdict, "canonical_seeds_used": False,
        "held_out_tape_generated_or_used": False, "held_out_started": False,
    }
    (eval_root / "DRTP_DEVELOPMENT_DECISION.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
