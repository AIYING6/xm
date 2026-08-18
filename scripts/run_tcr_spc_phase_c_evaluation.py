"""Unified final-checkpoint Phase-C evaluation on the frozen 440k tape."""
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
from scripts.create_tcr_spc_phase_c_tape import EPISODES, TAPE_START  # noqa: E402
from scripts.run_tcr_spc_phase_c_single import ARMS, SEEDS  # noqa: E402


PROTOCOL = "TCR-SPC-PHASE-C-1M-STABILITY-EVALUATION-V1"
PHASE_D_BUDGETS = {
    "2m": (2_000_128, "final_2m", "TCR-SPC-PHASE-D-2M-INTERIM-EVALUATION-V1"),
    "3m": (3_000_064, "final_3m", "TCR-SPC-PHASE-D-3M-CONTINUATION-EVALUATION-V1"),
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
        communication_dropout_prob=0.0, message_delay_steps=0, radar_dropout_prob=0.0,
        max_steps=260, min_success_step=260, failed_blue_agent=1 if spec is not None else -1,
        node_failure_start_step=onset, node_failure_duration_steps=duration,
    ))


def evaluate_cell(task: tuple[str, int, str, list[int], list[dict], str]) -> list[dict]:
    arm, seed, checkpoint_text, episode_ids, conditions, tape_hash = task
    import torch
    torch.set_num_threads(1)
    checkpoint = Path(checkpoint_text)
    agent = fl.build_agent({"graph_encoder": "single", "hidden_dim": 115}, checkpoint, seed)
    rows = []
    for condition in conditions:
        spec = None if condition["name"] == "nominal" else (int(condition["start_step"]), int(condition["duration_steps"]))
        original = evaluator.frozen_env
        evaluator.frozen_env = lambda episode_seed, failure_on, _spec=spec: variant_env(episode_seed, _spec)
        try:
            for episode_id in episode_ids:
                row, _ = evaluator.evaluate_episode(
                    agent, arm, seed, episode_id, "nominal" if spec is None else "relay_failure"
                )
                row.update({
                    "protocol": PROTOCOL, "topology_condition": condition["name"],
                    "onset": "" if spec is None else spec[0], "duration": "" if spec is None else spec[1],
                    "checkpoint_sha256": sha256(checkpoint), "tape_hash": tape_hash,
                })
                rows.append(row)
        finally:
            evaluator.frozen_env = original
    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)


def finite_mean(rows: list[dict], field: str) -> float:
    values = [float(row[field]) for row in rows if math.isfinite(float(row[field]))]
    return sum(values) / len(values) if values else math.nan


def gradient_summary(path: Path) -> dict:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    # Runtime telemetry may contain repeated CSV headers after periodic
    # checkpoint/log flushes. They are not observations and must not enter
    # numeric aggregation.
    rows = [row for row in rows if row.get("gradient_dot") != "gradient_dot"]
    if not rows:
        raise RuntimeError(f"missing actor-gradient rows: {path}")
    numeric = ("gradient_cosine", "post_projection_cosine", "g_nominal_norm", "g_failure_norm", "projection_magnitude", "final_gradient_norm")
    return {
        "gradient_updates": len(rows),
        "conflict_rate": sum(float(row["gradient_dot"]) < 0.0 for row in rows) / len(rows),
        **{field: finite_mean(rows, field) for field in numeric},
        "all_nominal_counts_128": all(int(float(row["nominal_sample_count"])) == 128 for row in rows),
        "all_failure_counts_128": all(int(float(row["failure_sample_count"])) == 128 for row in rows),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--phase-d", action="store_true")
    parser.add_argument("--phase-d-budget", choices=tuple(PHASE_D_BUDGETS), default="3m")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("NO-GO: explicit --execute is required")
    if args.workers < 1:
        raise ValueError("workers must be positive")
    tape = json.loads((args.output_root / "tape_manifest.json").read_text(encoding="utf-8"))
    if tape.get("episode_ids") != list(range(TAPE_START, TAPE_START + EPISODES)) or tape.get("canonical") is not False:
        raise RuntimeError("invalid Phase-C 440k tape")
    global PROTOCOL
    if args.phase_d:
        final_steps, eval_name, PROTOCOL = PHASE_D_BUDGETS[args.phase_d_budget]
    else:
        final_steps, eval_name = 1_000_192, "final_1m"
    eval_root = args.output_root / f"evaluations/{eval_name}"
    if eval_root.exists() and any(eval_root.iterdir()):
        raise FileExistsError(f"refusing to overwrite: {eval_root}")
    eval_root.mkdir(parents=True, exist_ok=False)
    tasks, source_runs, gradient_rows = [], [], []
    for arm in ARMS:
        for seed in SEEDS:
            run_dir = args.output_root / "runs" / arm / f"seed{seed}"
            manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))
            required = {
                "status": "completed", "parameter_count": 116728,
                "final_checkpoint_only": True, "canonical_seeds_used": False,
                "held_out_seeds_used": False,
            }
            if args.phase_d:
                required.update({
                    "final_environment_steps": final_steps,
                    "stage": args.phase_d_budget,
                    "strict_continuation": True,
                    "warm_restart_used": False,
                    "from_scratch_used": False,
                })
            else:
                required.update({
                    "environment_steps": 1_000_192,
                    "from_scratch": True,
                    "strict_continuous": True,
                    "drtp_adaptation": False,
                })
            if any(manifest.get(key) != value for key, value in required.items()) or manifest.get("tape_hash") != tape["tape_hash"]:
                raise RuntimeError(f"evaluation run contract violation: {run_dir}")
            checkpoint = run_dir / "actor_critic_latest.pt"
            expected_hash = manifest.get("final_checkpoint_sha256", manifest.get("checkpoint_sha256"))
            if not checkpoint.exists() or sha256(checkpoint) != expected_hash:
                raise RuntimeError(f"invalid final checkpoint: {run_dir}")
            summary = gradient_summary(run_dir / "actor_gradient_telemetry.csv")
            gradient_rows.append({"arm": arm, "seed": seed, **summary})
            tasks.append((arm, seed, str(checkpoint), tape["episode_ids"], tape["conditions"], tape["tape_hash"]))
            source_runs.append(manifest)
    total = len(tasks) * len(tape["conditions"]) * len(tape["episode_ids"])
    workers = min(args.workers, len(tasks))
    print(f"Phase-D evaluation {args.phase_d_budget if args.phase_d else '1m'}: workers={workers}, episodes={total}", flush=True)
    raw, completed = [], 0
    with ProcessPoolExecutor(max_workers=workers, mp_context=mp.get_context("spawn")) as pool:
        futures = [pool.submit(evaluate_cell, task) for task in tasks]
        for future in as_completed(futures):
            rows = future.result(); raw.extend(rows); completed += len(rows)
            print(f"Phase-D evaluation progress {completed}/{total} ({100 * completed / total:.2f}%)", flush=True)
    order = {row["name"]: index for index, row in enumerate(tape["conditions"])}
    raw.sort(key=lambda row: (row["method"], int(row["train_seed"]), order[row["topology_condition"]], int(row["development_episode_id"])))
    write_csv(eval_root / "raw_episode_metrics.csv", raw)
    summary = []
    for arm in ARMS:
        for seed in SEEDS:
            for condition in order:
                rows = [row for row in raw if row["method"] == arm and int(row["train_seed"]) == seed and row["topology_condition"] == condition]
                summary.append({
                    "arm": arm, "seed": seed, "condition": condition, "J": finite_mean(rows, "J"),
                    "collision": finite_mean(rows, "collision"), "timeout": finite_mean(rows, "timeout"),
                    "constraint_violation": finite_mean(rows, "constraint_violation"), "failure_exposure": finite_mean(rows, "failure_exposed"),
                    "episode_length": finite_mean(rows, "terminal_step"), "path_switch_count": finite_mean(rows, "path_switch_count"),
                    "direct_path_fraction": finite_mean(rows, "direct_path_fraction_during_failure"),
                    "relay_path_fraction": finite_mean(rows, "relay_path_fraction_during_failure"),
                    "task_support_fraction": finite_mean(rows, "task_support_fraction_during_failure"),
                })
    write_csv(eval_root / "per_seed_condition_summary.csv", summary)
    write_csv(eval_root / "gradient_diagnostics_summary.csv", gradient_rows)
    evaluation_manifest = {
        "protocol": PROTOCOL, "status": "completed", "tape_hash": tape["tape_hash"], "tape_start": TAPE_START,
        "episodes_per_condition": EPISODES, "conditions": [row["name"] for row in tape["conditions"]],
        "final_checkpoint_only": True, "phase_d": args.phase_d,
        "phase_d_stage": args.phase_d_budget if args.phase_d else None,
        "raw_rows": len(raw), "cells": len(tasks), "workers": workers,
        "source_runs": source_runs, "canonical_seeds_used": False, "held_out_used": False,
    }
    with (eval_root / "evaluation_manifest.json").open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(evaluation_manifest, handle, indent=2, default=str); handle.write("\n")
    print(json.dumps(evaluation_manifest, indent=2, default=str))


if __name__ == "__main__":
    main()
