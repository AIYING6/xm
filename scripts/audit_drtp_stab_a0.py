"""Read-only DRTP A0 weight-log analyzer.

This script is deliberately offline: it accepts historical sampler CSV logs,
extracts only ``weight_update`` rows, and writes descriptive dynamics metrics.
It never imports the environment, checkpoint, or PPO trainer.
"""
from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path


GROUPS = ("F0", "TE", "TL", "DS", "DL", "CP")


def percentile(values: list[float], fraction: float) -> float:
    if not values:
        return float("nan")
    ordered = sorted(values)
    index = (len(ordered) - 1) * fraction
    lower, upper = math.floor(index), math.ceil(index)
    return ordered[lower] if lower == upper else ordered[lower] + (ordered[upper] - ordered[lower]) * (index - lower)


def read_rows(path: Path) -> list[tuple[int, list[float]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = csv.DictReader(handle)
        output = []
        for row in rows:
            if row.get("record_type") != "weight_update":
                continue
            output.append((int(row["update"]), [float(row[f"q_{group}"]) for group in GROUPS]))
    return output


def summarize(seed: str, rows: list[tuple[int, list[float]]]) -> dict[str, str | float | int]:
    if len(rows) < 2:
        return {"seed": seed, "weight_updates": len(rows), "status": "insufficient_weight_updates"}
    vectors = [vector for _, vector in rows]
    jumps = [sum(abs(a - b) for a, b in zip(current, previous)) for previous, current in zip(vectors, vectors[1:])]
    accelerations = [abs(current - previous) for previous, current in zip(jumps, jumps[1:])]
    top_groups = [GROUPS[max(range(len(GROUPS)), key=lambda i: vector[i])] for vector in vectors]
    entropy = [-sum(value * math.log(value) for value in vector if value > 0) for vector in vectors]
    return {
        "seed": seed,
        "status": "ok",
        "weight_updates": len(rows),
        "first_update": rows[0][0],
        "last_update": rows[-1][0],
        "dw_mean": sum(jumps) / len(jumps),
        "dw_median": percentile(jumps, 0.5),
        "dw_p90": percentile(jumps, 0.9),
        "dw_p95": percentile(jumps, 0.95),
        "dw_max": max(jumps),
        "tv_weight": sum(jumps),
        "weight_entropy_min": min(entropy),
        "weight_entropy_mean": sum(entropy) / len(entropy),
        "max_group_dominance": max(max(vector) for vector in vectors),
        "top1_switches": sum(a != b for a, b in zip(top_groups, top_groups[1:])),
        "acceleration_mean": (sum(accelerations) / len(accelerations)) if accelerations else 0.0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Read-only DRTP A0 sampler-log analyzer")
    parser.add_argument("--seed-log", action="append", default=[], metavar="SEED=CSV")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    results = []
    for item in args.seed_log:
        seed, separator, value = item.partition("=")
        if not separator or not seed or not value:
            raise ValueError("--seed-log requires SEED=CSV")
        results.append(summarize(seed, read_rows(Path(value))))
    fields = sorted({field for row in results for field in row}) or ["seed", "status"]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(results)


if __name__ == "__main__":
    main()
