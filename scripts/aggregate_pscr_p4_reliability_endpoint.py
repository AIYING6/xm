"""Aggregate PSCR P4 endpoints with training seed as the independent unit."""
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
        bands = sorted({row["reliability_band"] for row in episodes})
        if bands != ["r0.25", "r0.90"]:
            raise ValueError(f"unexpected reliability bands for training seed {seed}: {bands}")
        for band in bands:
            subset = [row for row in episodes if row["reliability_band"] == band]
            if not subset:
                raise ValueError(f"no endpoint episodes for {seed}/{band}")
            per_seed.append({"training_seed": seed, "reliability_band": band, **{
                metric: mean([float(row[metric]) for row in subset]) for metric in METRICS
            }})

    summaries: list[dict[str, object]] = []
    for band in ["r0.25", "r0.90"]:
        subset = [row for row in per_seed if row["reliability_band"] == band]
        result: dict[str, object] = {"reliability_band": band, "n_training_seeds": len(subset)}
        for metric in METRICS:
            values = [float(row[metric]) for row in subset]
            result.update({
                f"mean_{metric}": mean(values),
                f"median_{metric}": float(statistics.median(values)),
                f"min_{metric}": min(values),
                f"sample_sd_{metric}": float(statistics.stdev(values)) if len(values) > 1 else 0.0,
            })
        summaries.append(result)

    args.output.mkdir(parents=True)
    with (args.output / "PSCR_P4_G0_PER_SEED_ENDPOINTS.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(per_seed[0]))
        writer.writeheader(); writer.writerows(per_seed)
    with (args.output / "PSCR_P4_G0_BAND_SUMMARY.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summaries[0]))
        writer.writeheader(); writer.writerows(summaries)
    report = {
        "protocol": "PSCR-P4-RELIABILITY-ENDPOINT-AGGREGATION-V1",
        "independent_unit": "training_seed",
        "training_seeds": args.seeds,
        "reliability_bands": ["r0.25", "r0.90"],
        "interpretation_boundary": "Reliability bands are evaluation strata within each trained policy; they do not increase the number of independent training repetitions.",
    }
    (args.output / "PSCR_P4_G0_ENDPOINT_MANIFEST.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
