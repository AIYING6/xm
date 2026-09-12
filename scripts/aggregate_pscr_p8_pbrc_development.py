"""Aggregate the frozen P8 PBRC development matrix without pooling episodes as seeds."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np


ARMS = ("plain", "plan_no_reliability", "permuted_pbrc", "pbrc")
SEEDS = (97211, 97212, 97213)
RELIABILITIES = (0.1, 0.9)


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--root", type=Path, required=True); parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute: raise SystemExit("refusing without --execute")
    if args.root.exists(): raise FileExistsError(f"refusing to overwrite {args.root}")
    rows: list[dict[str, object]] = []
    for arm in ARMS:
        for seed in SEEDS:
            path = args.root.parent / "evaluations" / arm / f"seed{seed}" / "episode_metrics.csv"
            if not path.exists(): raise FileNotFoundError(path)
            source = list(csv.DictReader(path.open(encoding="utf-8")))
            for reliability in RELIABILITIES:
                subset = [row for row in source if float(row["reliability"]) == reliability]
                if not subset: raise ValueError(f"missing {arm}/{seed}/{reliability}")
                row: dict[str, object] = {"arm": arm, "training_seed": seed, "reliability": reliability}
                for field in ("return", "weighted_service_value", "primary_completed", "future_completed", "future_localized", "energy_used", "commit_stage_plan"):
                    row[field] = float(np.mean([float(item[field]) for item in subset]))
                rows.append(row)
    pbrc = [row for row in rows if row["arm"] == "pbrc"]
    gaps = {seed: next(float(row["commit_stage_plan"]) for row in pbrc if int(row["training_seed"]) == seed and float(row["reliability"]) == 0.9) - next(float(row["commit_stage_plan"]) for row in pbrc if int(row["training_seed"]) == seed and float(row["reliability"]) == 0.1) for seed in SEEDS}
    cohort_future = float(np.mean([float(row["future_completed"]) for row in pbrc]))
    checks = {"all_arms_all_seeds_complete": len(rows) == len(ARMS) * len(SEEDS) * len(RELIABILITIES), "pbrc_directional_plan_response": sum(gap >= 0.15 for gap in gaps.values()) >= 2, "pbrc_future_completion_non_saturated": 0.05 <= cohort_future <= 0.95}
    report = {"protocol": "PSCR-P8-PBRC-DEVELOPMENT-V1", "verdict": "PSCR_P8_PBRC_DEVELOPMENT_PASS" if all(checks.values()) else "PSCR_P8_PBRC_DEVELOPMENT_FAIL", "development_only": True, "pbrc_seed_high_minus_low_stage_rate": gaps, "pbrc_mean_future_completion": cohort_future, "checks": checks, "boundary": "Training seeds are the independent units. This is a development gate, not a formal method claim."}
    args.root.mkdir(parents=True)
    with (args.root / "P8_PBRC_DEVELOPMENT_PER_SEED.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    (args.root / "P8_PBRC_DEVELOPMENT_REPORT.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__": main()
