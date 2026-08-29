"""Evaluate the nine frozen Stable-v2 final-0.5M checkpoints; never train."""
from __future__ import annotations

import argparse
import csv
from concurrent.futures import ProcessPoolExecutor, as_completed
import json
import multiprocessing as mp
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]
import run_drtp_sg_development_evaluation as base  # noqa: E402


PROTOCOL = "DRTP-STABLE-V2-PILOT-EVALUATION-V1"
ARMS = ("utr_sg", "drtp_sg", "drtp_klr_sg")
SEEDS = (3101, 3102, 3103)
TAPE = ROOT / "configs" / "drtp_stable_v2_pilot_tape.json"


def average(rows: list[dict], key: str) -> float:
    return sum(float(row[key]) for row in rows) / len(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=9)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute or args.workers != 9:
        raise SystemExit("Stable-v2 pilot freezes exactly 9 evaluation workers")
    tape = json.loads(TAPE.read_text(encoding="utf-8"))
    target = args.output_root / "evaluations" / "final_05m"
    if target.exists():
        raise FileExistsError(f"refusing evaluation overwrite/rerun: {target}")
    target.mkdir(parents=True, exist_ok=False)
    tasks, manifests = [], []
    for arm in ARMS:
        for seed in SEEDS:
            run = args.output_root / "runs" / arm / f"seed{seed}"
            manifest = json.loads((run / "run_manifest.json").read_text(encoding="utf-8"))
            if (
                manifest.get("status") != "completed"
                or manifest.get("protocol") != "DRTP-STABLE-V2-PILOT-STAGE1-V1"
                or manifest.get("seed") != seed
                or manifest.get("updates") != 1953
                or manifest.get("environment_steps") != 499968
                or manifest.get("tape_hash") != tape["tape_hash"]
            ):
                raise RuntimeError(f"invalid Stable-v2 source run: {run}")
            checkpoint = run / "actor_critic_latest.pt"
            for condition in tape["conditions"]:
                tasks.append((arm, seed, str(checkpoint), "500k", tape["episode_ids"], [condition], tape["tape_hash"]))
            manifests.append(manifest)
    total = len(tasks) * len(tape["episode_ids"])
    done, rows = 0, []
    print(f"Stable-v2 pilot evaluation: workers=9, cells={len(tasks)}, episodes={total}", flush=True)
    with ProcessPoolExecutor(max_workers=9, mp_context=mp.get_context("spawn")) as pool:
        futures = [pool.submit(base.evaluate_cell, task) for task in tasks]
        for future in as_completed(futures):
            part = future.result()
            rows.extend(part)
            done += len(part)
            print(f"Stable-v2 pilot evaluation progress {done}/{total} ({100 * done / total:.2f}%)", flush=True)
    order = {condition["name"]: index for index, condition in enumerate(tape["conditions"])}
    rows.sort(key=lambda row: (
        row["method"], int(row["train_seed"]), order[row["topology_condition"]],
        int(row["development_episode_id"]),
    ))
    if len(rows) != total:
        raise RuntimeError(f"raw row count {len(rows)} != {total}")
    with (target / "raw_episode_metrics.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    summary = []
    for arm in ARMS:
        for seed in SEEDS:
            for condition in tape["conditions"]:
                subset = [
                    row for row in rows
                    if row["method"] == arm
                    and int(row["train_seed"]) == seed
                    and row["topology_condition"] == condition["name"]
                ]
                if len(subset) != 100:
                    raise RuntimeError(f"incomplete evaluation cell: {arm}/seed{seed}/{condition['name']}")
                summary.append({
                    "method": arm,
                    "train_seed": seed,
                    "condition": condition["name"],
                    "J": average(subset, "J"),
                    "collision": average(subset, "collision"),
                    "timeout": average(subset, "timeout"),
                    "constraint_violation": average(subset, "constraint_violation"),
                    "failure_exposed": average(subset, "failure_exposed"),
                })
    with (target / "per_seed_condition_summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary[0]))
        writer.writeheader()
        writer.writerows(summary)
    payload = {
        "protocol": PROTOCOL,
        "status": "completed",
        "raw_rows": len(rows),
        "cells": len(tasks),
        "episodes_per_condition": 100,
        "workers": 9,
        "tape_hash": tape["tape_hash"],
        "source_runs": manifests,
        "all_original_episodes_retained": True,
        "checkpoint_promotion": False,
        "automatic_follow_on_started": False,
    }
    (target / "evaluation_manifest.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
