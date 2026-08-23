"""Unified post-hoc evaluation for the frozen DRTP-SEED-S1-A screen.

This script only reads completed S1-A checkpoints and evaluates them on the
development-only 440000--440099 tape.  It never trains, resumes, promotes a
checkpoint, or changes the registered intervention matrix.
"""
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


PROTOCOL = "DRTP-SEED-S1-A-DEVELOPMENT-EVALUATION-V1"
RUNS = (
    "R0_G_REFERENCE",
    "R1_B_REFERENCE",
    "R2_I_INIT",
    "R3_I_ENV",
    "R4_I_ACTION",
    "R5_I_MINIBATCH",
    "R6_I_TOPOLOGY",
)
TAPE_PATH = ROOT / "artifacts/drtp_seed_s1/diagnostic_tape_manifest.json"


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


def evaluate_cell(task: tuple[str, str, list[int], list[dict], str]) -> list[dict]:
    run_name, checkpoint_text, episode_ids, conditions, tape_hash = task
    import torch

    torch.set_num_threads(1)
    checkpoint = Path(checkpoint_text)
    # Every S1-A run uses the unchanged single-graph SG actor/critic.
    agent = evaluator.build_agent({"graph_encoder": "single", "hidden_dim": 115}, checkpoint, 1901)
    rows: list[dict] = []
    checkpoint_hash = sha256(checkpoint)
    for condition in conditions:
        name = str(condition["name"])
        onset = condition.get("failure_start_step")
        duration = condition.get("failure_duration_steps")
        spec = None if name == "nominal" else (int(onset), int(duration))
        original = evaluator.frozen_env
        evaluator.frozen_env = lambda episode_seed, failure_on, _spec=spec: variant_env(episode_seed, _spec)
        try:
            for episode_id in episode_ids:
                row, _ = evaluator.evaluate_episode(
                    agent,
                    run_name,
                    1901 if run_name == "R0_G_REFERENCE" else 1902,
                    int(episode_id),
                    "nominal" if spec is None else "relay_failure",
                )
                row.update({
                    "protocol": PROTOCOL,
                    "run": run_name,
                    "topology_condition": name,
                    "scheduled_failure_onset": "" if spec is None else int(onset),
                    "scheduled_failure_duration": "" if spec is None else int(duration),
                    "checkpoint_sha256": checkpoint_hash,
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


def finite_mean(rows: list[dict], field: str) -> float:
    values = []
    for row in rows:
        try:
            value = float(row[field])
        except (KeyError, TypeError, ValueError):
            continue
        if math.isfinite(value):
            values.append(value)
    return sum(values) / len(values) if values else math.nan


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("NO-GO: explicit --execute is required")
    if args.workers < 1:
        raise ValueError("workers must be positive")
    if not TAPE_PATH.exists():
        raise FileNotFoundError(TAPE_PATH)
    tape = json.loads(TAPE_PATH.read_text(encoding="utf-8"))
    expected_ids = list(range(440000, 440100))
    if tape.get("episode_ids") != expected_ids or tape.get("canonical") is not False:
        raise RuntimeError("invalid or non-development S1-A tape")
    if args.output_root.exists() and any(args.output_root.iterdir()):
        raise FileExistsError(f"refusing to overwrite: {args.output_root}")
    args.output_root.mkdir(parents=True, exist_ok=False)

    tasks: list[tuple[str, str, list[int], list[dict], str]] = []
    source_manifests = []
    for run_name in RUNS:
        run_dir = ROOT / "results/development/drtp_seed_s1a/runs" / run_name
        manifest_path = run_dir / "run_manifest.json"
        checkpoint = run_dir / "actor_critic_latest.pt"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        required = {
            "status": "completed",
            "updates": 5859,
            "steps": 1499904,
            "post_hoc_development_diagnostic": True,
            "from_scratch": True,
            "canonical_seeds_used": False,
            "heldout_used": False,
        }
        if any(manifest.get(key) != value for key, value in required.items()):
            raise RuntimeError(f"S1-A run contract violation: {run_name}")
        if not checkpoint.exists() or sha256(checkpoint) != manifest.get("checkpoint_sha256"):
            raise RuntimeError(f"invalid final checkpoint: {run_name}")
        tasks.append((run_name, str(checkpoint), tape["episode_ids"], tape["conditions"], tape["tape_hash"]))
        source_manifests.append(manifest)

    total = len(tasks) * len(tape["conditions"]) * len(tape["episode_ids"])
    workers = min(args.workers, len(tasks))
    print(f"S1-A evaluation: workers={workers}, episodes={total}", flush=True)
    raw: list[dict] = []
    completed = 0
    with ProcessPoolExecutor(max_workers=workers, mp_context=mp.get_context("spawn")) as pool:
        futures = [pool.submit(evaluate_cell, task) for task in tasks]
        for future in as_completed(futures):
            cell_rows = future.result()
            raw.extend(cell_rows)
            completed += len(cell_rows)
            print(f"S1-A evaluation progress {completed}/{total} ({100 * completed / total:.2f}%)", flush=True)

    order = {str(row["name"]): index for index, row in enumerate(tape["conditions"])}
    raw.sort(key=lambda row: (row["run"], order[row["topology_condition"]], int(row["development_episode_id"])))
    write_csv(args.output_root / "raw_episode_metrics.csv", raw)

    summary: list[dict] = []
    for run_name in RUNS:
        run_rows = [row for row in raw if row["run"] == run_name]
        nominal = [row for row in run_rows if row["topology_condition"] == "nominal"]
        nominal_by_id = {int(row["development_episode_id"]): row for row in nominal}
        for condition in [str(row["name"]) for row in tape["conditions"]]:
            cell = [row for row in run_rows if row["topology_condition"] == condition]
            summary.append({
                "run": run_name,
                "training_seed": 1901 if run_name == "R0_G_REFERENCE" else 1902,
                "condition": condition,
                "J": finite_mean(cell, "J"),
                "collision": finite_mean(cell, "collision"),
                "timeout": finite_mean(cell, "timeout"),
                "constraint_violation": finite_mean(cell, "constraint_violation"),
                "failure_exposure": finite_mean(cell, "failure_exposed"),
                "episode_length": finite_mean(cell, "terminal_step"),
                "path_switch_count": finite_mean(cell, "path_switch_count"),
                "direct_path_fraction": finite_mean(cell, "direct_path_fraction_during_failure"),
                "relay_path_fraction": finite_mean(cell, "relay_path_fraction_during_failure"),
                "task_support_fraction": finite_mean(cell, "task_support_fraction_during_failure"),
                "legal_information_fraction": finite_mean(cell, "legal_information_fraction_during_failure"),
                "mean_cache_age": finite_mean(cell, "mean_cache_age_during_failure"),
            })
        for row in [row for row in run_rows if row["topology_condition"] != "nominal"]:
            nominal_row = nominal_by_id[int(row["development_episode_id"])]
            row["J_nominal_paired"] = nominal_row["J"]
            row["delta_J_paired"] = float(nominal_row["J"]) - float(row["J"])
    write_csv(args.output_root / "per_run_condition_summary.csv", summary)

    manifest = {
        "protocol": PROTOCOL,
        "status": "completed",
        "tape_hash": tape["tape_hash"],
        "tape_namespace": "440000-440099",
        "conditions": [row["name"] for row in tape["conditions"]],
        "episodes_per_condition": 100,
        "raw_rows": len(raw),
        "runs": list(RUNS),
        "workers": workers,
        "final_checkpoint_only": True,
        "canonical_seeds_used": False,
        "heldout_used": False,
        "source_run_manifests": source_manifests,
    }
    (args.output_root / "evaluation_manifest.json").write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2), flush=True)


if __name__ == "__main__":
    main()
