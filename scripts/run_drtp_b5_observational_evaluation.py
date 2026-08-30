"""Evaluate every frozen B5 milestone on the independent diagnostic tape."""
from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
import json
import multiprocessing as mp
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]
import run_drtp_sg_development_evaluation as base  # noqa: E402


PROTOCOL = "DRTP-B5-OBSERVATIONAL-EVALUATION-V1"
TRAIN_PROTOCOL = "DRTP-B5-OBSERVATIONAL-COHORT-V1"
ARMS = ("utr_sg", "drtp_sg")
SEEDS = (3601, 3602, 3603, 3604, 3605)
LABELS = ("250k", "500k", "750k", "1m")
TAPE = ROOT / "configs" / "drtp_b5_observational_tape.json"


def evaluate(task: tuple) -> list[dict]:
    rows = base.evaluate_cell(task)
    for row in rows:
        row["protocol"] = PROTOCOL
        row["inference_unit"] = "training_seed"
    return rows


def mean(rows: list[dict], key: str) -> float:
    values = [float(row[key]) for row in rows]
    return sum(values) / len(values)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--workers", default=20, type=int)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute or args.workers < 1:
        raise SystemExit("--execute and positive --workers are required")
    tape = json.loads(TAPE.read_text(encoding="utf-8"))
    target = args.output_root / "evaluations" / "milestones_025m_to_1m"
    if target.exists():
        raise FileExistsError(f"refusing evaluation rerun: {target}")
    target.mkdir(parents=True, exist_ok=False)
    tasks, manifests = [], []
    for arm in ARMS:
        for seed in SEEDS:
            run = args.output_root / "runs" / arm / f"seed{seed}"
            manifest = json.loads((run / "run_manifest.json").read_text(encoding="utf-8"))
            checks = {
                "completed": manifest.get("status") == "completed",
                "protocol": manifest.get("protocol") == TRAIN_PROTOCOL,
                "seed": manifest.get("seed") == seed,
                "tape": manifest.get("tape_hash") == tape["tape_hash"],
                "credit": manifest.get("group_credit_telemetry") is True,
                "steps": manifest.get("environment_steps") == 1000192,
            }
            if not all(checks.values()):
                raise RuntimeError(f"invalid B5 run {run}: {checks}")
            for label in LABELS:
                checkpoint = run / f"actor_critic_milestone_{label}.pt"
                if not checkpoint.is_file():
                    raise FileNotFoundError(checkpoint)
                for condition in tape["conditions"]:
                    tasks.append((arm, seed, str(checkpoint), label, tape["episode_ids"], [condition], tape["tape_hash"]))
            manifests.append(manifest)
    workers = min(args.workers, len(tasks))
    total = len(tasks) * tape["episodes_per_condition"]
    print(f"B5 observational evaluation: workers={workers}, cells={len(tasks)}, episodes={total}", flush=True)
    rows, completed = [], 0
    with ProcessPoolExecutor(max_workers=workers, mp_context=mp.get_context("spawn")) as pool:
        futures = [pool.submit(evaluate, task) for task in tasks]
        for future in as_completed(futures):
            part = future.result()
            rows.extend(part)
            completed += len(part)
            print(f"B5 observational evaluation progress {completed}/{total} ({100 * completed / total:.2f}%)", flush=True)
    order = {condition["name"]: index for index, condition in enumerate(tape["conditions"])}
    rows.sort(key=lambda row: (
        row["method"], int(row["train_seed"]), LABELS.index(row["evaluation_budget"]),
        order[row["topology_condition"]], int(row["development_episode_id"]),
    ))
    if len(rows) != total:
        raise RuntimeError(f"expected {total} rows, found {len(rows)}")
    with (target / "raw_episode_metrics.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    grouped: dict[tuple, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[(row["method"], int(row["train_seed"]), row["evaluation_budget"], row["topology_condition"])].append(row)
    summary = []
    for arm in ARMS:
        for seed in SEEDS:
            for label in LABELS:
                for condition in order:
                    part = grouped[(arm, seed, label, condition)]
                    summary.append({
                        "arm": arm,
                        "seed": seed,
                        "checkpoint_label": label,
                        "condition": condition,
                        "J": mean(part, "J"),
                        "collision": mean(part, "collision"),
                        "timeout": mean(part, "timeout"),
                        "constraint_violation": mean(part, "constraint_violation"),
                        "task_support_fraction": mean(part, "task_support_fraction_during_failure"),
                        "legal_information_fraction": mean(part, "legal_information_fraction_during_failure"),
                        "mean_cache_age": mean(part, "mean_cache_age_during_failure"),
                    })
    with (target / "per_seed_condition_summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary[0]))
        writer.writeheader()
        writer.writerows(summary)
    manifest = {
        "protocol": PROTOCOL,
        "status": "completed",
        "tape_hash": tape["tape_hash"],
        "checkpoint_labels": LABELS,
        "raw_rows": len(rows),
        "cells": len(tasks),
        "workers": workers,
        "source_runs": manifests,
        "inference_unit": "training_seed",
        "checkpoint_promotion": False,
    }
    (target / "evaluation_manifest.json").write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
