"""Uniform multi-condition, paired evaluation for frozen DRTP development runs."""
from __future__ import annotations

import argparse
import csv
from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import json
import math
import multiprocessing as mp
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import run_phase_fl_single as fl  # noqa: E402
import run_phase_rsg1_development_smoke as evaluator  # noqa: E402
from envs.uav_intercept_3d_env import UAVIntercept3DConfig, UAVIntercept3DEnv  # noqa: E402


PROTOCOL = "DRTP-SG-DEVELOPMENT-EVALUATION-V1"
SEEDS = (1901, 1902)
ARMS = ("utr_sg", "drtp_sg")
BUDGET_LABELS = {
    "1m": ("750k", "1m"),
    "2m": ("1500k", "2m"),
    "3m": ("2500k", "3m"),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def variant_env(seed: int, spec: tuple[int, int] | None) -> UAVIntercept3DEnv:
    onset, duration = spec if spec is not None else (0, 0)
    return UAVIntercept3DEnv(UAVIntercept3DConfig(
        seed=seed, target_policy="straight", strict_target_sensing=True,
        agent_target_info_bottleneck=True, relay_dependent_task=True,
        business_grounded_geometry=True, communication_range_scale=1.0,
        communication_dropout_prob=0.0, message_delay_steps=0,
        radar_dropout_prob=0.0, max_steps=260, min_success_step=260,
        failed_blue_agent=1 if spec is not None else -1,
        node_failure_start_step=onset, node_failure_duration_steps=duration,
    ))


def checkpoint_for(run_dir: Path, label: str) -> Path:
    return run_dir / "actor_critic_latest.pt" if label in {"1m", "2m", "3m"} else run_dir / f"actor_critic_milestone_{label}.pt"


def evaluate_cell(task: tuple[str, int, str, str, list[int], list[dict], str]) -> list[dict]:
    arm, seed, checkpoint_str, label, episode_ids, condition_rows, tape_hash = task
    try:
        import torch
        torch.set_num_threads(1)
    except ImportError:  # pragma: no cover
        pass
    checkpoint = Path(checkpoint_str)
    agent = fl.build_agent({"graph_encoder": "single", "hidden_dim": 115}, checkpoint, seed)
    rows: list[dict] = []
    for condition in condition_rows:
        spec = None if condition["name"] == "nominal" else (int(condition["start_step"]), int(condition["duration_steps"]))
        original = evaluator.frozen_env
        evaluator.frozen_env = lambda episode_seed, failure_on, _spec=spec: variant_env(episode_seed, _spec)
        try:
            for episode_id in episode_ids:
                execution_condition = "nominal" if spec is None else "relay_failure"
                row, _ = evaluator.evaluate_episode(agent, arm, seed, episode_id, execution_condition)
                row.update({
                    "protocol": PROTOCOL, "evaluation_budget": label,
                    "topology_condition": condition["name"],
                    "onset": "" if spec is None else spec[0],
                    "duration": "" if spec is None else spec[1],
                    "checkpoint_sha256": sha256(checkpoint), "tape_hash": tape_hash,
                })
                rows.append(row)
        finally:
            evaluator.frozen_env = original
    return rows


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
    parser.add_argument("--budget", choices=tuple(BUDGET_LABELS), required=True)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("NO-GO: explicit --execute is required")
    if args.workers < 1:
        raise ValueError("workers must be positive")
    tape = json.loads((args.output_root / "tape_manifest.json").read_text(encoding="utf-8"))
    if tape.get("episode_ids") != list(range(420000, 420100)) or tape.get("canonical") is not False:
        raise RuntimeError("invalid 420k development tape")
    eval_root = args.output_root / "evaluations" / args.budget
    if eval_root.exists() and any(eval_root.iterdir()):
        raise FileExistsError(f"refusing to overwrite: {eval_root}")
    eval_root.mkdir(parents=True, exist_ok=False)
    tasks, source_manifests = [], []
    for arm in ARMS:
        for seed in SEEDS:
            run_dir = args.output_root / "runs" / args.budget / arm / f"seed{seed}"
            manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))
            if manifest.get("status") != "completed" or manifest.get("budget") != args.budget:
                raise RuntimeError(f"incomplete or mismatched run: {run_dir}")
            if manifest.get("parameter_count") != 116728 or manifest.get("canonical_seeds_used") is not False:
                raise RuntimeError(f"contract violation in run manifest: {run_dir}")
            for label in BUDGET_LABELS[args.budget]:
                checkpoint = checkpoint_for(run_dir, label)
                if not checkpoint.exists():
                    raise FileNotFoundError(checkpoint)
                tasks.append((arm, seed, str(checkpoint), label, tape["episode_ids"], tape["conditions"], tape["tape_hash"]))
            source_manifests.append(manifest)
    workers = min(args.workers, len(tasks))
    total = len(tasks) * len(tape["conditions"]) * len(tape["episode_ids"])
    print(f"DRTP evaluation: workers={workers}, cells={len(tasks)}, episodes={total}", flush=True)
    raw_rows, completed = [], 0
    context = mp.get_context("spawn")
    with ProcessPoolExecutor(max_workers=workers, mp_context=context) as pool:
        futures = [pool.submit(evaluate_cell, task) for task in tasks]
        for future in as_completed(futures):
            rows = future.result()
            raw_rows.extend(rows); completed += len(rows)
            print(f"DRTP evaluation progress {completed}/{total} ({100 * completed / total:.1f}%)", flush=True)
    condition_order = {item["name"]: index for index, item in enumerate(tape["conditions"])}
    raw_rows.sort(key=lambda row: (row["method"], int(row["train_seed"]), row["evaluation_budget"],
                                   condition_order[row["topology_condition"]], int(row["development_episode_id"])))
    write_csv(eval_root / "raw_episode_metrics.csv", raw_rows)
    summary = []
    for arm in ARMS:
        for seed in SEEDS:
            for label in BUDGET_LABELS[args.budget]:
                for condition in condition_order:
                    rows = [row for row in raw_rows if row["method"] == arm and int(row["train_seed"]) == seed
                            and row["evaluation_budget"] == label and row["topology_condition"] == condition]
                    summary.append({
                        "arm": arm, "seed": seed, "checkpoint_label": label, "condition": condition,
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
        "protocol": PROTOCOL, "status": "completed", "budget": args.budget,
        "tape_hash": tape["tape_hash"], "tape_start": 420000, "episodes_per_condition": 100,
        "checkpoint_labels": list(BUDGET_LABELS[args.budget]), "raw_rows": len(raw_rows),
        "cells": len(tasks), "workers": workers, "source_runs": source_manifests,
        "canonical_seeds_used": False, "held_out_tape_used": False,
    }
    (eval_root / "evaluation_manifest.json").write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2, default=str))


if __name__ == "__main__":
    main()
