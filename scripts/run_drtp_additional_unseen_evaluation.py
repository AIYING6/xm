"""Evaluate frozen UTR/DRTP checkpoints on one additional unseen-condition tape."""
from __future__ import annotations

import argparse
import csv
from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import json
import math
import multiprocessing as mp
from pathlib import Path
import statistics
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))

import run_drtp_sg_development_evaluation as base  # noqa: E402
from create_drtp_additional_unseen_tape import CONDITIONS, EPISODES, TAPE_START, frozen_manifest  # noqa: E402


PROTOCOL = "DRTP-ADDITIONAL-UNSEEN-CONDITION-EVALUATION-V1"
ARMS = ("utr_sg", "drtp_sg")
COHORTS = {
    "formal_2301_2305": {"seeds": (2301, 2302, 2303, 2304, 2305), "protocol": "DRTP-UTR-Q2-FORMAL-PAIRED-5SEED-TRAINING-V1"},
    "independent_2401_2405": {"seeds": (2401, 2402, 2403, 2404, 2405), "protocol": "DRTP-SNR-Q2-MECHANISM-COMPARATOR-TRAINING-V1"},
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise RuntimeError(f"refusing to write empty CSV: {path}")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def mean(rows: list[dict], field: str) -> float:
    values = [float(row[field]) for row in rows if math.isfinite(float(row[field]))]
    return statistics.mean(values) if values else math.nan


def load_sources(cohort: str, root: Path) -> list[dict]:
    config, sources = COHORTS[cohort], []
    for arm in ARMS:
        for seed in config["seeds"]:
            run_dir = root / "runs" / arm / f"seed{seed}"
            manifest_path, checkpoint = run_dir / "run_manifest.json", run_dir / "actor_critic_latest.pt"
            if not manifest_path.is_file() or not checkpoint.is_file():
                raise FileNotFoundError(f"missing final asset: {run_dir}")
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            checks = {
                "completed": manifest.get("status") == "completed",
                "protocol": manifest.get("protocol") == config["protocol"],
                "seed": int(manifest.get("seed")) == seed,
                "parameters": manifest.get("parameter_count") == 116728,
                "from_scratch": manifest.get("from_scratch") is True,
                "strict_continuous": manifest.get("strict_continuous_trajectory") is True,
                "runtime_persistence": manifest.get("runtime_state_checkpointing") is True,
                "no_canonical": manifest.get("canonical_seeds_used") is False,
            }
            expected_hash = manifest.get("final_checkpoint_sha256")
            if expected_hash is not None:
                checks["checkpoint_hash"] = sha256(checkpoint) == expected_hash
            if not all(checks.values()):
                raise RuntimeError(f"source validation failed for {cohort}/{arm}/seed{seed}: {checks}")
            sources.append({"cohort": cohort, "arm": arm, "seed": seed, "checkpoint": checkpoint,
                            "checkpoint_sha256": sha256(checkpoint), "manifest": manifest})
    return sources


def worker(task: tuple[tuple, int]) -> list[dict]:
    base_task, gpu_id = task
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.set_device(gpu_id)
    except ImportError:  # pragma: no cover
        pass
    cohort, arm, seed, checkpoint, episode_ids, conditions, tape_hash = base_task
    rows = base.evaluate_cell((arm, seed, checkpoint, "10m", episode_ids, conditions, tape_hash))
    for row in rows:
        row.update({"protocol": PROTOCOL, "training_cohort": cohort, "inference_unit": "training_seed"})
    return rows


def condition_rows(raw_rows: list[dict], tape: dict) -> list[dict]:
    by_key: dict[tuple[str, str, int, str], list[dict]] = {}
    for row in raw_rows:
        by_key.setdefault((row["training_cohort"], row["method"], int(row["train_seed"]), row["topology_condition"]), []).append(row)
    result = []
    for (cohort, arm, seed, condition), rows in sorted(by_key.items()):
        if len(rows) != EPISODES:
            raise RuntimeError(f"incomplete cell: {cohort}/{arm}/seed{seed}/{condition}")
        onset = next(item["start_step"] for item in tape["conditions"] if item["name"] == condition)
        risk = [row for row in rows if int(float(row["terminal_step"])) >= onset]
        pre = [row for row in rows if float(row["collision"]) == 1.0 and int(float(row["terminal_step"])) < onset]
        result.append({
            "training_cohort": cohort, "arm": arm, "seed": seed, "condition": condition,
            "J": mean(rows, "J"), "collision": mean(rows, "collision"), "timeout": mean(rows, "timeout"),
            "constraint_violation": mean(rows, "constraint_violation"), "risk_set_size": len(risk),
            "survival_to_onset_fraction": len(risk) / len(rows),
            "failure_trigger_success_rate_risk_set": mean(risk, "failure_exposed") if risk else math.nan,
            "pretrigger_collision_count": len(pre), "pretrigger_collision_rate": len(pre) / len(rows),
            "failure_exposure_all_scheduled": mean(rows, "failure_exposed"),
        })
    return result


def paired_effects(summary: list[dict]) -> list[dict]:
    index = {(row["training_cohort"], row["arm"], int(row["seed"]), row["condition"]): row for row in summary}
    result = []
    for cohort, config in COHORTS.items():
        for condition in CONDITIONS:
            for metric in ("J", "collision", "timeout", "constraint_violation"):
                values = [float(index[(cohort, "drtp_sg", seed, condition)][metric]) - float(index[(cohort, "utr_sg", seed, condition)][metric]) for seed in config["seeds"]]
                result.append({"training_cohort": cohort, "condition": condition, "metric": metric,
                               "n_training_seeds": len(values), "mean_drtp_minus_utr": statistics.mean(values),
                               "median_drtp_minus_utr": statistics.median(values), "wins_over_zero": sum(value > 0 for value in values),
                               "worst_drtp_minus_utr": min(values), "paired_values": json.dumps(values)})
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--formal-root", type=Path, required=True)
    parser.add_argument("--independent-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--gpu-ids", default="0")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("NO-GO: explicit --execute is required")
    if args.workers < 1 or args.output_root.exists() and any(args.output_root.iterdir()):
        raise RuntimeError("workers must be positive and output root must be new or empty")
    tape_path = args.output_root / "additional_unseen_tape_manifest.json"
    if not tape_path.is_file():
        raise FileNotFoundError("freeze the unseen tape before evaluation")
    tape = json.loads(tape_path.read_text(encoding="utf-8"))
    expected_tape = frozen_manifest()
    if tape.get("tape_hash") != expected_tape["tape_hash"]:
        raise RuntimeError("unseen tape manifest differs from contract")
    sources = load_sources("formal_2301_2305", args.formal_root) + load_sources("independent_2401_2405", args.independent_root)
    gpu_ids = [int(value) for value in args.gpu_ids.split(",") if value.strip()]
    tasks = [(source["cohort"], source["arm"], source["seed"], str(source["checkpoint"]), tape["episode_ids"], tape["conditions"], tape["tape_hash"]) for source in sources]
    assigned = [(task, gpu_ids[index % len(gpu_ids)]) for index, task in enumerate(tasks)]
    total, completed, raw = len(tasks) * len(tape["conditions"]) * EPISODES, 0, []
    print(f"additional unseen evaluation: workers={min(args.workers, len(assigned))}, cells={len(tasks)}, episodes={total}", flush=True)
    with ProcessPoolExecutor(max_workers=min(args.workers, len(assigned)), mp_context=mp.get_context("spawn")) as pool:
        futures = [pool.submit(worker, task) for task in assigned]
        for future in as_completed(futures):
            rows = future.result(); raw.extend(rows); completed += len(rows)
            print(f"additional unseen evaluation progress {completed}/{total} ({100 * completed / total:.2f}%)", flush=True)
    if len(raw) != total:
        raise RuntimeError(f"expected {total} raw rows, found {len(raw)}")
    order = {name: index for index, name in enumerate(CONDITIONS)}
    raw.sort(key=lambda row: (row["training_cohort"], row["method"], int(row["train_seed"]), order[row["topology_condition"]], int(row["development_episode_id"])))
    write_csv(args.output_root / "raw_episode_metrics.csv", raw)
    summary = condition_rows(raw, tape); write_csv(args.output_root / "per_seed_condition_summary.csv", summary)
    effects = paired_effects(summary); write_csv(args.output_root / "paired_effects_by_cohort_condition.csv", effects)
    manifest = {"protocol": PROTOCOL, "status": "completed", "training_started": False, "raw_rows": len(raw), "expected_rows": total,
                "workers": min(args.workers, len(assigned)), "gpu_ids": gpu_ids, "tape_hash": tape["tape_hash"],
                "all_scheduled_episodes_retained": True, "cross_cohort_pooling_prohibited": True,
                "source_checkpoints": [{key: source[key] for key in ("cohort", "arm", "seed", "checkpoint_sha256")} for source in sources]}
    (args.output_root / "evaluation_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
