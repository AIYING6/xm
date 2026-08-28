"""Evaluate the six Mechanism V1 final checkpoints on the frozen diagnostic tape."""
from __future__ import annotations

import argparse
import csv
from concurrent.futures import ProcessPoolExecutor, as_completed
import json
import multiprocessing as mp
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import run_drtp_sg_development_evaluation as base  # noqa: E402


PROTOCOL = "DRTP-TRAINING-FAILURE-MECHANISM-V1-EVALUATION"
ARMS = ("utr_sg", "drtp_sg")
SEEDS = (2601, 2602, 2603)


def evaluate(task: tuple) -> list[dict]:
    rows = base.evaluate_cell(task)
    for row in rows:
        row["protocol"] = PROTOCOL
        row["inference_unit"] = "training_seed"
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("NO-GO: --execute is required")
    tape = json.loads((ROOT / "diagnostics/drtp_mechanism_v1/03_tape/tape_manifest.json").read_text(encoding="utf-8"))
    eval_root = args.output_root / "evaluations" / "final_1m"
    if eval_root.exists() and any(eval_root.iterdir()):
        raise FileExistsError(f"refusing to overwrite: {eval_root}")
    eval_root.mkdir(parents=True, exist_ok=False)
    episode_ids = [int(item["episode_id"]) for item in tape["episodes"]]
    tasks, source = [], []
    for arm in ARMS:
        for seed in SEEDS:
            run_dir = args.output_root / "runs" / arm / f"seed{seed}"
            manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))
            checks = {
                "completed": manifest.get("status") == "completed",
                "protocol": manifest.get("protocol") == "DRTP-TRAINING-FAILURE-MECHANISM-V1",
                "seed": manifest.get("seed") == seed,
                "parameter_count": manifest.get("parameter_count") == 116728,
                "telemetry": manifest.get("failure_aware_telemetry") is True,
                "tape_hash": manifest.get("tape_hash") == tape["tape_hash"],
                "no_canonical": manifest.get("canonical_seeds_used") is False,
            }
            if not all(checks.values()):
                raise RuntimeError(f"training provenance violation in {run_dir}: {checks}")
            checkpoint = run_dir / "actor_critic_latest.pt"
            if not checkpoint.exists():
                raise FileNotFoundError(checkpoint)
            tasks.append((arm, seed, str(checkpoint), "1m", episode_ids, tape["conditions"], tape["tape_hash"]))
            source.append(manifest)
    workers = min(args.workers, len(tasks))
    total = len(tasks) * len(tape["conditions"]) * len(episode_ids)
    print(f"mechanism evaluation: workers={workers}, cells={len(tasks)}, episodes={total}", flush=True)
    rows, completed = [], 0
    with ProcessPoolExecutor(max_workers=workers, mp_context=mp.get_context("spawn")) as pool:
        futures = [pool.submit(evaluate, task) for task in tasks]
        for future in as_completed(futures):
            part = future.result()
            rows.extend(part)
            completed += len(part)
            print(f"mechanism evaluation progress {completed}/{total} ({100 * completed / total:.2f}%)", flush=True)
    condition_order = {item["name"]: index for index, item in enumerate(tape["conditions"])}
    rows.sort(key=lambda row: (row["method"], int(row["train_seed"]), condition_order[row["topology_condition"]], int(row["development_episode_id"])))
    if len(rows) != total:
        raise RuntimeError(f"expected {total} rows, found {len(rows)}")
    with (eval_root / "raw_episode_metrics.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    manifest = {
        "protocol": PROTOCOL, "status": "completed", "tape_hash": tape["tape_hash"],
        "episodes_per_condition": tape["episodes_per_condition"], "conditions": tape["conditions"],
        "raw_rows": len(rows), "cells": len(tasks), "workers": workers,
        "source_runs": source, "inference_unit": "training_seed", "checkpoint_label": "1m",
        "all_original_episodes_retained": True, "canonical_seeds_used": False,
    }
    (eval_root / "evaluation_manifest.json").write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2, default=str))


if __name__ == "__main__":
    main()
