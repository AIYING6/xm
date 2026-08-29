"""Evaluate the nine frozen S1 final checkpoints on the development-only tape."""
from __future__ import annotations

import argparse
import csv
import json
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]
import run_drtp_sg_development_evaluation as base  # noqa: E402

PROTOCOL = "DRTP-STABILIZATION-S1-STAGE1-EVALUATION-V1"
ARMS, SEEDS = ("utr_sg", "drtp_sg", "drtp_tr_sg"), (2901, 2902, 2903)
TAPE = ROOT / "configs" / "drtp_stabilization_s1_development_tape.json"


def mean(rows: list[dict], key: str) -> float:
    return sum(float(row[key]) for row in rows) / len(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute or args.workers != 6:
        raise SystemExit("S1 requires --execute and exactly 6 workers")
    tape = json.loads(TAPE.read_text(encoding="utf-8"))
    target = args.output_root / "evaluations" / "final_05m"
    if target.exists() and any(target.iterdir()):
        raise FileExistsError(f"refusing overwrite: {target}")
    target.mkdir(parents=True, exist_ok=False)
    tasks, manifests = [], []
    for arm in ARMS:
        for seed in SEEDS:
            run = args.output_root / "runs" / arm / f"seed{seed}"
            manifest = json.loads((run / "run_manifest.json").read_text(encoding="utf-8"))
            if (manifest.get("status") != "completed" or manifest.get("protocol") != "DRTP-STABILIZATION-S1-STAGE1-V1"
                    or manifest.get("seed") != seed or manifest.get("updates") != 1953
                    or manifest.get("tape_hash") != tape["tape_hash"]):
                raise RuntimeError(f"invalid S1 source run: {run}")
            checkpoint = run / "actor_critic_latest.pt"
            for condition in tape["conditions"]:
                tasks.append((arm, seed, str(checkpoint), "500k", tape["episode_ids"], [condition], tape["tape_hash"]))
            manifests.append(manifest)
    total, done, rows = len(tasks) * len(tape["episode_ids"]), 0, []
    print(f"S1 evaluation: workers=6, cells={len(tasks)}, episodes={total}", flush=True)
    with ProcessPoolExecutor(max_workers=6, mp_context=mp.get_context("spawn")) as pool:
        futures = [pool.submit(base.evaluate_cell, task) for task in tasks]
        for future in as_completed(futures):
            part = future.result()
            rows.extend(part); done += len(part)
            print(f"S1 evaluation progress {done}/{total} ({100 * done / total:.2f}%)", flush=True)
    order = {condition["name"]: index for index, condition in enumerate(tape["conditions"])}
    rows.sort(key=lambda row: (row["method"], int(row["train_seed"]), order[row["topology_condition"]], int(row["development_episode_id"])))
    if len(rows) != total:
        raise RuntimeError(f"S1 raw row count {len(rows)} != {total}")
    with (target / "raw_episode_metrics.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    summary = []
    for arm in ARMS:
        for seed in SEEDS:
            for condition in tape["conditions"]:
                subset = [row for row in rows if row["method"] == arm and int(row["train_seed"]) == seed
                          and row["topology_condition"] == condition["name"]]
                if len(subset) != len(tape["episode_ids"]):
                    raise RuntimeError(f"incomplete S1 cell: {arm}/seed{seed}/{condition['name']}")
                summary.append({"method": arm, "train_seed": seed, "condition": condition["name"],
                                "J": mean(subset, "J"), "collision": mean(subset, "collision"),
                                "timeout": mean(subset, "timeout"),
                                "constraint_violation": mean(subset, "constraint_violation"),
                                "failure_exposed": mean(subset, "failure_exposed")})
    with (target / "per_seed_condition_summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary[0])); writer.writeheader(); writer.writerows(summary)
    manifest = {"protocol": PROTOCOL, "status": "completed", "raw_rows": len(rows), "cells": len(tasks),
                "episodes_per_condition": len(tape["episode_ids"]), "workers": 6, "tape_hash": tape["tape_hash"],
                "source_runs": manifests, "all_original_episodes_retained": True,
                "automatic_follow_on_started": False}
    (target / "evaluation_manifest.json").write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
