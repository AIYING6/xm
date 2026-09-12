"""Aggregate pre-registered RC-PSCR M1 endpoints and paired controls."""
from __future__ import annotations

import argparse
import csv
import json
import statistics
from pathlib import Path


METRICS = ("return", "weighted_service_value", "primary_completed", "future_completed", "primary_expired", "future_expired", "energy_used", "reconfiguration_events")


def avg(values: list[float]) -> float:
    return float(statistics.fmean(values))


def load_seed(root: Path, arm: str, seed: int) -> list[dict[str, str]]:
    source = root / arm / f"evaluation_seed{seed}" / "episode_metrics.csv"
    if not source.is_file():
        raise FileNotFoundError(f"missing endpoint file: {source}")
    with source.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if sorted({row["reliability_band"] for row in rows}) != ["r0.25", "r0.90"]:
        raise ValueError(f"unexpected endpoint bands for {arm}/{seed}")
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--seeds", type=int, nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite {args.output}")

    arms = ("full", "phase_control", "permuted_reliability")
    per_seed: list[dict[str, object]] = []
    for arm in arms:
        for seed in args.seeds:
            rows = load_seed(args.root, arm, seed)
            for band in ("r0.25", "r0.90"):
                subset = [row for row in rows if row["reliability_band"] == band]
                per_seed.append({"arm": arm, "training_seed": seed, "reliability_band": band, **{
                    metric: avg([float(row[metric]) for row in subset]) for metric in METRICS
                }})

    paired: list[dict[str, object]] = []
    for control in ("phase_control", "permuted_reliability"):
        for seed in args.seeds:
            for band in ("r0.25", "r0.90"):
                full = next(row for row in per_seed if row["arm"] == "full" and row["training_seed"] == seed and row["reliability_band"] == band)
                other = next(row for row in per_seed if row["arm"] == control and row["training_seed"] == seed and row["reliability_band"] == band)
                paired.append({"candidate": "full", "control": control, "training_seed": seed, "reliability_band": band, **{
                    f"delta_{metric}": float(full[metric]) - float(other[metric]) for metric in METRICS
                }})

    summary: list[dict[str, object]] = []
    for arm in arms:
        for band in ("r0.25", "r0.90"):
            subset = [row for row in per_seed if row["arm"] == arm and row["reliability_band"] == band]
            line: dict[str, object] = {"arm": arm, "reliability_band": band, "n_training_seeds": len(subset)}
            for metric in METRICS:
                values = [float(row[metric]) for row in subset]
                line.update({f"mean_{metric}": avg(values), f"median_{metric}": float(statistics.median(values)), f"min_{metric}": min(values)})
            summary.append(line)

    args.output.mkdir(parents=True)
    for name, rows in (("PSCR_RC_M1_PER_SEED_ENDPOINTS.csv", per_seed), ("PSCR_RC_M1_PAIRED_DELTAS.csv", paired), ("PSCR_RC_M1_SUMMARY.csv", summary)):
        with (args.output / name).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    manifest = {
        "protocol": "PSCR-RC-COMMITMENT-RELEASE-MAPPO-M1-V1",
        "independent_unit": "training_seed",
        "arms": list(arms),
        "training_seeds": args.seeds,
        "reliability_bands": ["r0.25", "r0.90"],
        "interpretation_boundary": "M1 is a development pilot. Paired deltas compare identical training-seed labels but are not a substitute for future independent formal cohorts.",
    }
    (args.output / "PSCR_RC_M1_MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
