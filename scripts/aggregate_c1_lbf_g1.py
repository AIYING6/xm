"""Aggregate the frozen C1 G1 baseline and issue its pre-registered gate."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

TRAINING_SEEDS = (91011, 91012, 91013)
PROTOCOL = "C1-LBF-G1-MATCHED-MAPPO-V1"


def read_summary(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("protocol") != PROTOCOL:
        raise ValueError(f"unexpected protocol in {path}")
    return data


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("refusing to aggregate without --execute")
    if (args.root / "G1_VERDICT.json").exists():
        raise FileExistsError("refusing to overwrite a G1 verdict")
    random_summary = read_summary(args.root / "random_reference" / "summary.json")
    random_completion = float(random_summary["mean_completed_foods"])
    rows = []
    for seed in TRAINING_SEEDS:
        summary = read_summary(args.root / "runs" / f"seed{seed}" / "endpoint" / "summary.json")
        completion = float(summary["mean_completed_foods"])
        rows.append({"seed": seed, **summary, "completion_gain_over_random": completion - random_completion})
    learnable_count = sum(row["completion_gain_over_random"] >= 0.25 for row in rows)
    mean_completion = sum(float(row["mean_completed_foods"]) for row in rows) / len(rows)
    learnable = learnable_count >= 2
    not_saturated = mean_completion < 1.90
    verdict = "C1_LBF_G1_PASS" if learnable and not_saturated else "C1_LBF_G1_STOP"
    with (args.root / "G1_PER_SEED.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys()); writer.writeheader(); writer.writerows(rows)
    report = {
        "protocol": PROTOCOL,
        "verdict": verdict,
        "training_started": True,
        "method_started": False,
        "random_reference_completion": random_completion,
        "checks": {
            "learnable_two_of_three": learnable,
            "learnable_seed_count": learnable_count,
            "not_saturated": not_saturated,
            "mean_endpoint_completed_foods": mean_completion,
        },
        "boundary": "G1 only establishes learnability/non-saturation of the public task. It neither validates capability-posterior inference nor authorizes a method claim.",
    }
    (args.root / "G1_VERDICT.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
