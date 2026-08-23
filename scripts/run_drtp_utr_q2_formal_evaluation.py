"""Evaluate all prospective formal 10M checkpoints on the frozen 490k tape."""
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
from create_drtp_utr_q2_formal_tape import TAPE_START  # noqa: E402
from run_drtp_utr_q2_formal_single import ARMS, PROTOCOL as TRAIN_PROTOCOL, SEEDS  # noqa: E402


PROTOCOL = "DRTP-UTR-Q2-FORMAL-PAIRED-5SEED-EVALUATION-V1"
FINAL_LABEL = "10m"


def evaluate_formal_cell(task: tuple[tuple, int]) -> list[dict]:
    base_task, gpu_id = task
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.set_device(gpu_id)
    except ImportError:  # pragma: no cover
        pass
    return base.evaluate_cell(base_task)


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def finite_mean(rows: list[dict], key: str) -> float:
    values = [float(row[key]) for row in rows if math.isfinite(float(row[key]))]
    return sum(values) / len(values) if values else math.nan


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--gpu-ids", default="0")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("NO-GO: explicit --execute is required")
    tape = json.loads((args.output_root / "formal_tape_manifest.json").read_text(encoding="utf-8"))
    if tape.get("episode_ids") != list(range(TAPE_START, TAPE_START + 100)):
        raise RuntimeError("invalid formal tape namespace")
    if tape.get("canonical") is not False or tape.get("prospective_formal_confirmation") is not True:
        raise RuntimeError("invalid formal tape provenance")
    eval_root = args.output_root / "evaluations" / "final_10m"
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
                "prospective_formal": manifest.get("prospective_formal_confirmation") is True,
                "no_canonical": manifest.get("canonical_seeds_used") is False,
            }
            if not all(checks.values()):
                raise RuntimeError(f"formal run contract violation in {run_dir}: {checks}")
            checkpoint = run_dir / "actor_critic_latest.pt"
            if not checkpoint.exists():
                raise FileNotFoundError(checkpoint)
            tasks.append((arm, seed, str(checkpoint), FINAL_LABEL,
                          tape["episode_ids"], tape["conditions"], tape["tape_hash"]))
            source_manifests.append(manifest)
    gpu_ids = [int(item.strip()) for item in args.gpu_ids.split(",") if item.strip()]
    if not gpu_ids:
        raise ValueError("at least one GPU id is required")
    assigned_tasks = [(task, gpu_ids[index % len(gpu_ids)]) for index, task in enumerate(tasks)]
    workers = min(args.workers, len(assigned_tasks))
    total = len(tasks) * len(tape["conditions"]) * len(tape["episode_ids"])
    print(f"formal evaluation: workers={workers}, cells={len(tasks)}, episodes={total}", flush=True)
    raw_rows, completed = [], 0
    context = mp.get_context("spawn")
    with ProcessPoolExecutor(max_workers=workers, mp_context=context) as pool:
        futures = [pool.submit(evaluate_formal_cell, task) for task in assigned_tasks]
        for future in as_completed(futures):
            rows = future.result()
            for row in rows:
                row["protocol"] = PROTOCOL
                row["inference_unit"] = "training_seed"
            raw_rows.extend(rows)
            completed += len(rows)
            print(f"formal evaluation progress {completed}/{total} ({100 * completed / total:.2f}%)", flush=True)
    condition_order = {item["name"]: index for index, item in enumerate(tape["conditions"])}
    raw_rows.sort(key=lambda row: (row["method"], int(row["train_seed"]),
                                  condition_order[row["topology_condition"]],
                                  int(row["development_episode_id"])))
    if len(raw_rows) != total:
        raise RuntimeError(f"expected {total} raw rows, found {len(raw_rows)}")
    write_csv(eval_root / "raw_episode_metrics.csv", raw_rows)

    condition_specs = {item["name"]: item for item in tape["conditions"]}
    grouped: dict[tuple[str, int, str], list[dict]] = {}
    for row in raw_rows:
        grouped.setdefault((row["method"], int(row["train_seed"]), row["topology_condition"]), []).append(row)
    summary = []
    for arm in ARMS:
        for seed in SEEDS:
            for condition in condition_order:
                rows = grouped[(arm, seed, condition)]
                spec = condition_specs[condition]
                onset = int(spec["start_step"])
                risk_rows = [] if condition == "nominal" else [row for row in rows if int(float(row["terminal_step"])) >= onset]
                pretrigger = [] if condition == "nominal" else [
                    row for row in rows
                    if float(row["collision"]) == 1.0 and int(float(row["terminal_step"])) < onset
                ]
                summary.append({
                    "arm": arm, "seed": seed, "checkpoint_label": FINAL_LABEL,
                    "condition": condition, "J": finite_mean(rows, "J"),
                    "collision": finite_mean(rows, "collision"),
                    "timeout": finite_mean(rows, "timeout"),
                    "constraint_violation": finite_mean(rows, "constraint_violation"),
                    "failure_exposure": math.nan if condition == "nominal" else finite_mean(rows, "failure_exposed"),
                    "failure_exposure_all_scheduled": math.nan if condition == "nominal" else finite_mean(rows, "failure_exposed"),
                    "episode_length": finite_mean(rows, "terminal_step"),
                    "risk_set_size": len(risk_rows),
                    "survival_to_onset_fraction": math.nan if condition == "nominal" else len(risk_rows) / len(rows),
                    "failure_trigger_success_rate_risk_set": math.nan if not risk_rows else finite_mean(risk_rows, "failure_exposed"),
                    "pretrigger_collision_count": len(pretrigger),
                    "pretrigger_collision_rate": math.nan if condition == "nominal" else len(pretrigger) / len(rows),
                    "path_switch_count": finite_mean(rows, "path_switch_count"),
                    "direct_path_fraction": finite_mean(rows, "direct_path_fraction_during_failure"),
                    "relay_path_fraction": finite_mean(rows, "relay_path_fraction_during_failure"),
                    "task_support_fraction": finite_mean(rows, "task_support_fraction_during_failure"),
                    "legal_information_fraction": finite_mean(rows, "legal_information_fraction_during_failure"),
                    "mean_cache_age": finite_mean(rows, "mean_cache_age_during_failure"),
                    "traveled_distance": finite_mean(rows, "traveled_distance"),
                    "control_effort": finite_mean(rows, "control_effort"),
                })
    write_csv(eval_root / "per_seed_condition_summary.csv", summary)
    manifest = {
        "protocol": PROTOCOL, "status": "completed", "tape_hash": tape["tape_hash"],
        "tape_start": TAPE_START, "episodes_per_condition": 100,
        "checkpoint_label": FINAL_LABEL, "raw_rows": len(raw_rows), "cells": len(tasks),
        "workers": workers, "gpu_ids": gpu_ids, "source_runs": source_manifests,
        "inference_unit": "training_seed", "canonical_seeds_used": False,
        "all_scheduled_episodes_retained": True,
    }
    (eval_root / "evaluation_manifest.json").write_text(
        json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2, default=str))


if __name__ == "__main__":
    main()
