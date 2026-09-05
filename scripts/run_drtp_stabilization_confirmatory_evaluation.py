"""Evaluate frozen 10M confirmation checkpoints on one matched tape."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]

import run_phase_rsg1_development_smoke as evaluator  # noqa: E402
from envs.uav_intercept_3d_env import UAVIntercept3DConfig, UAVIntercept3DEnv  # noqa: E402
from run_drtp_stabilization_confirmatory_single import ARMS, SEEDS, STEPS, UPDATES  # noqa: E402


PROTOCOL = "DRTP-STABILIZATION-FINAL-CONFIRMATION-10M-EVALUATION-V1"
TAPE_PROTOCOL = "DRTP-STABILIZATION-CONFIRMATORY-TAPE-V1"


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def fixed_env(seed: int, condition: dict) -> UAVIntercept3DEnv:
    return UAVIntercept3DEnv(UAVIntercept3DConfig(
        seed=seed, target_policy="straight", strict_target_sensing=True,
        agent_target_info_bottleneck=True, relay_dependent_task=True, business_grounded_geometry=True,
        communication_range_scale=1.0, communication_dropout_prob=0.0, message_delay_steps=0,
        radar_dropout_prob=0.0, max_steps=260, min_success_step=260,
        failed_blue_agent=int(condition["failed_blue_agent"]),
        node_failure_start_step=int(condition["start_step"]),
        node_failure_duration_steps=int(condition["duration_steps"]),
    ))


def cell(task: tuple) -> list[dict]:
    arm, seed, checkpoint, episode_ids, conditions, tape_hash = task
    import torch
    torch.set_num_threads(1)
    agent = evaluator.build_agent({"graph_encoder": "single", "hidden_dim": 115}, Path(checkpoint), seed)
    rows: list[dict] = []
    for condition in conditions:
        original = evaluator.frozen_env
        evaluator.frozen_env = lambda episode_seed, failure_on, _condition=condition: fixed_env(episode_seed, _condition)
        try:
            for episode_id in episode_ids:
                row, _ = evaluator.evaluate_episode(
                    agent, arm, seed, int(episode_id), "nominal" if condition["name"] == "nominal" else "relay_failure"
                )
                row.update({
                    "protocol": PROTOCOL, "topology_condition": condition["name"],
                    "scheduled_failure_onset": int(condition["start_step"]),
                    "scheduled_failure_duration": int(condition["duration_steps"]),
                    "checkpoint_sha256": digest(Path(checkpoint)), "tape_hash": tape_hash,
                })
                rows.append(row)
        finally:
            evaluator.frozen_env = original
    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def mean(rows: list[dict], key: str) -> float:
    values = [float(row[key]) for row in rows if math.isfinite(float(row[key]))]
    return sum(values) / len(values) if values else math.nan


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trained-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=10)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("explicit --execute is required")
    if args.output_root.exists():
        raise FileExistsError(f"refusing to overwrite {args.output_root}")
    tape = json.loads((args.trained_root / "tape" / "tape_manifest.json").read_text(encoding="utf-8"))
    if (tape.get("protocol") != TAPE_PROTOCOL or tape.get("episode_ids") != list(range(780000, 780100))
            or tape.get("training_access") != "forbidden"):
        raise RuntimeError("invalid confirmation tape")
    tasks, manifests = [], []
    for arm in ARMS:
        for seed in SEEDS:
            run = args.trained_root / "runs" / arm / f"seed{seed}"
            manifest = json.loads((run / "run_manifest.json").read_text(encoding="utf-8"))
            checkpoint = run / "actor_critic_latest.pt"
            expected = {
                "status": "completed", "updates": UPDATES, "environment_steps": STEPS,
                "from_scratch": True, "resume": False, "early_stopping": False,
                "checkpoint_promotion": False, "seed_replacement": False,
                "tape_hash": tape["tape_hash"],
            }
            if any(manifest.get(key) != value for key, value in expected.items()):
                raise RuntimeError(f"invalid confirmatory source run: {arm}/seed{seed}")
            if not checkpoint.is_file() or manifest.get("checkpoint_sha256") != digest(checkpoint):
                raise RuntimeError(f"invalid endpoint checkpoint: {checkpoint}")
            tasks.append((arm, seed, str(checkpoint), tape["episode_ids"], tape["conditions"], tape["tape_hash"]))
            manifests.append(manifest)
    total = len(tasks) * len(tape["conditions"]) * len(tape["episode_ids"])
    print(f"DRTP final confirmation evaluation: cells={len(tasks)}, episodes={total}, workers={min(args.workers, len(tasks))}", flush=True)
    raw: list[dict] = []
    completed = 0
    with ProcessPoolExecutor(max_workers=min(args.workers, len(tasks)), mp_context=mp.get_context("spawn")) as pool:
        futures = [pool.submit(cell, task) for task in tasks]
        for future in as_completed(futures):
            rows = future.result()
            raw.extend(rows)
            completed += len(rows)
            print(f"DRTP final confirmation evaluation progress {completed}/{total} ({100 * completed / total:.2f}%)", flush=True)
    order = {entry["name"]: index for index, entry in enumerate(tape["conditions"])}
    raw.sort(key=lambda row: (row["method"], int(row["train_seed"]), order[row["topology_condition"]], int(row["development_episode_id"])))
    write_csv(args.output_root / "raw_episode_metrics.csv", raw)
    summary: list[dict] = []
    for arm in ARMS:
        for seed in SEEDS:
            for condition in order:
                subset = [row for row in raw if row["method"] == arm and int(row["train_seed"]) == seed and row["topology_condition"] == condition]
                summary.append({
                    "method": arm, "train_seed": seed, "condition": condition, "episodes": len(subset),
                    "J": mean(subset, "J"), "success": mean(subset, "success_at_horizon"),
                    "collision": mean(subset, "collision"), "timeout": mean(subset, "timeout"),
                    "constraint_violation": mean(subset, "constraint_violation"),
                    "control_effort": mean(subset, "control_effort"),
                })
    write_csv(args.output_root / "per_seed_condition_summary.csv", summary)
    evaluation_manifest = {
        "protocol": PROTOCOL, "status": "completed", "endpoint": "final_10m_only",
        "cells": len(tasks), "conditions": [entry["name"] for entry in tape["conditions"]],
        "episodes_per_condition": len(tape["episode_ids"]), "raw_episode_rows": len(raw),
        "summary_rows": len(summary), "tape_hash": tape["tape_hash"], "source_run_manifests": manifests,
        "training_started": False, "automatic_algorithm_revision": False, "automatic_6uav": False,
    }
    (args.output_root / "evaluation_manifest.json").write_text(json.dumps(evaluation_manifest, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({"status": "completed", "raw_episode_rows": len(raw)}, indent=2), flush=True)


if __name__ == "__main__":
    main()
