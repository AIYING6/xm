"""Evaluate frozen A/B UTR and DRTP endpoints on the final unseen OOD tape."""
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
import tarfile


ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]

import run_phase_rsg1_development_smoke as evaluator  # noqa: E402
from envs.uav_intercept_3d_env import UAVIntercept3DConfig, UAVIntercept3DEnv  # noqa: E402


FREEZE = ROOT / "configs" / "drtp_final_evidence_p0_heldout_ood_freeze_20260906.json"
PROTOCOL = "DRTP-FINAL-EVIDENCE-HELDOUT-OOD-EVALUATION-V1"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_freeze() -> dict:
    return json.loads(FREEZE.read_text(encoding="utf-8"))


def fixed_env(seed: int, condition: dict) -> UAVIntercept3DEnv:
    return UAVIntercept3DEnv(UAVIntercept3DConfig(
        seed=seed, target_policy="straight", strict_target_sensing=True,
        agent_target_info_bottleneck=True, relay_dependent_task=True,
        business_grounded_geometry=True, communication_range_scale=1.0,
        communication_dropout_prob=0.0, message_delay_steps=0,
        radar_dropout_prob=0.0, max_steps=260, min_success_step=260,
        failed_blue_agent=int(condition["failed_blue_agent"]),
        node_failure_start_step=int(condition["start_step"]),
        node_failure_duration_steps=int(condition["duration_steps"]),
        comm_topology_mode=str(condition["comm_topology_mode"]),
    ))


def source_member(asset: dict, arm: str, seed: int, name: str) -> str:
    return f"{asset['archive_root']}/runs/{arm}/seed{seed}/{name}"


def extract_sources(label: str, archive_path: Path, output_root: Path, freeze: dict) -> list[dict]:
    asset = freeze["source_archives"][label]
    if sha256(archive_path) != asset["sha256"]:
        raise RuntimeError(f"{label} archive SHA256 mismatch")
    result: list[dict] = []
    with tarfile.open(archive_path, "r:gz") as archive:
        available = {item.name.lstrip("./"): item for item in archive.getmembers() if item.isfile()}
        for arm in freeze["checkpoint_contract"]["arms"]:
            for seed in asset["seeds"]:
                manifest_name = source_member(asset, arm, seed, "run_manifest.json")
                checkpoint_name = source_member(asset, arm, seed, "actor_critic_latest.pt")
                if manifest_name not in available or checkpoint_name not in available:
                    raise RuntimeError(f"{label} archive lacks frozen endpoint for {arm}/seed{seed}")
                manifest_handle = archive.extractfile(available[manifest_name])
                checkpoint_handle = archive.extractfile(available[checkpoint_name])
                if manifest_handle is None or checkpoint_handle is None:
                    raise RuntimeError(f"cannot read frozen endpoint for {arm}/seed{seed}")
                manifest = json.loads(manifest_handle.read().decode("utf-8"))
                if (manifest.get("status") != "completed"
                        or manifest.get("updates") != freeze["checkpoint_contract"]["updates"]
                        or manifest.get("environment_steps") != freeze["checkpoint_contract"]["environment_steps"]
                        or manifest.get("checkpoint_promotion") is not False
                        or manifest.get("seed_replacement") is not False):
                    raise RuntimeError(f"invalid frozen source manifest for {label}/{arm}/seed{seed}")
                destination = output_root / "frozen_inputs" / label / arm / f"seed{seed}"
                destination.mkdir(parents=True, exist_ok=False)
                checkpoint = destination / "actor_critic_latest.pt"
                checkpoint.write_bytes(checkpoint_handle.read())
                if manifest.get("checkpoint_sha256") != sha256(checkpoint):
                    raise RuntimeError(f"checkpoint hash mismatch for {label}/{arm}/seed{seed}")
                (destination / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
                result.append({
                    "cohort": label, "method": arm, "train_seed": seed,
                    "checkpoint": str(checkpoint), "checkpoint_sha256": manifest["checkpoint_sha256"],
                    "source_manifest": manifest,
                })
    return result


def cell(task: tuple) -> list[dict]:
    cohort, arm, seed, checkpoint, conditions, episode_ids, tape_hash = task
    import torch
    torch.set_num_threads(1)
    agent = evaluator.build_agent({"graph_encoder": "single", "hidden_dim": 115}, Path(checkpoint), int(seed))
    rows: list[dict] = []
    for condition in conditions:
        original = evaluator.frozen_env
        evaluator.frozen_env = lambda episode_seed, failure_on, _condition=condition: fixed_env(episode_seed, _condition)
        try:
            for episode_id in episode_ids:
                row, _ = evaluator.evaluate_episode(
                    agent, arm, int(seed), int(episode_id),
                    "nominal" if condition["name"] == "nominal_reference" else "heldout_ood",
                )
                row.update({
                    "protocol": PROTOCOL, "cohort": cohort, "topology_condition": condition["name"],
                    "condition_class": condition["class"], "failed_blue_agent": int(condition["failed_blue_agent"]),
                    "scheduled_failure_onset": int(condition["start_step"]),
                    "scheduled_failure_duration": int(condition["duration_steps"]),
                    "comm_topology_mode": condition["comm_topology_mode"],
                    "checkpoint_sha256": sha256(Path(checkpoint)), "tape_hash": tape_hash,
                })
                rows.append(row)
        finally:
            evaluator.frozen_env = original
    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(dict.fromkeys(field for row in rows for field in row))
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def finite_mean(rows: list[dict], field: str) -> float:
    values = [float(row[field]) for row in rows if math.isfinite(float(row[field]))]
    return sum(values) / len(values) if values else math.nan


def make_summary(raw: list[dict], conditions: list[dict]) -> list[dict]:
    summary: list[dict] = []
    for cohort in ("A", "B"):
        for arm in ("utr_sg", "drtp_sg"):
            for seed in sorted({int(row["train_seed"]) for row in raw if row["cohort"] == cohort and row["method"] == arm}):
                for condition in conditions:
                    subset = [row for row in raw if row["cohort"] == cohort and row["method"] == arm
                              and int(row["train_seed"]) == seed and row["topology_condition"] == condition["name"]]
                    summary.append({
                        "cohort": cohort, "method": arm, "train_seed": seed,
                        "condition": condition["name"], "condition_class": condition["class"],
                        "episodes": len(subset), "J": finite_mean(subset, "J"),
                        "success": finite_mean(subset, "success_at_horizon"),
                        "collision": finite_mean(subset, "collision"),
                        "timeout": finite_mean(subset, "timeout"),
                        "constraint_violation": finite_mean(subset, "constraint_violation"),
                    })
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive-a", type=Path, required=True)
    parser.add_argument("--archive-b", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=20)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("explicit --execute is required")
    if args.output_root.exists():
        raise FileExistsError(f"refusing to overwrite {args.output_root}")
    freeze = load_freeze()
    args.output_root.mkdir(parents=True)
    sources = [
        *extract_sources("A", args.archive_a, args.output_root, freeze),
        *extract_sources("B", args.archive_b, args.output_root, freeze),
    ]
    tape = freeze["fresh_heldout_ood_tape"]
    encoded = json.dumps(tape, sort_keys=True, separators=(",", ":")).encode("utf-8")
    tape_hash = hashlib.sha256(encoded).hexdigest()
    episode_ids = list(range(int(tape["episode_ids"][0]), int(tape["episode_ids"][1]) + 1))
    tasks = [(item["cohort"], item["method"], item["train_seed"], item["checkpoint"], tape["conditions"], episode_ids, tape_hash) for item in sources]
    total = len(tasks) * len(tape["conditions"]) * len(episode_ids)
    print(f"DRTP final held-out/OOD evaluation: cells={len(tasks)}, episodes={total}, workers={min(args.workers, len(tasks))}", flush=True)
    raw: list[dict] = []
    completed = 0
    with ProcessPoolExecutor(max_workers=min(args.workers, len(tasks)), mp_context=mp.get_context("spawn")) as pool:
        futures = [pool.submit(cell, task) for task in tasks]
        for future in as_completed(futures):
            rows = future.result()
            raw.extend(rows)
            completed += len(rows)
            print(f"DRTP final held-out/OOD evaluation progress {completed}/{total} ({100 * completed / total:.2f}%)", flush=True)
    condition_order = {item["name"]: index for index, item in enumerate(tape["conditions"])}
    raw.sort(key=lambda row: (row["cohort"], row["method"], int(row["train_seed"]), condition_order[row["topology_condition"]], int(row["development_episode_id"])))
    write_csv(args.output_root / "raw_episode_metrics.csv", raw)
    summary = make_summary(raw, tape["conditions"])
    write_csv(args.output_root / "per_seed_condition_summary.csv", summary)
    (args.output_root / "evaluation_manifest.json").write_text(json.dumps({
        "protocol": PROTOCOL, "status": "completed", "endpoint": "frozen_final_10m_only",
        "source_archives": {"A": freeze["source_archives"]["A"]["sha256"], "B": freeze["source_archives"]["B"]["sha256"]},
        "source_cells": [{key: value for key, value in item.items() if key != "source_manifest"} for item in sources],
        "tape_protocol": tape["protocol"], "tape_hash": tape_hash, "conditions": tape["conditions"],
        "episodes_per_condition": len(episode_ids), "raw_episode_rows": len(raw), "summary_rows": len(summary),
        "training_started": False, "checkpoint_selection": False, "automatic_algorithm_revision": False,
        "automatic_external_comparator": False, "automatic_6uav": False,
    }, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "completed", "raw_episode_rows": len(raw)}, indent=2), flush=True)


if __name__ == "__main__":
    main()
