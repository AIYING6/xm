"""Evaluate the frozen EGTR P3 1M checkpoints on the P3 development tape."""
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

import run_phase_rsg1_development_smoke as evaluator  # noqa: E402
from envs.uav_intercept_3d_env import UAVIntercept3DConfig, UAVIntercept3DEnv  # noqa: E402


PROTOCOL = "EGTR-P3-DEVELOPMENT-EVALUATION-V1"
TAPE_PROTOCOL = "EGTR-P3-DEVELOPMENT-TAPE-V1"
TAPE_START = 520000
TAPE_END = 520099
EPISODES = 100
ARMS = ("utr_sg", "drtp_sg", "egtr_sg")
SEEDS = (2501, 2502, 2503)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def variant_env(seed: int, spec: tuple[int, int] | None) -> UAVIntercept3DEnv:
    onset, duration = spec if spec is not None else (0, 0)
    return UAVIntercept3DEnv(UAVIntercept3DConfig(
        seed=seed,
        target_policy="straight",
        strict_target_sensing=True,
        agent_target_info_bottleneck=True,
        relay_dependent_task=True,
        business_grounded_geometry=True,
        communication_range_scale=1.0,
        communication_dropout_prob=0.0,
        message_delay_steps=0,
        radar_dropout_prob=0.0,
        max_steps=260,
        min_success_step=260,
        failed_blue_agent=1 if spec is not None else -1,
        node_failure_start_step=onset,
        node_failure_duration_steps=duration,
    ))


def evaluate_cell(task: tuple[str, int, str, list[int], list[dict], str]) -> list[dict]:
    arm, seed, checkpoint_str, episode_ids, condition_rows, tape_hash = task
    import torch

    torch.set_num_threads(1)
    checkpoint = Path(checkpoint_str)
    agent = evaluator.build_agent({"graph_encoder": "single", "hidden_dim": 115}, checkpoint, seed)
    rows: list[dict] = []
    for condition in condition_rows:
        name = str(condition["name"])
        spec = None if name == "nominal" else (
            int(condition["start_step"]), int(condition["duration_steps"])
        )
        original = evaluator.frozen_env
        evaluator.frozen_env = lambda episode_seed, failure_on, _spec=spec: variant_env(episode_seed, _spec)
        try:
            for episode_id in episode_ids:
                execution_condition = "nominal" if spec is None else "relay_failure"
                row, _ = evaluator.evaluate_episode(agent, arm, seed, episode_id, execution_condition)
                row.update({
                    "protocol": PROTOCOL,
                    "evaluation_budget": "1m",
                    "topology_condition": name,
                    "scheduled_failure_onset": "" if spec is None else spec[0],
                    "scheduled_failure_duration": "" if spec is None else spec[1],
                    "checkpoint_sha256": sha256(checkpoint),
                    "tape_hash": tape_hash,
                })
                rows.append(row)
        finally:
            evaluator.frozen_env = original
    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def finite_mean(rows: list[dict], key: str) -> float:
    values = []
    for row in rows:
        try:
            value = float(row[key])
        except (KeyError, TypeError, ValueError):
            continue
        if math.isfinite(value):
            values.append(value)
    return sum(values) / len(values) if values else math.nan


def validate_inputs(trained_root: Path) -> tuple[dict, list[dict]]:
    tape_path = trained_root / "tape" / "tape_manifest.json"
    tape = json.loads(tape_path.read_text(encoding="utf-8"))
    if tape.get("protocol") != TAPE_PROTOCOL:
        raise RuntimeError(f"unexpected tape protocol: {tape.get('protocol')}")
    if tape.get("episode_ids") != list(range(TAPE_START, TAPE_END + 1)):
        raise RuntimeError("P3 tape episode ids are not 520000-520099")
    if tape.get("canonical") is not False or tape.get("development_only") is not True:
        raise RuntimeError("P3 tape is not development-only")
    manifests = []
    for arm in ARMS:
        for seed in SEEDS:
            run_dir = trained_root / "runs" / arm / f"seed{seed}"
            manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))
            expected = {
                "status": "completed",
                "updates": 3907,
                "environment_steps": 1000192,
                "parameter_count": 116728,
                "from_scratch": True,
                "resume": False,
                "canonical_seeds_used": False,
                "tape_hash": tape["tape_hash"],
            }
            for key, value in expected.items():
                if manifest.get(key) != value:
                    raise RuntimeError(f"manifest mismatch {key}={manifest.get(key)!r}: {run_dir}")
            checkpoint = run_dir / "actor_critic_latest.pt"
            if not checkpoint.is_file():
                raise FileNotFoundError(checkpoint)
            if manifest.get("checkpoint_sha256") != sha256(checkpoint):
                raise RuntimeError(f"checkpoint hash mismatch: {checkpoint}")
            manifests.append(manifest)
    return tape, manifests


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trained-root", type=Path, required=True,
                        help="extracted results/development/egtr_p3 directory")
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("NO-GO: explicit --execute is required")
    if args.workers < 1:
        raise ValueError("workers must be positive")
    if args.output_root.exists() and any(args.output_root.iterdir()):
        raise FileExistsError(f"refusing to overwrite: {args.output_root}")
    args.output_root.mkdir(parents=True, exist_ok=True)

    tape, source_manifests = validate_inputs(args.trained_root)
    tasks = []
    for arm in ARMS:
        for seed in SEEDS:
            checkpoint = args.trained_root / "runs" / arm / f"seed{seed}" / "actor_critic_latest.pt"
            tasks.append((arm, seed, str(checkpoint), tape["episode_ids"], tape["conditions"], tape["tape_hash"]))

    workers = min(args.workers, len(tasks))
    total = len(tasks) * len(tape["conditions"]) * len(tape["episode_ids"])
    print(f"EGTR P3 evaluation: workers={workers}, cells={len(tasks)}, episodes={total}", flush=True)
    raw_rows: list[dict] = []
    completed = 0
    context = mp.get_context("spawn")
    with ProcessPoolExecutor(max_workers=workers, mp_context=context) as pool:
        futures = [pool.submit(evaluate_cell, task) for task in tasks]
        for future in as_completed(futures):
            rows = future.result()
            raw_rows.extend(rows)
            completed += len(rows)
            print(f"EGTR P3 evaluation progress {completed}/{total} ({100 * completed / total:.2f}%)", flush=True)

    condition_order = {item["name"]: index for index, item in enumerate(tape["conditions"])}
    raw_rows.sort(key=lambda row: (
        row["method"], int(row["train_seed"]),
        condition_order[row["topology_condition"]], int(row["development_episode_id"]),
    ))
    write_csv(args.output_root / "raw_episode_metrics.csv", raw_rows)

    summary: list[dict] = []
    for arm in ARMS:
        for seed in SEEDS:
            for condition in condition_order:
                rows = [row for row in raw_rows if row["method"] == arm
                        and int(row["train_seed"]) == seed
                        and row["topology_condition"] == condition]
                summary.append({
                    "method": arm,
                    "train_seed": seed,
                    "condition": condition,
                    "episodes": len(rows),
                    "J": finite_mean(rows, "J"),
                    "success": finite_mean(rows, "success_at_horizon"),
                    "collision": finite_mean(rows, "collision"),
                    "timeout": finite_mean(rows, "timeout"),
                    "constraint_violation": finite_mean(rows, "constraint_violation"),
                    "failure_exposure": finite_mean(rows, "failure_exposed"),
                    "terminal_step": finite_mean(rows, "terminal_step"),
                    "path_switch_count": finite_mean(rows, "path_switch_count"),
                    "direct_path_fraction": finite_mean(rows, "direct_path_fraction_during_failure"),
                    "relay_path_fraction": finite_mean(rows, "relay_path_fraction_during_failure"),
                    "task_support_fraction": finite_mean(rows, "task_support_fraction_during_failure"),
                    "legal_information_fraction": finite_mean(rows, "legal_information_fraction_during_failure"),
                    "mean_cache_age": finite_mean(rows, "mean_cache_age_during_failure"),
                })
    write_csv(args.output_root / "per_seed_condition_summary.csv", summary)
    manifest = {
        "protocol": PROTOCOL,
        "status": "completed",
        "budget": "1m",
        "tape_protocol": TAPE_PROTOCOL,
        "tape_hash": tape["tape_hash"],
        "tape_start": TAPE_START,
        "tape_end": TAPE_END,
        "episodes_per_condition": EPISODES,
        "conditions": len(tape["conditions"]),
        "raw_rows": len(raw_rows),
        "cells": len(tasks),
        "workers": workers,
        "source_runs": source_manifests,
        "canonical_seeds_used": False,
        "held_out_tape_used": False,
    }
    (args.output_root / "evaluation_manifest.json").write_text(
        json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2, default=str))


if __name__ == "__main__":
    main()
