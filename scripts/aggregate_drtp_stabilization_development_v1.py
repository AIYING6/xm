"""Integrated, development-only assessment for Global-Anchored EGTR V1.

This report ranks frozen V1 candidates on the complete predeclared endpoint.
It deliberately does not run training, alter a checkpoint, or authorize V2/
confirmation.  A development result is read holistically: upside, lower tail,
central tendency, seed spread, nominal retention, safety, and whether the
anchored sampler actually remained adaptive.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.run_drtp_stabilization_development_v1_single import ARMS, SEEDS


PROTOCOL = "DRTP-STABILIZATION-DEVELOPMENT-V1-INTEGRATED-ASSESSMENT"
BASELINES = ("utr_sg", "drtp_sg", "egtr_sg")
CANDIDATES = tuple(name for name in ARMS if name.startswith("anchored_egtr_"))
PERTURBED = ("F0", "TE", "DL", "CP")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def finite(value: str | float | int | None) -> float:
    try:
        parsed = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return math.nan
    return parsed if math.isfinite(parsed) else math.nan


def average(values: list[float]) -> float:
    values = [value for value in values if math.isfinite(value)]
    return sum(values) / len(values) if values else math.nan


def sample_sd(values: list[float]) -> float:
    values = [value for value in values if math.isfinite(value)]
    return statistics.stdev(values) if len(values) > 1 else 0.0


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def sampler_summary(trained_root: Path, arm: str, seed: int) -> dict[str, float | int | bool]:
    path = trained_root / "runs" / arm / f"seed{seed}" / "drtp_topology_sampler_log.csv"
    if not path.is_file():
        return {"sampler_log_present": False, "sampler_weight_updates": 0,
                "sampler_adapted_updates": 0, "sampler_anchor_active_updates": 0,
                "sampler_uniform_l1_mean": math.nan, "sampler_uniform_l1_max": math.nan}
    updates = [row for row in read_csv(path) if row.get("record_type") == "weight_update"]
    distances = []
    for row in updates:
        distance = finite(row.get("post_anchor_uniform_l1"))
        if not math.isfinite(distance):
            q = [finite(row.get(f"q_{group}")) for group in ("F0", "TE", "TL", "DS", "DL", "CP")]
            if all(math.isfinite(value) for value in q):
                distance = sum(abs(value - 1.0 / 6.0) for value in q)
        distances.append(distance)
    return {
        "sampler_log_present": True,
        "sampler_weight_updates": len(updates),
        "sampler_adapted_updates": sum(str(row.get("adapted", "")).lower() == "true" for row in updates),
        "sampler_anchor_active_updates": sum(str(row.get("anchor_active", "")).lower() == "true" for row in updates),
        "sampler_uniform_l1_mean": average(distances),
        "sampler_uniform_l1_max": max((value for value in distances if math.isfinite(value)), default=math.nan),
    }


def endpoint_rows(summary: list[dict[str, str]], trained_root: Path) -> list[dict]:
    cells: dict[tuple[str, int], list[dict[str, str]]] = defaultdict(list)
    for row in summary:
        cells[(row["method"], int(row["train_seed"]))].append(row)
    rows: list[dict] = []
    for arm in ARMS:
        for seed in SEEDS:
            by_condition = {row["condition"]: row for row in cells[(arm, seed)]}
            if set(by_condition) != {"nominal", *PERTURBED}:
                raise RuntimeError(f"incomplete endpoint summary for {arm}/seed{seed}")
            nominal = by_condition["nominal"]
            perturbed = [by_condition[name] for name in PERTURBED]
            record = {
                "method": arm, "train_seed": seed,
                "J_nominal": finite(nominal["J"]), "success_nominal": finite(nominal["success"]),
                "collision_nominal": finite(nominal["collision"]), "timeout_nominal": finite(nominal["timeout"]),
                "J_perturbed": average([finite(row["J"]) for row in perturbed]),
                "success_perturbed": average([finite(row["success"]) for row in perturbed]),
                "collision_perturbed": average([finite(row["collision"]) for row in perturbed]),
                "timeout_perturbed": average([finite(row["timeout"]) for row in perturbed]),
                "J_all_conditions": average([finite(row["J"]) for row in by_condition.values()]),
                "success_all_conditions": average([finite(row["success"]) for row in by_condition.values()]),
            }
            record.update(sampler_summary(trained_root, arm, seed))
            rows.append(record)
    return rows


def aggregate_method(rows: list[dict], arm: str) -> dict:
    selected = [row for row in rows if row["method"] == arm]
    result: dict[str, object] = {"method": arm, "seed_count": len(selected)}
    for metric in ("J_perturbed", "success_perturbed", "J_nominal", "success_nominal",
                   "collision_perturbed", "timeout_perturbed", "J_all_conditions", "success_all_conditions"):
        values = [float(row[metric]) for row in selected]
        result[f"mean_{metric}"] = average(values)
        result[f"median_{metric}"] = statistics.median(values)
        result[f"min_{metric}"] = min(values)
        result[f"max_{metric}"] = max(values)
        result[f"range_{metric}"] = max(values) - min(values)
        result[f"sd_{metric}"] = sample_sd(values)
    result["sampler_adapted_updates_total"] = sum(int(row["sampler_adapted_updates"]) for row in selected)
    result["sampler_anchor_active_updates_total"] = sum(int(row["sampler_anchor_active_updates"]) for row in selected)
    result["sampler_uniform_l1_max"] = max(
        (float(row["sampler_uniform_l1_max"]) for row in selected if math.isfinite(float(row["sampler_uniform_l1_max"]))),
        default=math.nan,
    )
    return result


def paired_rows(per_seed: list[dict]) -> list[dict]:
    lookup = {(row["method"], int(row["train_seed"])): row for row in per_seed}
    rows: list[dict] = []
    for candidate in CANDIDATES:
        for baseline in BASELINES:
            for seed in SEEDS:
                c, b = lookup[(candidate, seed)], lookup[(baseline, seed)]
                rows.append({
                    "candidate": candidate, "baseline": baseline, "train_seed": seed,
                    "delta_J_perturbed": float(c["J_perturbed"]) - float(b["J_perturbed"]),
                    "delta_success_perturbed": float(c["success_perturbed"]) - float(b["success_perturbed"]),
                    "delta_J_nominal": float(c["J_nominal"]) - float(b["J_nominal"]),
                    "delta_success_nominal": float(c["success_nominal"]) - float(b["success_nominal"]),
                    "delta_collision_perturbed": float(c["collision_perturbed"]) - float(b["collision_perturbed"]),
                    "delta_timeout_perturbed": float(c["timeout_perturbed"]) - float(b["timeout_perturbed"]),
                })
    return rows


def development_verdict(methods: dict[str, dict], paired: list[dict]) -> tuple[str, str, list[dict]]:
    assessments: list[dict] = []
    for candidate in CANDIDATES:
        record, utr, original, egtr = methods[candidate], methods["utr_sg"], methods["drtp_sg"], methods["egtr_sg"]
        versus_utr = [row for row in paired if row["candidate"] == candidate and row["baseline"] == "utr_sg"]
        versus_original = [row for row in paired if row["candidate"] == candidate and row["baseline"] == "drtp_sg"]
        versus_egtr = [row for row in paired if row["candidate"] == candidate and row["baseline"] == "egtr_sg"]
        mean_vs_utr = average([float(row["delta_J_perturbed"]) for row in versus_utr])
        mean_vs_original = average([float(row["delta_J_perturbed"]) for row in versus_original])
        mean_vs_egtr = average([float(row["delta_J_perturbed"]) for row in versus_egtr])
        lower_tail_better = float(record["min_J_perturbed"]) >= max(float(utr["min_J_perturbed"]), float(original["min_J_perturbed"]))
        spread_reduced = float(record["range_J_perturbed"]) <= float(original["range_J_perturbed"])
        nominal_retained = average([float(row["delta_J_nominal"]) for row in versus_utr]) >= -10.0
        material_safety_harm = (
            average([float(row["delta_collision_perturbed"]) for row in versus_utr]) > 0.10
            or average([float(row["delta_timeout_perturbed"]) for row in versus_utr]) > 0.10
            or max(float(row["delta_collision_perturbed"]) for row in versus_utr) > 0.20
        )
        adaptive = int(record["sampler_adapted_updates_total"]) > 0 and float(record["sampler_uniform_l1_max"]) > 1e-8
        broad_harm = mean_vs_utr < -10.0 and mean_vs_original < -10.0 and not lower_tail_better
        positive_dimensions = sum((
            mean_vs_utr >= 0.0 or mean_vs_original >= 0.0,
            float(record["median_J_perturbed"]) >= float(utr["median_J_perturbed"]),
            lower_tail_better,
            spread_reduced,
            nominal_retained,
            not material_safety_harm,
            adaptive,
        ))
        if adaptive and not material_safety_harm and lower_tail_better and spread_reduced and mean_vs_egtr >= 0.0 and nominal_retained:
            disposition = "strong"
        elif adaptive and not material_safety_harm and not broad_harm and positive_dimensions >= 4:
            disposition = "promising"
        else:
            disposition = "weak"
        assessments.append({
            "candidate": candidate, "disposition": disposition, "positive_dimensions": positive_dimensions,
            "adaptive": adaptive, "material_safety_harm": material_safety_harm, "broad_harm": broad_harm,
            "mean_delta_J_perturbed_vs_utr": mean_vs_utr,
            "mean_delta_J_perturbed_vs_drtp": mean_vs_original,
            "mean_delta_J_perturbed_vs_egtr": mean_vs_egtr,
            "lower_tail_better_than_utr_and_drtp": lower_tail_better,
            "spread_reduced_vs_drtp": spread_reduced, "nominal_retained_vs_utr": nominal_retained,
        })
    if any(row["disposition"] == "strong" for row in assessments):
        return "V1_STRONG", "A frozen candidate merits separate confirmation planning; no continuation is automatic.", assessments
    if any(row["disposition"] == "promising" for row in assessments):
        return "V1_PROMISING_NEEDS_ONE_REVISION", "At most one human-authorized revision may be designed; no automatic V2 is started.", assessments
    return "V1_WEAK", "All frozen candidates lack a balanced development case; no automatic continuation is started.", assessments


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trained-root", type=Path, required=True)
    parser.add_argument("--evaluation-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("explicit --execute is required")
    out = args.output_root / "diagnostics" / "development_assessment"
    if out.exists():
        raise FileExistsError(f"refusing to overwrite {out}")
    manifest = json.loads((args.evaluation_root / "evaluation_manifest.json").read_text(encoding="utf-8"))
    if manifest.get("protocol") != "DRTP-STABILIZATION-DEVELOPMENT-V1-FIXED-ENDPOINT-EVALUATION" or manifest.get("status") != "completed":
        raise RuntimeError("endpoint evaluation is incomplete or from another protocol")
    per_seed = endpoint_rows(read_csv(args.evaluation_root / "per_seed_condition_summary.csv"), args.trained_root)
    methods = {arm: aggregate_method(per_seed, arm) for arm in ARMS}
    paired = paired_rows(per_seed)
    verdict, interpretation, candidate_assessments = development_verdict(methods, paired)
    out.mkdir(parents=True, exist_ok=False)
    write_csv(out / "DEVELOPMENT_PER_SEED_ENDPOINTS.csv", per_seed)
    write_csv(out / "DEVELOPMENT_PAIRED_SEED_SUMMARY.csv", paired)
    write_csv(out / "DEVELOPMENT_CANDIDATE_ASSESSMENT.csv", candidate_assessments)
    report = {
        "protocol": PROTOCOL, "verdict": verdict, "interpretation": interpretation,
        "development_only": True, "integrated_dimensions": ["upside", "lower_tail", "mean", "median", "seed_spread", "nominal", "safety", "adaptivity"],
        "methods": methods, "candidate_assessments": candidate_assessments,
        "automatic_v2_or_confirmation": False, "training_started": False, "evaluation_started": False,
    }
    (out / "DEVELOPMENT_ASSESSMENT.json").write_text(json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8")
    (out / "DEVELOPMENT_ASSESSMENT.md").write_text(
        "# DRTP Stabilization Development V1 integrated assessment\n\n"
        f"**Verdict:** `{verdict}`.\n\n{interpretation}\n\n"
        "This is development evidence, not confirmatory paper evidence. The report jointly considers upside, lower tail, central tendency, seed spread, nominal behavior, safety, and whether each anchored sampler stayed adaptive.\n",
        encoding="utf-8",
    )
    print(json.dumps({"verdict": verdict, "automatic_v2_or_confirmation": False}, indent=2), flush=True)


if __name__ == "__main__":
    main()
