"""Aggregate the pre-registered A0 OC-MAPPO development pilot.

The output is deliberately descriptive.  Three training seeds are a direction
gate, not a confirmatory estimate or a publishable statistical sample.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np


ARMS = ("plain", "oc", "shuffled_oc")
SEEDS = (99511, 99512, 99513)
METRICS = (
    "mean_return",
    "mean_estimation_error",
    "mean_final_logdet",
    "mean_near_collision_steps",
    "mean_distance",
    "mean_measurement_count",
)


def last_training_row(path: Path) -> dict[str, str]:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 128:
        raise ValueError(f"expected 128 updates in {path}, found {len(rows)}")
    return rows[-1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("refusing to aggregate without --execute")
    if not (args.root / "run_contract.json").is_file() or not (args.root / "evaluation_plan.json").is_file():
        raise FileNotFoundError("missing frozen run contract or pre-evaluation plan")

    rows: list[dict[str, object]] = []
    telemetry: list[dict[str, object]] = []
    for arm in ARMS:
        for seed in SEEDS:
            run = args.root / f"{arm}_seed{seed}"
            summary_path = run / "eval" / "summary.json"
            if not summary_path.is_file():
                raise FileNotFoundError(summary_path)
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            if summary.get("episodes") != 64.0:
                raise ValueError(f"unexpected endpoint episode count in {summary_path}")
            train = last_training_row(run / "train_log.csv")
            rows.append({"arm": arm, "training_seed": seed, **{key: float(summary[key]) for key in METRICS}})
            telemetry.append({
                "arm": arm,
                "training_seed": seed,
                "final_credit_mean": float(train["credit_mean"]),
                "final_credit_std": float(train["credit_std"]),
                "final_credit_positive_fraction": float(train["credit_positive_fraction"]),
                "final_credit_actor_adv_correlation": train["credit_actor_adv_correlation"],
            })

    by_key = {(str(row["arm"]), int(row["training_seed"])): row for row in rows}
    deltas: list[dict[str, object]] = []
    for seed in SEEDS:
        oc = by_key[("oc", seed)]
        for comparator in ("plain", "shuffled_oc"):
            ref = by_key[(comparator, seed)]
            delta = {"training_seed": seed, "candidate": "oc", "comparator": comparator}
            delta.update({f"delta_{metric}": float(oc[metric]) - float(ref[metric]) for metric in METRICS})
            deltas.append(delta)

    nondegenerate = all(
        float(row["final_credit_std"]) > 0.0 and float(row["final_credit_positive_fraction"]) > 0.0
        for row in telemetry if row["arm"] in {"oc", "shuffled_oc"}
    )
    plain_zero = all(
        float(row["final_credit_std"]) == 0.0 and float(row["final_credit_positive_fraction"]) == 0.0
        for row in telemetry if row["arm"] == "plain"
    )
    report = {
        "protocol": "A0-OC-MAPPO-METHOD-PILOT-V1",
        "verdict": "A0_OC_METHOD_PILOT_REPORTED",
        "development_only": True,
        "training_seeds": list(SEEDS),
        "checks": {
            "all_nine_endpoints_present": len(rows) == 9,
            "fixed_64_episode_evaluation": True,
            "oc_and_shuffled_telemetry_nondegenerate": nondegenerate,
            "plain_credit_is_zero": plain_zero,
        },
        "interpretation_limit": "Descriptive three-seed direction gate only. No confirmatory claim or automatic scale-up follows.",
    }
    for filename, data in (("per_seed_endpoint_summary.csv", rows), ("credit_telemetry_summary.csv", telemetry), ("paired_oc_deltas.csv", deltas)):
        with (args.root / filename).open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(data[0]))
            writer.writeheader(); writer.writerows(data)
    (args.root / "A0_OC_METHOD_PILOT_REPORT.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
