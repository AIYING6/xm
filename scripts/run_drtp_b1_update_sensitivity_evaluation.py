"""Evaluate frozen B1 branch horizons on one development-only tape."""
from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import json
import multiprocessing as mp
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]
import run_drtp_sg_development_evaluation as base  # noqa: E402
from run_drtp_b1_update_sensitivity_branch import (  # noqa: E402
    ARMS, BRANCHES, COHORTS, FAMILIES, PROTOCOL as TRAIN_PROTOCOL,
)


PROTOCOL = "DRTP-B1-UPDATE-SENSITIVITY-EVALUATION-V1"
TAPE = ROOT / "configs" / "drtp_b1_update_sensitivity_tape.json"
HORIZONS = ("u016", "u064")
PERTURBATIONS = ("F0_44_80", "T28_28_80", "D120_44_120", "C28_120")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def evaluate(task: tuple) -> list[dict]:
    metadata, base_task = task
    rows = base.evaluate_cell(base_task)
    for row in rows:
        row.update(metadata)
        row["protocol"] = PROTOCOL
        row["independent_unit"] = "source_training_seed"
        row["technical_repetition"] = "rng_branch_x_evaluation_episode"
    return rows


def mean(rows: list[dict], key: str) -> float:
    return sum(float(row[key]) for row in rows) / len(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=20)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute or args.workers < 1:
        raise SystemExit("--execute and positive --workers are required")
    tape = json.loads(TAPE.read_text(encoding="utf-8"))
    target = args.output_root / "evaluations" / "branch_horizons"
    if target.exists():
        raise FileExistsError(f"refusing B1 evaluation rerun: {target}")
    target.mkdir(parents=True, exist_ok=False)
    tasks = []
    for cohort, seeds in COHORTS.items():
        for arm in ARMS:
            for seed in seeds:
                for family in FAMILIES:
                    for branch in BRANCHES:
                        run = args.output_root / "branches" / cohort / arm / f"seed{seed}" / family / f"branch{branch}"
                        manifest = json.loads((run / "branch_manifest.json").read_text(encoding="utf-8"))
                        if manifest.get("status") != "completed" or manifest.get("protocol") != TRAIN_PROTOCOL:
                            raise RuntimeError(f"invalid B1 branch: {run}")
                        for horizon in HORIZONS:
                            checkpoint = run / f"actor_critic_milestone_{horizon}.pt"
                            metadata = {"cohort": cohort, "family": family, "branch": branch, "horizon": horizon}
                            base_task = (
                                arm, seed, str(checkpoint), horizon,
                                tape["episode_ids"], tape["conditions"], sha256(TAPE),
                            )
                            tasks.append((metadata, base_task))
    workers = min(args.workers, len(tasks))
    total = len(tasks) * len(tape["episode_ids"]) * len(tape["conditions"])
    print(f"B1 branch evaluation: workers={workers}, cells={len(tasks)}, episodes={total}", flush=True)
    rows, completed = [], 0
    with ProcessPoolExecutor(max_workers=workers, mp_context=mp.get_context("spawn")) as pool:
        futures = [pool.submit(evaluate, task) for task in tasks]
        for future in as_completed(futures):
            part = future.result()
            rows.extend(part)
            completed += len(part)
            print(f"B1 branch evaluation progress {completed}/{total} ({100 * completed / total:.2f}%)", flush=True)
    if len(rows) != total:
        raise RuntimeError(f"expected {total} B1 evaluation rows, found {len(rows)}")
    rows.sort(key=lambda row: (
        row["cohort"], row["method"], int(row["train_seed"]), row["family"],
        int(row["branch"]), row["horizon"], row["topology_condition"], int(row["development_episode_id"]),
    ))
    with (target / "raw_episode_metrics.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    grouped: dict[tuple, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[(row["cohort"], row["method"], int(row["train_seed"]), row["family"], int(row["branch"]), row["horizon"], row["topology_condition"])].append(row)
    summary = []
    for key, part in sorted(grouped.items()):
        cohort, arm, seed, family, branch, horizon, condition = key
        summary.append({
            "cohort": cohort, "arm": arm, "seed": seed, "family": family,
            "branch": branch, "horizon": horizon, "condition": condition,
            "J": mean(part, "J"), "collision": mean(part, "collision"),
            "timeout": mean(part, "timeout"), "constraint_violation": mean(part, "constraint_violation"),
        })
    with (target / "per_branch_condition_summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary[0]))
        writer.writeheader(); writer.writerows(summary)
    manifest = {
        "protocol": PROTOCOL, "status": "completed", "raw_rows": len(rows),
        "cells": len(tasks), "workers": workers, "tape_sha256": sha256(TAPE),
        "checkpoint_promotion": False, "independent_unit": "source_training_seed",
    }
    (target / "evaluation_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
