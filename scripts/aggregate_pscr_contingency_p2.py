"""Aggregate the frozen PSCR P2 contingency pilot by training seed."""
from __future__ import annotations

import argparse
import csv
import json
import statistics
from pathlib import Path


METRICS = ("return", "weighted_service_value", "primary_completed", "future_completed", "primary_expired", "future_expired", "energy_used", "reconfiguration_events")
ARMS = ("direct", "robust", "masked")
PROFILES = ("bounded_mixture", "urgent_opposite", "routine_aligned")


def avg(values: list[float]) -> float:
    return float(statistics.fmean(values))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--seeds", type=int, nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--label", default="PSCR_P2", help="artifact prefix, e.g. PSCR_P3")
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite {args.output}")

    per_seed: list[dict[str, object]] = []
    for arm in ARMS:
        for seed in args.seeds:
            source = args.root / f"evaluation_{arm}_seed{seed}" / "episode_metrics.csv"
            if not source.is_file():
                raise FileNotFoundError(source)
            with source.open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            if len(rows) != 72:
                raise ValueError(f"expected 72 endpoint episodes: {source}")
            for profile in PROFILES:
                subset = [row for row in rows if row["profile"] == profile]
                if len(subset) != 24:
                    raise ValueError(f"expected 24 episodes for {arm}/{seed}/{profile}")
                per_seed.append({"arm": arm, "training_seed": seed, "profile": profile, **{metric: avg([float(row[metric]) for row in subset]) for metric in METRICS}})

    summaries: list[dict[str, object]] = []
    for arm in ARMS:
        for profile in PROFILES:
            subset = [row for row in per_seed if row["arm"] == arm and row["profile"] == profile]
            record: dict[str, object] = {"arm": arm, "profile": profile, "n_training_seeds": len(subset)}
            for metric in METRICS:
                values = [float(row[metric]) for row in subset]
                record[f"mean_{metric}"] = avg(values)
                record[f"median_{metric}"] = float(statistics.median(values))
                record[f"min_{metric}"] = min(values)
                record[f"sample_sd_{metric}"] = float(statistics.stdev(values)) if len(values) > 1 else 0.0
            summaries.append(record)

    paired: list[dict[str, object]] = []
    for control in ("direct", "masked"):
        for seed in args.seeds:
            for profile in PROFILES:
                full = next(row for row in per_seed if row["arm"] == "robust" and row["training_seed"] == seed and row["profile"] == profile)
                base = next(row for row in per_seed if row["arm"] == control and row["training_seed"] == seed and row["profile"] == profile)
                paired.append({"candidate": "robust", "control": control, "training_seed": seed, "profile": profile, **{f"delta_{metric}": float(full[metric]) - float(base[metric]) for metric in METRICS}})

    args.output.mkdir(parents=True)
    for name, rows in ((f"{args.label}_PER_SEED_ENDPOINTS.csv", per_seed), (f"{args.label}_PROFILE_SUMMARY.csv", summaries), (f"{args.label}_PAIRED_DELTAS.csv", paired)):
        with (args.output / name).open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader(); writer.writerows(rows)
    manifest = {
        "protocol": f"{args.label}-PILOT-AGGREGATION-V1",
        "independent_unit": "training_seed",
        "training_seeds": args.seeds,
        "episodes_per_seed_profile": 24,
        "arms": list(ARMS),
        "profiles": list(PROFILES),
        "interpretation_boundary": "Development pilot; episode rows estimate each trained policy, while only seed summaries are independent repetitions.",
    }
    (args.output / f"{args.label}_ENDPOINT_MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
