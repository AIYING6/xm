"""Aggregate four isolated M2 cloud runs without rerunning any evaluation."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

TRAIN_SEEDS = (9201, 9202)


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--root", type=Path, required=True); args = parser.parse_args()
    rows = []
    for method in ("full", "b1"):
        for seed in TRAIN_SEEDS:
            path = args.root / f"{method}_seed{seed}" / "summary.csv"
            if not path.exists(): raise FileNotFoundError(path)
            with path.open(newline="", encoding="utf-8") as handle: rows.extend(csv.DictReader(handle))
    summary = [{key: (int(value) if key in {"training_seed", "episodes", "evidence_episodes"} else float(value) if key not in {"method"} else value) for key, value in row.items()} for row in rows]
    mechanisms = []
    for seed in TRAIN_SEEDS:
        full = next(row for row in summary if row["training_seed"] == seed and row["method"] == "full")
        b1 = next(row for row in summary if row["training_seed"] == seed and row["method"] == "b1")
        mechanisms.append(full["acquisition_given_evidence"] > b1["acquisition_given_evidence"] and full["evidence_to_range_latency"] < b1["evidence_to_range_latency"] and full["no_attack_range_acquisition_fraction"] < b1["no_attack_range_acquisition_fraction"])
    mission = any(next(row for row in summary if row["training_seed"] == seed and row["method"] == "full")["neutralization_rate"] > next(row for row in summary if row["training_seed"] == seed and row["method"] == "b1")["neutralization_rate"] or next(row for row in summary if row["training_seed"] == seed and row["method"] == "full")["rmtn180"] < next(row for row in summary if row["training_seed"] == seed and row["method"] == "b1")["rmtn180"] for seed in TRAIN_SEEDS)
    verdict = "M2_PILOT_PASS__ACQUISITION_MECHANISM_SIGNAL_ESTABLISHED__READY_FOR_FORMAL_PROTOCOL" if all(mechanisms) and mission else ("M2_PILOT_PARTIAL__SIGNAL_UNSTABLE__DIAGNOSE_EXISTING_RUNS_ONLY" if any(mechanisms) else "M2_PILOT_NO_GO__ACQUISITION_CONDITIONING_NOT_SUPPORTED")
    payload = {"verdict": verdict, "summary": summary, "mechanism_improvement_by_seed": dict(zip(map(str, TRAIN_SEEDS), mechanisms)), "performance_use_prohibited": True}
    (args.root / "PILOT_VERDICT.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__": main()
