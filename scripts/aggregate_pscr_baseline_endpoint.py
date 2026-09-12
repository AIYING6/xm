"""Aggregate fixed PSCR endpoint evaluations with training seed as the unit."""
from __future__ import annotations

import argparse
import csv
import json
import statistics
from pathlib import Path


METRICS = (
    "return",
    "weighted_service_value",
    "primary_completed",
    "future_completed",
    "primary_expired",
    "future_expired",
    "energy_used",
    "reconfiguration_events",
)


def mean(values: list[float]) -> float:
    return float(statistics.fmean(values))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--seeds", type=int, nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite {args.output}")

    per_seed: list[dict[str, object]] = []
    for seed in args.seeds:
        source = args.root / f"evaluation_seed{seed}" / "episode_metrics.csv"
        if not source.is_file():
            raise FileNotFoundError(f"missing endpoint metrics for training seed {seed}: {source}")
        with source.open(newline="", encoding="utf-8") as handle:
            episodes = list(csv.DictReader(handle))
        profiles = sorted({row["profile"] for row in episodes})
        if len(episodes) != 72 or profiles != ["bounded_mixture", "routine_aligned", "urgent_opposite"]:
            raise ValueError(f"unexpected frozen endpoint layout for training seed {seed}")
        for profile in profiles:
            subset = [row for row in episodes if row["profile"] == profile]
            if len(subset) != 24:
                raise ValueError(f"expected 24 episodes for {seed}/{profile}")
            per_seed.append(
                {"training_seed": seed, "profile": profile, **{metric: mean([float(row[metric]) for row in subset]) for metric in METRICS}}
            )

    summaries: list[dict[str, object]] = []
    for profile in sorted({str(row["profile"]) for row in per_seed}):
        subset = [row for row in per_seed if row["profile"] == profile]
        result: dict[str, object] = {"profile": profile, "n_training_seeds": len(subset)}
        for metric in METRICS:
            values = [float(row[metric]) for row in subset]
            result[f"mean_{metric}"] = mean(values)
            result[f"median_{metric}"] = float(statistics.median(values))
            result[f"min_{metric}"] = min(values)
            result[f"sample_sd_{metric}"] = float(statistics.stdev(values)) if len(values) > 1 else 0.0
        summaries.append(result)

    args.output.mkdir(parents=True)
    with (args.output / "PSCR_G1_PER_SEED_ENDPOINTS.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(per_seed[0]))
        writer.writeheader(); writer.writerows(per_seed)
    with (args.output / "PSCR_G1_PROFILE_SUMMARY.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summaries[0]))
        writer.writeheader(); writer.writerows(summaries)
    report = {
        "protocol": "PSCR-G1-ENDPOINT-AGGREGATION-V1",
        "independent_unit": "training_seed",
        "training_seeds": args.seeds,
        "episodes_per_seed_profile": 24,
        "profiles": [row["profile"] for row in summaries],
        "interpretation_boundary": "Episode rows support each trained policy estimate; only training-seed summaries are independent repetitions.",
    }
    (args.output / "PSCR_G1_ENDPOINT_MANIFEST.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
