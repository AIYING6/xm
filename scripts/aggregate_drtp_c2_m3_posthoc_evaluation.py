"""Describe fixed M3 temporal ordering; never designs or launches an intervention."""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FREEZE = ROOT / "configs" / "drtp_c2_m3_posthoc_evaluation_freeze.json"


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def mean(values: list[float]) -> float:
    return sum(values) / len(values)


def metric(summary: list[dict[str, str]], arm: str, seed: int, label: str) -> dict[str, float]:
    values = {row["condition"]: row for row in summary if row["arm"] == arm and int(row["seed"]) == seed and row["checkpoint_label"] == label}
    failure = [float(values[name]["J"]) for name in values if name != "nominal"]
    if len(failure) != 4 or "nominal" not in values:
        raise RuntimeError(f"incomplete summary for {arm}/{seed}/{label}")
    return {
        "J_nominal": float(values["nominal"]["J"]),
        "J_pert_mean": mean(failure),
        "J_pert_worst": min(failure),
        "collision": mean([float(values[name]["collision"]) for name in values if name != "nominal"]),
        "timeout": mean([float(values[name]["timeout"]) for name in values if name != "nominal"]),
        "constraint": max(float(values[name]["constraint_violation"]) for name in values if name != "nominal"),
    }


def telemetry_signal(run: Path, update_max: int) -> dict[str, float]:
    group = [row for row in rows(run / "group_credit_telemetry.csv") if row["status"] == "OK" and int(row["update"]) <= update_max]
    conflict = [row for row in rows(run / "group_credit_gradient_conflicts.csv") if row["status"] == "OK" and int(row["update"]) <= update_max]
    if not group:
        return {"td_abs_q90": math.nan, "advantage_std": math.nan, "actor_gradient_norm": math.nan, "actor_conflict_rate": math.nan}
    conflict_rate = mean([float(row["actor_gradient_conflict"].strip().lower() == "true") for row in conflict]) if conflict else math.nan
    return {"td_abs_q90": mean([float(row["td_residual_abs_q90"]) for row in group]), "advantage_std": mean([float(row["raw_advantage_std"]) for row in group]), "actor_gradient_norm": mean([float(row["actor_gradient_norm"]) for row in group]), "actor_conflict_rate": conflict_rate}


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--output-root", type=Path, required=True); parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("--execute required")
    freeze = json.loads(FREEZE.read_text(encoding="utf-8")); root = args.output_root; evaluation = root / "evaluations" / "m3_fixed_milestones"
    manifest = json.loads((evaluation / "evaluation_manifest.json").read_text(encoding="utf-8"))
    if manifest.get("status") != "completed":
        raise RuntimeError("M3 milestone evaluation is incomplete")
    report = root / "diagnostics" / "m3_posthoc_temporal_ordering"
    if report.exists():
        raise FileExistsError(f"refusing aggregation overwrite: {report}")
    summary = rows(evaluation / "per_seed_condition_summary.csv"); labels = list(freeze["milestones"].values()); updates = [int(value) for value in freeze["milestones"]]
    margin = float(freeze["mechanism_gate"]["final_delta_margin"]); record = []
    classifications: dict[str, dict[str, list[int]]] = {}
    for cohort, seeds in freeze["cohorts"].items():
        classifications[cohort] = {"rescue": [], "harm": [], "near_zero": []}
        for seed in seeds:
            trajectory = []
            for label, update in zip(labels, updates):
                utr = metric(summary, "utr_sg", seed, label); weighted = metric(summary, "group_weighted_utr_sg", seed, label)
                signals = telemetry_signal(root / "runs" / "group_weighted_utr_sg" / f"seed{seed}", update)
                trajectory.append({"label": label, "update": update, "weighted_minus_utr_J_pert_mean": weighted["J_pert_mean"] - utr["J_pert_mean"], "weighted": weighted, "utr": utr, "training_only_signal": signals})
            final_delta = trajectory[-1]["weighted_minus_utr_J_pert_mean"]
            category = "rescue" if final_delta >= margin else "harm" if final_delta <= -margin else "near_zero"
            classifications[cohort][category].append(seed)
            record.append({"cohort": cohort, "seed": seed, "final_category": category, "milestones": trajectory})
    coverage = {cohort: {category: len(seed_list) for category, seed_list in categories.items()} for cohort, categories in classifications.items()}
    sufficient = all(coverage[cohort]["rescue"] >= freeze["mechanism_gate"]["minimum_rescue_and_harm_seeds_per_cohort"] and coverage[cohort]["harm"] >= freeze["mechanism_gate"]["minimum_rescue_and_harm_seeds_per_cohort"] for cohort in coverage)
    verdict = "M3_ACTIONABLE_MECHANISM_CANDIDATE" if sufficient else "M3_NO_ACTIONABLE_MECHANISM"
    report.mkdir(parents=True)
    payload = {"protocol": freeze["protocol"], "verdict": verdict, "classification_margin": margin, "coverage": coverage, "sufficient_rescue_and_harm_coverage": sufficient, "records": record, "inference_unit": "training_seed", "evaluation_is_posthoc_temporal_ordering_only": True, "mechanism_declared": False, "algorithm_modification_authorized": False, "automatic_continuation_authorized": False}
    (report / "M3_TEMPORAL_ORDERING_DECISION.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    text = f"# C2-M3 post-hoc temporal-ordering report\n\n**Verdict:** `{verdict}`.\n\nThis report is descriptive. It uses the fixed checkpoints solely to order training-only telemetry relative to task divergence; it does not select a checkpoint, declare a mechanism, or authorize an algorithm.\n\n| Cohort | rescue | harm | near-zero |\n| --- | ---: | ---: | ---: |\n" + "\n".join(f"| {cohort} | {values['rescue']} | {values['harm']} | {values['near_zero']} |" for cohort, values in coverage.items()) + "\n"
    (report / "M3_TEMPORAL_ORDERING_REPORT.md").write_text(text, encoding="utf-8")
    print(json.dumps({"verdict": verdict, "report": str(report / "M3_TEMPORAL_ORDERING_REPORT.md")}, indent=2))


if __name__ == "__main__":
    main()
