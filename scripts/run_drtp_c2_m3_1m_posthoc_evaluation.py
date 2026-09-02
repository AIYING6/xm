"""Evaluate only the four frozen 1M-extension checkpoints on the existing development tape."""
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
import run_drtp_sg_development_evaluation as base

FREEZE = ROOT / "configs" / "drtp_c2_m3_1m_posthoc_evaluation_freeze.json"
TAPE = ROOT / "configs" / "drtp_c2_m3_posthoc_evaluation_tape.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_tape() -> dict:
    tape = json.loads(TAPE.read_text(encoding="utf-8"))
    tape["episode_ids"] = list(range(tape["episode_start"], tape["episode_start"] + tape["episode_count"]))
    tape["tape_hash"] = hashlib.sha256(json.dumps(tape, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return tape


def mean(rows: list[dict], key: str) -> float:
    return sum(float(row[key]) for row in rows) / len(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=15)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    freeze, tape = json.loads(FREEZE.read_text(encoding="utf-8")), load_tape()
    if not args.execute or not freeze["authorization"]["checkpoint_evaluation_authorized"]:
        raise SystemExit("frozen 1M checkpoint-evaluation authorization is required")
    if args.workers < 1:
        raise ValueError("workers must be positive")
    prior = args.output_root / "evaluations" / freeze["prior_evaluation_directory"] / "evaluation_manifest.json"
    if not prior.is_file():
        raise RuntimeError("the frozen 500k post-hoc evaluation is required before 1M evaluation")
    if json.loads(prior.read_text(encoding="utf-8")).get("tape_hash") != tape["tape_hash"]:
        raise RuntimeError("the 1M evaluation must reuse exactly the frozen 500k development tape")
    target = args.output_root / "evaluations" / freeze["new_evaluation_directory"]
    if target.exists():
        raise FileExistsError(f"refusing 1M post-hoc evaluation overwrite: {target}")
    target.mkdir(parents=True, exist_ok=False)

    tasks, sources = [], []
    milestones = list(freeze["new_milestones"].values())
    for arm in freeze["arms"]:
        for cohort, seeds in freeze["cohorts"].items():
            for seed in seeds:
                run = args.output_root / "runs" / arm / f"seed{seed}"
                base_manifest = json.loads((run / "run_manifest.json").read_text(encoding="utf-8"))
                extension = json.loads((run / "m3_1m_extension_manifest.json").read_text(encoding="utf-8"))
                checks = {
                    "base_completed": base_manifest.get("status") == "completed",
                    "base_protocol": base_manifest.get("protocol") == freeze["source_training_protocol"],
                    "extension_completed": extension.get("status") == "completed",
                    "extension_protocol": extension.get("protocol") == freeze["source_extension_protocol"],
                    "seed": int(extension.get("seed")) == seed,
                    "arm": extension.get("arm") == arm,
                    "training_evaluation_disabled": extension.get("evaluation_authorized") is False,
                }
                if not all(checks.values()):
                    raise RuntimeError(f"invalid 1M source {run}: {checks}")
                for label in milestones:
                    checkpoint = run / f"actor_critic_milestone_{label}.pt"
                    if not checkpoint.is_file():
                        raise FileNotFoundError(checkpoint)
                    for condition in tape["conditions"]:
                        tasks.append((arm, seed, str(checkpoint), label, tape["episode_ids"], [condition], tape["tape_hash"]))
                sources.append({"arm": arm, "seed": seed, "cohort": cohort, "extension_manifest_sha256": digest(run / "m3_1m_extension_manifest.json")})

    workers = min(args.workers, len(tasks))
    total, done, rows = len(tasks) * len(tape["episode_ids"]), 0, []
    print(f"M3 1M post-hoc evaluation: workers={workers}, cells={len(tasks)}, episodes={total}", flush=True)
    with ProcessPoolExecutor(max_workers=workers, mp_context=mp.get_context("spawn")) as pool:
        futures = [pool.submit(base.evaluate_cell, task) for task in tasks]
        for future in as_completed(futures):
            result = future.result()
            rows.extend(result)
            done += len(result)
            print(f"M3 1M post-hoc evaluation progress {done}/{total} ({100 * done / total:.2f}%)", flush=True)
    if len(rows) != total:
        raise RuntimeError(f"incomplete M3 1M evaluation: {len(rows)}/{total}")
    condition_order = {row["name"]: index for index, row in enumerate(tape["conditions"])}
    rows.sort(key=lambda row: (row["method"], int(row["train_seed"]), milestones.index(row["evaluation_budget"]), condition_order[row["topology_condition"]], int(row["development_episode_id"])))
    with (target / "raw_episode_metrics.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    grouped: dict[tuple, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[(row["method"], int(row["train_seed"]), row["evaluation_budget"], row["topology_condition"])].append(row)
    summary = []
    for arm in freeze["arms"]:
        for cohort, seeds in freeze["cohorts"].items():
            for seed in seeds:
                for label in milestones:
                    for condition in condition_order:
                        part = grouped[(arm, seed, label, condition)]
                        summary.append({"arm": arm, "cohort": cohort, "seed": seed, "checkpoint_label": label, "condition": condition, "J": mean(part, "J"), "collision": mean(part, "collision"), "timeout": mean(part, "timeout"), "constraint_violation": mean(part, "constraint_violation")})
    with (target / "per_seed_condition_summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary[0])); writer.writeheader(); writer.writerows(summary)
    manifest = {"protocol": freeze["protocol"], "status": "completed", "tape_hash": tape["tape_hash"], "tape_sha256": digest(TAPE), "freeze_sha256": digest(FREEZE), "source_runs": sources, "checkpoint_labels": milestones, "raw_rows": len(rows), "cells": len(tasks), "episodes_per_cell": len(tape["episode_ids"]), "workers": workers, "training_started": False, "checkpoint_promotion": False, "automatic_follow_on_started": False}
    (target / "evaluation_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
