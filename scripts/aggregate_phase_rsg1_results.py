"""Aggregate the nine completed RSG-1 cells without changing their results."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np

from run_phase_rsg1_development_smoke import METHODS, PROTOCOL, SEEDS, write_csv


def read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def f(row: dict, key: str) -> float:
    return float(row[key])


def aggregate(output_root: Path) -> dict:
    expected = [(method, seed) for method in METHODS for seed in SEEDS]
    manifests, all_raw, all_bias, summary = [], [], [], []
    for method, seed in expected:
        run_dir = output_root / "runs" / method / f"seed{seed}"
        manifest_path = run_dir / "run_manifest.json"
        if not manifest_path.exists():
            raise FileNotFoundError(manifest_path)
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("status") != "completed":
            raise RuntimeError(f"incomplete run: {method}/seed{seed}")
        train_log = run_dir / "train_log.csv"
        if len(read_csv(train_log)) != 782:
            raise RuntimeError(f"train log is not 782 updates: {train_log}")
        raw = read_csv(run_dir / "raw_episode_metrics.csv")
        bias = read_csv(run_dir / "bias_telemetry.csv")
        if len(raw) != 200:
            raise RuntimeError(f"raw episode row count is not 200: {run_dir}")
        if len({int(row["development_episode_id"]) for row in raw}) != 100:
            raise RuntimeError(f"evaluation tape mismatch: {run_dir}")
        all_raw.extend(raw)
        all_bias.extend(bias)
        nominal = {int(row["development_episode_id"]): row for row in raw
                   if row["condition"] == "nominal"}
        failures = [row for row in raw if row["condition"] == "relay_failure"]
        deltas = [f(nominal[int(row["development_episode_id"])], "J") - f(row, "J")
                  for row in failures]
        summary.append({
            "method": method, "train_seed": seed, "episodes": len(failures),
            "J_nominal_mean": float(np.mean([f(nominal[int(row["development_episode_id"])], "J") for row in failures])),
            "J_failure_mean": float(np.mean([f(row, "J") for row in failures])),
            "delta_J_mean": float(np.mean(deltas)),
            "success_nominal_mean": float(np.mean([f(nominal[int(row["development_episode_id"])], "success_at_horizon") for row in failures])),
            "success_failure_mean": float(np.mean([f(row, "success_at_horizon") for row in failures])),
            "collision_nominal_mean": float(np.mean([f(nominal[int(row["development_episode_id"])], "collision") for row in failures])),
            "collision_failure_mean": float(np.mean([f(row, "collision") for row in failures])),
            "timeout_nominal_mean": float(np.mean([f(nominal[int(row["development_episode_id"])], "timeout") for row in failures])),
            "timeout_failure_mean": float(np.mean([f(row, "timeout") for row in failures])),
            "constraint_nominal_mean": float(np.mean([f(nominal[int(row["development_episode_id"])], "constraint_violation") for row in failures])),
            "constraint_failure_mean": float(np.mean([f(row, "constraint_violation") for row in failures])),
        })
        manifests.append(manifest)
    write_csv(output_root / "raw_episode_metrics.csv", all_raw)
    write_csv(output_root / "bias_telemetry.csv", all_bias)
    write_csv(output_root / "per_seed_summary.csv", summary)
    result = {
        "protocol": PROTOCOL, "status": "completed", "formal_training": True,
        "methods": list(METHODS), "seeds": list(SEEDS),
        "environment_steps_per_run": 782 * 4 * 64,
        "tape_start": 340000, "episodes_per_condition": 100,
        "checkpoint_selection": "fixed_final_update_only", "manifests": manifests,
        "bias_telemetry_rows": len(all_bias), "parallel_cells": len(expected),
    }
    (output_root / "manifest.json").write_text(
        json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8"
    )
    print(json.dumps({"status": "completed", "output_root": str(output_root),
                      "cells": len(expected), "bias_rows": len(all_bias)}, indent=2))
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path,
                        default=Path("results/development/phase_rsg1_development_smoke"))
    args = parser.parse_args()
    aggregate(args.output_root)


if __name__ == "__main__":
    main()
