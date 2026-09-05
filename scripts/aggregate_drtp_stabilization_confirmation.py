"""Report a frozen final-method confirmation without changing the algorithm."""
from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.run_drtp_stabilization_confirmatory_single import ARMS, SEEDS  # noqa: E402


PROTOCOL = "DRTP-STABILIZATION-FINAL-CONFIRMATION-REPORT-V1"
FINAL = "global_anchored_egtr_a075_sg"
BASELINES = ("utr_sg", "drtp_sg", "egtr_sg")
PERTURBED = ("F0", "TE", "TL", "DS", "DL", "CP")
OOD = ("TE", "TL", "DS", "DL", "CP")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def f(value: str | float | None) -> float:
    try:
        number = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return math.nan
    return number if math.isfinite(number) else math.nan


def mean(values: list[float]) -> float:
    values = [value for value in values if math.isfinite(value)]
    return sum(values) / len(values) if values else math.nan


def sd(values: list[float]) -> float:
    values = [value for value in values if math.isfinite(value)]
    return statistics.stdev(values) if len(values) > 1 else 0.0


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def sampler_record(trained: Path, seed: int) -> dict[str, float | int | bool]:
    log = trained / "runs" / FINAL / f"seed{seed}" / "drtp_topology_sampler_log.csv"
    rows = [row for row in read_csv(log) if row.get("record_type") == "weight_update"]
    distances = [f(row.get("post_anchor_uniform_l1")) for row in rows]
    return {
        "sampler_weight_updates": len(rows),
        "sampler_adapted_updates": sum(row.get("adapted", "").lower() == "true" for row in rows),
        "anchor_active_updates": sum(row.get("anchor_active", "").lower() == "true" for row in rows),
        "post_anchor_utr_l1_mean": mean(distances),
        "post_anchor_utr_l1_max": max((value for value in distances if math.isfinite(value)), default=math.nan),
        "cumulative_exposure_deviation_l1": sum(abs(f(rows[-1].get(f"cumulative_exposure_deviation_{group}"))) for group in ("F0", "TE", "TL", "DS", "DL", "CP")) if rows else math.nan,
    }


def seed_endpoints(rows: list[dict[str, str]], trained: Path) -> list[dict]:
    cells: dict[tuple[str, int], dict[str, dict[str, str]]] = defaultdict(dict)
    for row in rows:
        cells[(row["method"], int(row["train_seed"]))][row["condition"]] = row
    endpoints = []
    for arm in ARMS:
        for seed in SEEDS:
            cell = cells[(arm, seed)]
            if set(cell) != {"nominal", *PERTURBED}:
                raise RuntimeError(f"incomplete confirmation cell {arm}/seed{seed}")
            nominal = cell["nominal"]
            perturbed = [cell[name] for name in PERTURBED]
            ood = [cell[name] for name in OOD]
            record = {
                "method": arm, "train_seed": seed,
                "J_nominal": f(nominal["J"]), "success_nominal": f(nominal["success"]),
                "J_perturbed": mean([f(row["J"]) for row in perturbed]),
                "J_perturbed_worst_condition": min(f(row["J"]) for row in perturbed),
                "success_perturbed": mean([f(row["success"]) for row in perturbed]),
                "collision_perturbed": mean([f(row["collision"]) for row in perturbed]),
                "timeout_perturbed": mean([f(row["timeout"]) for row in perturbed]),
                "J_ood": mean([f(row["J"]) for row in ood]),
                "J_ood_worst_condition": min(f(row["J"]) for row in ood),
                "success_ood": mean([f(row["success"]) for row in ood]),
            }
            if arm == FINAL:
                record.update(sampler_record(trained, seed))
            endpoints.append(record)
    return endpoints


def method_summary(rows: list[dict], arm: str) -> dict:
    chosen = [row for row in rows if row["method"] == arm]
    report: dict[str, object] = {"method": arm, "seed_count": len(chosen)}
    for metric in ("J_perturbed", "J_perturbed_worst_condition", "success_perturbed", "J_ood", "J_ood_worst_condition", "success_ood", "J_nominal", "success_nominal", "collision_perturbed", "timeout_perturbed"):
        values = [float(row[metric]) for row in chosen]
        report[f"mean_{metric}"] = mean(values)
        report[f"median_{metric}"] = statistics.median(values)
        report[f"min_{metric}"] = min(values)
        report[f"max_{metric}"] = max(values)
        report[f"range_{metric}"] = max(values) - min(values)
        report[f"sd_{metric}"] = sd(values)
    if arm == FINAL:
        report.update({
            "sampler_adapted_updates_total": sum(int(row["sampler_adapted_updates"]) for row in chosen),
            "anchor_active_updates_total": sum(int(row["anchor_active_updates"]) for row in chosen),
            "post_anchor_utr_l1_max": max(float(row["post_anchor_utr_l1_max"]) for row in chosen),
        })
    return report


def classify(summaries: dict[str, dict], paired: list[dict]) -> tuple[str, str]:
    final, utr, original = summaries[FINAL], summaries["utr_sg"], summaries["drtp_sg"]
    paired_utr = [row for row in paired if row["baseline"] == "utr_sg"]
    mean_delta = mean([float(row["delta_J_perturbed"]) for row in paired_utr])
    wins = sum(float(row["delta_J_perturbed"]) > 0.0 for row in paired_utr)
    lower_tail = float(final["min_J_perturbed"]) >= float(original["min_J_perturbed"])
    nominal_broadly_retained = float(final["mean_J_nominal"]) >= float(utr["mean_J_nominal"]) - 10.0
    safety_major = (float(final["mean_collision_perturbed"]) > float(utr["mean_collision_perturbed"]) + 0.10 or float(final["mean_timeout_perturbed"]) > float(utr["mean_timeout_perturbed"]) + 0.10)
    adaptive = int(final["sampler_adapted_updates_total"]) > 0 and int(final["anchor_active_updates_total"]) > 0
    if mean_delta > 0.0 and wins >= 3 and lower_tail and nominal_broadly_retained and not safety_major and adaptive:
        return "CONFIRMATION_STRONG", "The frozen final method shows favorable central tendency, majority seed benefit, lower-tail retention against Original DRTP, acceptable nominal/safety behavior, and active bounded adaptation."
    if mean_delta > 0.0 and wins >= 3 and lower_tail and not safety_major and adaptive:
        return "CONFIRMATION_MIXED_BUT_PUBLISHABLE", "The final method has a positive, reliability-relevant signal with secondary trade-offs; claims should be bounded to the completed evidence."
    return "CONFIRMATION_WEAK", "The completed confirmation does not establish a sufficiently favorable reliability profile. No algorithm revision is started automatically."


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trained-root", type=Path, required=True)
    parser.add_argument("--evaluation-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("explicit --execute is required")
    out = args.output_root / "diagnostics" / "confirmation_final"
    if out.exists():
        raise FileExistsError(f"refusing to overwrite {out}")
    manifest = json.loads((args.evaluation_root / "evaluation_manifest.json").read_text(encoding="utf-8"))
    if manifest.get("protocol") != "DRTP-STABILIZATION-FINAL-CONFIRMATION-10M-EVALUATION-V1" or manifest.get("status") != "completed":
        raise RuntimeError("incomplete or incompatible confirmatory evaluation")
    endpoints = seed_endpoints(read_csv(args.evaluation_root / "per_seed_condition_summary.csv"), args.trained_root)
    summaries = {arm: method_summary(endpoints, arm) for arm in ARMS}
    lookup = {(row["method"], int(row["train_seed"])): row for row in endpoints}
    paired = []
    for baseline in BASELINES:
        for seed in SEEDS:
            final, base = lookup[(FINAL, seed)], lookup[(baseline, seed)]
            paired.append({
                "baseline": baseline, "train_seed": seed,
                "delta_J_perturbed": float(final["J_perturbed"]) - float(base["J_perturbed"]),
                "delta_success_perturbed": float(final["success_perturbed"]) - float(base["success_perturbed"]),
                "delta_J_nominal": float(final["J_nominal"]) - float(base["J_nominal"]),
                "delta_collision_perturbed": float(final["collision_perturbed"]) - float(base["collision_perturbed"]),
                "delta_timeout_perturbed": float(final["timeout_perturbed"]) - float(base["timeout_perturbed"]),
            })
    verdict, interpretation = classify(summaries, paired)
    out.mkdir(parents=True, exist_ok=False)
    write_csv(out / "CONFIRMATION_PER_SEED_ENDPOINTS.csv", endpoints)
    write_csv(out / "CONFIRMATION_PAIRED_SEED_DELTAS.csv", paired)
    report = {"protocol": PROTOCOL, "verdict": verdict, "interpretation": interpretation, "summaries": summaries, "primary_unit": "training_seed", "raw_range_sd_auxiliary_only": True, "automatic_algorithm_revision": False, "automatic_6uav": False}
    (out / "CONFIRMATION_REPORT.json").write_text(json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8")
    (out / "CONFIRMATION_REPORT.md").write_text(f"# DRTP final confirmation report\n\n**Verdict:** `{verdict}`.\n\n{interpretation}\n\nRange and SD are descriptive only: they must be interpreted together with lower-tail and worst-seed behavior.\n", encoding="utf-8")
    print(json.dumps({"verdict": verdict, "automatic_algorithm_revision": False}, indent=2), flush=True)


if __name__ == "__main__":
    main()
