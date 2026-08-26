"""Evaluate frozen MAPPO-NoGraph 10M checkpoints on the existing formal tape."""
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
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))

import run_drtp_sg_development_evaluation as condition_eval  # noqa: E402
import run_phase_rsg1_development_smoke as evaluator  # noqa: E402
from create_drtp_utr_q2_formal_tape import TAPE_START  # noqa: E402
from run_drtp_mappo_external_single import ARM, HIDDEN_DIM, PROTOCOL as TRAIN_PROTOCOL, SEEDS  # noqa: E402


PROTOCOL = "DRTP-MAPPO-NOGRAPH-EXTERNAL-REFERENCE-5SEED-EVALUATION-V1"
FINAL_LABEL = "10m"


def sha256(path: Path) -> str:
    import hashlib
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""): digest.update(chunk)
    return digest.hexdigest()


def evaluate_cell(task: tuple[tuple, int]) -> list[dict]:
    (seed, checkpoint_s, episode_ids, conditions, tape_hash), gpu_id = task
    try:
        import torch
        torch.set_num_threads(1)
        if torch.cuda.is_available(): torch.cuda.set_device(gpu_id)
    except ImportError: pass
    checkpoint = Path(checkpoint_s)
    agent = evaluator.build_agent({"graph_encoder": "no_graph", "hidden_dim": HIDDEN_DIM}, checkpoint, seed)
    rows: list[dict] = []
    for condition in conditions:
        spec = None if condition["name"] == "nominal" else (int(condition["start_step"]), int(condition["duration_steps"]))
        original = evaluator.frozen_env
        evaluator.frozen_env = lambda episode_seed, failure_on, _spec=spec: condition_eval.variant_env(episode_seed, _spec)
        try:
            for episode_id in episode_ids:
                row, _ = evaluator.evaluate_episode(agent, ARM, seed, episode_id, "nominal" if spec is None else "relay_failure")
                row.update({"protocol": PROTOCOL, "evaluation_budget": FINAL_LABEL,
                            "topology_condition": condition["name"], "onset": "" if spec is None else spec[0],
                            "duration": "" if spec is None else spec[1], "checkpoint_sha256": sha256(checkpoint),
                            "tape_hash": tape_hash})
                rows.append(row)
        finally:
            evaluator.frozen_env = original
    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)


def finite_mean(rows: list[dict], key: str) -> float:
    values = [float(row[key]) for row in rows if math.isfinite(float(row[key]))]
    return sum(values) / len(values) if values else math.nan


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=5); parser.add_argument("--gpu-ids", default="0")
    parser.add_argument("--execute", action="store_true"); args = parser.parse_args()
    if not args.execute: raise SystemExit("NO-GO: explicit --execute is required")
    tape = json.loads((args.output_root / "formal_tape_manifest.json").read_text(encoding="utf-8"))
    if tape.get("tape_hash") != "84e31ed185ced0608a30c9cb9f9659c7423c952e4603aac53cf691c54fc64ac2": raise RuntimeError("formal tape hash mismatch")
    if tape.get("episode_ids") != list(range(TAPE_START, TAPE_START + 100)): raise RuntimeError("formal tape namespace mismatch")
    root = args.output_root / "evaluations" / "final_10m"
    if root.exists() and any(root.iterdir()): raise FileExistsError(f"refusing to overwrite: {root}")
    root.mkdir(parents=True, exist_ok=False)
    tasks, manifests = [], []
    for seed in SEEDS:
        run_dir = args.output_root / "runs" / ARM / f"seed{seed}"
        manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))
        checks = {"completed": manifest.get("status") == "completed", "protocol": manifest.get("protocol") == TRAIN_PROTOCOL,
                  "from_scratch": manifest.get("from_scratch") is True, "strict": manifest.get("strict_continuous_trajectory") is True,
                  "no_promotion": manifest.get("checkpoint_promotion") is False, "runtime": manifest.get("runtime_state_checkpointing") is True,
                  "no_graph": manifest.get("graph_encoder") == "no_graph"}
        if not all(checks.values()): raise RuntimeError(f"contract violation in {run_dir}: {checks}")
        checkpoint = run_dir / "actor_critic_latest.pt"
        if not checkpoint.exists(): raise FileNotFoundError(checkpoint)
        tasks.append((seed, str(checkpoint), tape["episode_ids"], tape["conditions"], tape["tape_hash"])); manifests.append(manifest)
    gpu_ids = [int(value.strip()) for value in args.gpu_ids.split(",") if value.strip()]
    if not gpu_ids: raise ValueError("at least one GPU id is required")
    assigned = [(task, gpu_ids[index % len(gpu_ids)]) for index, task in enumerate(tasks)]
    workers, total = min(args.workers, len(assigned)), len(tasks) * len(tape["conditions"]) * len(tape["episode_ids"])
    print(f"MAPPO external evaluation: workers={workers}, cells={len(tasks)}, episodes={total}", flush=True)
    raw, completed = [], 0
    with ProcessPoolExecutor(max_workers=workers, mp_context=mp.get_context("spawn")) as pool:
        futures = [pool.submit(evaluate_cell, task) for task in assigned]
        for future in as_completed(futures):
            cell = future.result(); raw.extend(cell); completed += len(cell)
            print(f"MAPPO external evaluation progress {completed}/{total} ({100 * completed / total:.2f}%)", flush=True)
    order = {item["name"]: index for index, item in enumerate(tape["conditions"])}
    raw.sort(key=lambda row: (int(row["train_seed"]), order[row["topology_condition"]], int(row["development_episode_id"])))
    if len(raw) != total: raise RuntimeError(f"expected {total} rows, found {len(raw)}")
    write_csv(root / "raw_episode_metrics.csv", raw)
    by_key: dict[tuple[int, str], list[dict]] = {}
    for row in raw: by_key.setdefault((int(row["train_seed"]), row["topology_condition"]), []).append(row)
    summary = []
    for seed in SEEDS:
        for condition in tape["conditions"]:
            name, rows = condition["name"], by_key[(seed, condition["name"])]
            onset = int(condition["start_step"])
            risk = [] if name == "nominal" else [row for row in rows if int(float(row["terminal_step"])) >= onset]
            pre = [] if name == "nominal" else [row for row in rows if float(row["collision"]) == 1.0 and int(float(row["terminal_step"])) < onset]
            summary.append({"arm": ARM, "seed": seed, "checkpoint_label": FINAL_LABEL, "condition": name,
                "J": finite_mean(rows, "J"), "collision": finite_mean(rows, "collision"), "timeout": finite_mean(rows, "timeout"),
                "constraint_violation": finite_mean(rows, "constraint_violation"),
                "failure_exposure": math.nan if name == "nominal" else finite_mean(rows, "failure_exposed"),
                "failure_exposure_all_scheduled": math.nan if name == "nominal" else finite_mean(rows, "failure_exposed"),
                "episode_length": finite_mean(rows, "terminal_step"), "risk_set_size": len(risk),
                "survival_to_onset_fraction": math.nan if name == "nominal" else len(risk) / len(rows),
                "failure_trigger_success_rate_risk_set": math.nan if not risk else finite_mean(risk, "failure_exposed"),
                "pretrigger_collision_count": len(pre), "pretrigger_collision_rate": math.nan if name == "nominal" else len(pre) / len(rows),
                "path_switch_count": finite_mean(rows, "path_switch_count"), "direct_path_fraction": finite_mean(rows, "direct_path_fraction_during_failure"),
                "relay_path_fraction": finite_mean(rows, "relay_path_fraction_during_failure"), "task_support_fraction": finite_mean(rows, "task_support_fraction_during_failure"),
                "legal_information_fraction": finite_mean(rows, "legal_information_fraction_during_failure"),
                "mean_cache_age": finite_mean(rows, "mean_cache_age_during_failure"), "traveled_distance": finite_mean(rows, "traveled_distance"), "control_effort": finite_mean(rows, "control_effort")})
    write_csv(root / "per_seed_condition_summary.csv", summary)
    manifest = {"protocol": PROTOCOL, "status": "completed", "tape_hash": tape["tape_hash"], "checkpoint_label": FINAL_LABEL,
                "raw_rows": len(raw), "cells": len(tasks), "workers": workers, "source_runs": manifests,
                "inference_unit": "training_seed", "all_scheduled_episodes_retained": True, "canonical_seeds_used": False}
    (root / "evaluation_manifest.json").write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2, default=str))


if __name__ == "__main__": main()
