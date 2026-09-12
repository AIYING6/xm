"""Aggregate the pre-frozen P8 plain-MAPPO learnability gate."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


PROTOCOL = "PSCR-P8-PLAIN-MAPPO-LEARNABILITY-V1"
SEEDS = (97111, 97112, 97113)
RELIABILITIES = (0.1, 0.9)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("refusing without --execute")
    if args.root.exists():
        raise FileExistsError(f"refusing to overwrite {args.root}")
    rows: list[dict[str, object]] = []
    for seed in SEEDS:
        metrics = args.root.parent / "evaluations" / "plain_mappo" / f"seed{seed}" / "episode_metrics.csv"
        if not metrics.exists():
            raise FileNotFoundError(metrics)
        values: dict[float, list[dict[str, str]]] = {r: [] for r in RELIABILITIES}
        with metrics.open(encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                values[float(row["reliability"])].append(row)
        for reliability in RELIABILITIES:
            subset = values[reliability]
            if not subset:
                raise ValueError(f"no rows for seed {seed}, reliability {reliability}")
            rows.append({
                "seed": seed,
                "reliability": reliability,
                "return": sum(float(r["return"]) for r in subset) / len(subset),
                "weighted_service_value": sum(float(r["weighted_service_value"]) for r in subset) / len(subset),
                "primary_completed": sum(float(r["primary_completed"]) for r in subset) / len(subset),
                "future_completed": sum(float(r["future_completed"]) for r in subset) / len(subset),
                "future_localized": sum(float(r["future_localized"]) for r in subset) / len(subset),
                "energy_used": sum(float(r["energy_used"]) for r in subset) / len(subset),
            })
    by_seed = {seed: [r for r in rows if int(r["seed"]) == seed] for seed in SEEDS}
    primary_seed_count = sum(all(float(r["primary_completed"]) >= 0.5 for r in by_seed[seed]) for seed in SEEDS)
    future_seed_count = sum(any(float(r["future_completed"]) > 0.0 for r in by_seed[seed]) for seed in SEEDS)
    cohort_future = sum(float(r["future_completed"]) for r in rows) / len(rows)
    checks = {
        "all_three_endpoints_present": len(rows) == len(SEEDS) * len(RELIABILITIES),
        "primary_completion_two_of_three": primary_seed_count >= 2,
        "future_completion_two_of_three": future_seed_count >= 2,
        "future_completion_non_saturated": 0.05 <= cohort_future <= 0.95,
    }
    verdict = "PSCR_P8_PLAIN_LEARNABILITY_PASS" if all(checks.values()) else "PSCR_P8_PLAIN_LEARNABILITY_FAIL"
    args.root.mkdir(parents=True)
    with (args.root / "P8_PLAIN_LEARNABILITY_PER_SEED.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    report = {
        "protocol": PROTOCOL,
        "verdict": verdict,
        "development_only": True,
        "training_seeds": list(SEEDS),
        "evaluation_reliabilities": list(RELIABILITIES),
        "primary_completion_seed_count": primary_seed_count,
        "future_completion_seed_count": future_seed_count,
        "cohort_mean_future_completion": cohort_future,
        "checks": checks,
        "boundary": "This gate establishes task learnability and non-saturation only. It is not a method comparison or a basis for scientific claims.",
    }
    (args.root / "P8_PLAIN_LEARNABILITY_REPORT.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
