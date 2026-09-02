"""Merge frozen 500k and 1M checkpoint summaries into longitudinal evidence only."""
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FREEZE = ROOT / "configs" / "drtp_c2_m3_1m_posthoc_evaluation_freeze.json"
OLD = ROOT / "configs" / "drtp_c2_m3_posthoc_evaluation_freeze.json"


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def mean(values: list[float]) -> float:
    return sum(values) / len(values)


def score(rows: list[dict[str, str]], arm: str, seed: int, label: str) -> dict[str, float]:
    selected = [row for row in rows if row["arm"] == arm and int(row["seed"]) == seed and row["checkpoint_label"] == label]
    by_condition = {row["condition"]: row for row in selected}
    failure = [float(row["J"]) for condition, row in by_condition.items() if condition != "nominal"]
    if len(failure) != 4 or "nominal" not in by_condition:
        raise RuntimeError(f"incomplete condition summary: {arm}/seed{seed}/{label}")
    return {"J_nominal": float(by_condition["nominal"]["J"]), "J_pert_mean": mean(failure), "J_pert_worst": min(failure), "collision": mean([float(row["collision"]) for condition, row in by_condition.items() if condition != "nominal"]), "timeout": mean([float(row["timeout"]) for condition, row in by_condition.items() if condition != "nominal"])}


def category(delta: float, margin: float) -> str:
    return "rescue" if delta >= margin else "harm" if delta <= -margin else "near_zero"


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--output-root", type=Path, required=True); parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("--execute required")
    freeze, old = json.loads(FREEZE.read_text(encoding="utf-8")), json.loads(OLD.read_text(encoding="utf-8"))
    evaluation_root = args.output_root / "evaluations"
    old_dir = evaluation_root / freeze["prior_evaluation_directory"]
    new_dir = evaluation_root / freeze["new_evaluation_directory"]
    old_manifest, new_manifest = (json.loads((directory / "evaluation_manifest.json").read_text(encoding="utf-8")) for directory in (old_dir, new_dir))
    if old_manifest.get("status") != "completed" or new_manifest.get("status") != "completed" or old_manifest.get("tape_hash") != new_manifest.get("tape_hash"):
        raise RuntimeError("the merged longitudinal record requires two completed evaluations on the same frozen tape")
    target = args.output_root / "diagnostics" / "m3_1m_longitudinal"
    if target.exists():
        raise FileExistsError(f"refusing longitudinal analysis overwrite: {target}")
    target.mkdir(parents=True)
    summary = read_rows(old_dir / "per_seed_condition_summary.csv") + read_rows(new_dir / "per_seed_condition_summary.csv")
    labels = list(old["milestones"].values()) + list(freeze["new_milestones"].values())
    updates = [int(value) for value in old["milestones"]] + [int(value) for value in freeze["new_milestones"]]
    margin = float(old["mechanism_gate"]["final_delta_margin"])
    rows, cohort_summary = [], defaultdict(lambda: {"rescue": 0, "harm": 0, "near_zero": 0, "endpoint_stable": 0, "sign_reversal": 0})
    for cohort, seeds in freeze["cohorts"].items():
        for seed in seeds:
            points = []
            for label, update in zip(labels, updates):
                utr, weighted = score(summary, "utr_sg", seed, label), score(summary, "group_weighted_utr_sg", seed, label)
                points.append({"label": label, "update": update, "delta_J_pert_mean": weighted["J_pert_mean"] - utr["J_pert_mean"], "weighted": weighted, "utr": utr})
            states = [category(point["delta_J_pert_mean"], margin) for point in points]
            nonzero = [state for state in states if state != "near_zero"]
            reverses = any(left != right for left, right in zip(nonzero, nonzero[1:]))
            stable = len(states) >= 3 and len(set(states[-3:])) == 1
            final = states[-1]
            cohort_summary[cohort][final] += 1
            cohort_summary[cohort]["endpoint_stable"] += int(stable)
            cohort_summary[cohort]["sign_reversal"] += int(reverses)
            rows.append({"cohort": cohort, "seed": seed, "final_category": final, "last_three_categories": "->".join(states[-3:]), "endpoint_stable": stable, "any_practical_sign_reversal": reverses, "points": points})
    verdict = freeze["hard_stop"]["result_status"]
    payload = {"protocol": freeze["protocol"], "verdict": verdict, "classification_margin": margin, "labels": labels, "cohort_summary": dict(cohort_summary), "records": rows, "training_seed_is_independent_unit": True, "cohorts_pooled": False, "mechanism_declared": False, "algorithm_modification_authorized": False, "automatic_continuation_authorized": False}
    (target / "M3_1M_LONGITUDINAL_DECISION.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    lines = ["# C2-M3 1M longitudinal evidence", "", f"**Status:** `{verdict}`.", "", "This is a fixed-checkpoint, same-development-tape longitudinal record. It neither selects a checkpoint nor declares a mechanism or authorizes a new algorithm.", "", "| Cohort | rescue at 1M | harm at 1M | near-zero at 1M | endpoint-stable (last 3) | any practical reversal |", "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for cohort in ("A", "B"):
        item = cohort_summary[cohort]
        lines.append(f"| {cohort} | {item['rescue']} | {item['harm']} | {item['near_zero']} | {item['endpoint_stable']} | {item['sign_reversal']} |")
    lines.extend(["", "Per-seed trajectories are stored in `M3_1M_LONGITUDINAL_DECISION.json`. A separate human scientific review is required before any mechanism claim or subsequent action."])
    (target / "M3_1M_LONGITUDINAL_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"verdict": verdict, "report": str(target / "M3_1M_LONGITUDINAL_REPORT.md")}, indent=2))


if __name__ == "__main__":
    main()
