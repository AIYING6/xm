"""Fixed-endpoint evaluation for the frozen PLR external comparator."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]
from scripts.drtp_plr_external_contracts import ARMS, SEEDS, STEPS, UPDATES, tape_payload  # noqa: E402
from scripts.run_drtp_stabilization_confirmatory_evaluation import cell  # noqa: E402

PROTOCOL = "DRTP-PLR-EXTERNAL-FORMAL-ENDPOINT-EVALUATION-V1"


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""): h.update(chunk)
    return h.hexdigest()


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--trained-root", type=Path, required=True); parser.add_argument("--output-root", type=Path, required=True); parser.add_argument("--workers", type=int, default=15); parser.add_argument("--execute", action="store_true"); args = parser.parse_args()
    if not args.execute: raise SystemExit("explicit --execute is required")
    if args.output_root.exists(): raise FileExistsError(f"refusing to overwrite {args.output_root}")
    tape = json.loads((args.trained_root / "tape" / "tape_manifest.json").read_text(encoding="utf-8"))
    if tape != tape_payload(): raise RuntimeError("invalid frozen PLR tape")
    tasks, manifests = [], []
    for arm in ARMS:
        for seed in SEEDS:
            run = args.trained_root / "runs" / arm / f"seed{seed}"; checkpoint = run / "actor_critic_latest.pt"
            manifest = json.loads((run / "run_manifest.json").read_text(encoding="utf-8"))
            expected = {"status": "completed", "updates": UPDATES, "environment_steps": STEPS, "from_scratch": True, "resume": False, "early_stopping": False, "checkpoint_promotion": False, "endpoint_tape_hash": tape["tape_hash"]}
            if any(manifest.get(key) != value for key, value in expected.items()) or manifest.get("checkpoint_sha256") != digest(checkpoint): raise RuntimeError(f"invalid source run {arm}/seed{seed}")
            tasks.append((arm, seed, str(checkpoint), tape["episode_ids"], tape["conditions"], tape["tape_hash"], PROTOCOL)); manifests.append(manifest)
    total, raw, completed = len(tasks) * len(tape["conditions"]) * len(tape["episode_ids"]), [], 0
    print(f"PLR external comparator evaluation: cells={len(tasks)}, episodes={total}, workers={min(args.workers, len(tasks))}", flush=True)
    with ProcessPoolExecutor(max_workers=min(args.workers, len(tasks)), mp_context=mp.get_context("spawn")) as pool:
        futures = [pool.submit(cell, task) for task in tasks]
        for future in as_completed(futures):
            rows = future.result(); raw.extend(rows); completed += len(rows); print(f"PLR external comparator evaluation progress {completed}/{total} ({100*completed/total:.2f}%)", flush=True)
    order = {row["name"]: index for index, row in enumerate(tape["conditions"])}
    raw.sort(key=lambda row: (row["method"], int(row["train_seed"]), order[row["topology_condition"]], int(row["development_episode_id"])))
    write_csv(args.output_root / "raw_episode_metrics.csv", raw)
    summary = []
    for arm in ARMS:
        for seed in SEEDS:
            for condition in order:
                rows = [row for row in raw if row["method"] == arm and int(row["train_seed"]) == seed and row["topology_condition"] == condition]
                summary.append({"method": arm, "train_seed": seed, "condition": condition, "episodes": len(rows), **{key: sum(float(row[key]) for row in rows) / len(rows) for key in ("J", "success_at_horizon", "collision", "timeout", "constraint_violation", "control_effort")}})
    write_csv(args.output_root / "per_seed_condition_summary.csv", summary)
    (args.output_root / "evaluation_manifest.json").write_text(json.dumps({"protocol": PROTOCOL, "status": "completed", "endpoint": "10m_only", "tape_hash": tape["tape_hash"], "raw_episode_rows": len(raw), "summary_rows": len(summary), "source_run_manifests": manifests, "training_started": False, "automatic_algorithm_revision": False}, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({"status": "completed", "raw_episode_rows": len(raw)}, indent=2), flush=True)


if __name__ == "__main__": main()
