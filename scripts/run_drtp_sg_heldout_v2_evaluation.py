"""Uniform final-checkpoint evaluation for authorized DRTP held-out v2 runs."""
from __future__ import annotations

import argparse
import csv
from concurrent.futures import ProcessPoolExecutor, as_completed
import json
import math
import multiprocessing as mp
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import run_drtp_sg_development_evaluation as base  # noqa: E402
from run_drtp_sg_heldout_v2_single import ARMS, PROTOCOL as TRAIN_PROTOCOL, SEEDS  # noqa: E402


PROTOCOL = "DRTP-SG-MAPPO-HELDOUT-CONFIRMATION-V2-EVALUATION-V1"
FINAL_LABEL = "10m"


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def finite_mean(rows: list[dict], key: str) -> float:
    values = [float(row[key]) for row in rows if math.isfinite(float(row[key]))]
    return sum(values) / len(values) if values else math.nan


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("NO-GO: explicit --execute is required")
    if args.workers < 1:
        raise ValueError("workers must be positive")
    tape = json.loads((args.output_root / "heldout_tape_manifest.json").read_text(encoding="utf-8"))
    if tape.get("episode_ids") != list(range(430000, 430100)) or tape.get("canonical") is not False:
        raise RuntimeError("invalid frozen v2 held-out tape")
    eval_root = args.output_root / "evaluations" / "heldout_v2"
    if eval_root.exists() and any(eval_root.iterdir()):
        raise FileExistsError(f"refusing to overwrite: {eval_root}")
    eval_root.mkdir(parents=True, exist_ok=False)
    tasks, source_manifests = [], []
    for arm in ARMS:
        for seed in SEEDS:
            run_dir = args.output_root / "runs" / arm / f"seed{seed}"
            manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))
            checks = {
                "status": manifest.get("status") == "completed",
                "protocol": manifest.get("protocol") == TRAIN_PROTOCOL,
                "parameter_count": manifest.get("parameter_count") == 116728,
                "from_scratch": manifest.get("from_scratch") is True,
                "strict_continuous": manifest.get("strict_continuous_trajectory") is True,
                "no_warm_restart": manifest.get("warm_restart_used") is False,
                "no_runtime_resume": manifest.get("runtime_resume_used") is False,
                "runtime_persistence": manifest.get("runtime_state_checkpointing") is True,
                "held_out": manifest.get("held_out_seeds_used") is True,
                "no_canonical": manifest.get("canonical_seeds_used") is False,
            }
            if not all(checks.values()):
                raise RuntimeError(f"v2 held-out run contract violation in {run_dir}: {checks}")
            checkpoint = run_dir / "actor_critic_latest.pt"
            if not checkpoint.exists():
                raise FileNotFoundError(checkpoint)
            tasks.append((arm, seed, str(checkpoint), FINAL_LABEL, tape["episode_ids"], tape["conditions"], tape["tape_hash"]))
            source_manifests.append(manifest)
    workers = min(args.workers, len(tasks))
    total = len(tasks) * len(tape["conditions"]) * len(tape["episode_ids"])
    print(f"held-out v2 evaluation: workers={workers}, cells={len(tasks)}, episodes={total}", flush=True)
    raw_rows, completed = [], 0
    context = mp.get_context("spawn")
    with ProcessPoolExecutor(max_workers=workers, mp_context=context) as pool:
        futures = [pool.submit(base.evaluate_cell, task) for task in tasks]
        for future in as_completed(futures):
            rows = future.result()
            for row in rows:
                row["protocol"] = PROTOCOL
                row["inference_unit"] = "training_seed"
            raw_rows.extend(rows); completed += len(rows)
            print(f"held-out v2 evaluation progress {completed}/{total} ({100 * completed / total:.1f}%)", flush=True)
    condition_order = {item["name"]: index for index, item in enumerate(tape["conditions"])}
    raw_rows.sort(key=lambda row: (row["method"], int(row["train_seed"]), condition_order[row["topology_condition"]], int(row["development_episode_id"])))
    write_csv(eval_root / "raw_episode_metrics.csv", raw_rows)
    grouped: dict[tuple[str, int, str], list[dict]] = {}
    for row in raw_rows:
        grouped.setdefault((row["method"], int(row["train_seed"]), row["topology_condition"]), []).append(row)
    summary = []
    for arm in ARMS:
        for seed in SEEDS:
            for condition in condition_order:
                rows = grouped[(arm, seed, condition)]
                summary.append({
                    "arm": arm, "seed": seed, "checkpoint_label": FINAL_LABEL, "condition": condition,
                    "J": finite_mean(rows, "J"), "collision": finite_mean(rows, "collision"),
                    "timeout": finite_mean(rows, "timeout"), "constraint_violation": finite_mean(rows, "constraint_violation"),
                    "failure_exposure": finite_mean(rows, "failure_exposed"), "episode_length": finite_mean(rows, "terminal_step"),
                    "path_switch_count": finite_mean(rows, "path_switch_count"),
                    "direct_path_fraction": finite_mean(rows, "direct_path_fraction_during_failure"),
                    "relay_path_fraction": finite_mean(rows, "relay_path_fraction_during_failure"),
                    "task_support_fraction": finite_mean(rows, "task_support_fraction_during_failure"),
                    "legal_information_fraction": finite_mean(rows, "legal_information_fraction_during_failure"),
                    "mean_cache_age": finite_mean(rows, "mean_cache_age_during_failure"),
                })
    write_csv(eval_root / "per_seed_condition_summary.csv", summary)
    manifest = {
        "protocol": PROTOCOL, "status": "completed", "tape_hash": tape["tape_hash"], "tape_start": 430000,
        "episodes_per_condition": 100, "checkpoint_label": FINAL_LABEL, "raw_rows": len(raw_rows),
        "cells": len(tasks), "workers": workers, "source_runs": source_manifests,
        "inference_unit": "training_seed", "canonical_seeds_used": False, "development_tape_used": False,
    }
    (eval_root / "evaluation_manifest.json").write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2, default=str))


if __name__ == "__main__":
    main()
