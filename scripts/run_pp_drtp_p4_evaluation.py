"""Evaluate frozen PP-DRTP P4 final 0.5M checkpoints only."""
from __future__ import annotations
import argparse, csv, hashlib, json, multiprocessing as mp, sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]
import run_drtp_sg_development_evaluation as base

ARMS = ("utr_sg", "drtp_sg", "pp_drtp_sg")
SEEDS = (3501, 3502, 3503, 3504, 3505)
PROTOCOL = "PP-DRTP-P4-INDEPENDENT-VALIDATION-V1"
TAPE = ROOT / "configs" / "pp_drtp_p4_validation_tape.json"

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=15)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute or args.workers != 15:
        raise SystemExit("frozen workers=15 and --execute required")
    tape = json.loads(TAPE.read_text())
    tape_hash = hashlib.sha256(TAPE.read_bytes()).hexdigest()
    out = args.output_root / "evaluations" / "final_05m"
    if out.exists():
        raise FileExistsError("refusing evaluation rerun")
    out.mkdir(parents=True)
    tasks = []
    for arm in ARMS:
        for seed in SEEDS:
            run = args.output_root / "runs" / arm / f"seed{seed}"
            manifest = json.loads((run / "run_manifest.json").read_text())
            if (manifest.get("status") != "completed" or
                    manifest.get("protocol") != PROTOCOL or
                    manifest.get("tape_sha256") != tape_hash):
                raise RuntimeError(f"invalid run {run}")
            for condition in tape["conditions"]:
                tasks.append((arm, seed, str(run / "actor_critic_latest.pt"),
                              "500k", tape["episode_ids"], [condition], tape_hash))
    rows, done = [], 0
    total = len(tasks) * 100
    print(f"PP P4 evaluation: workers=15, cells={len(tasks)}, episodes={total}", flush=True)
    with ProcessPoolExecutor(max_workers=15, mp_context=mp.get_context("spawn")) as pool:
        futures = [pool.submit(base.evaluate_cell, task) for task in tasks]
        for future in as_completed(futures):
            rows += future.result()
            done += 100
            print(f"PP P4 evaluation progress {done}/{total} ({100*done/total:.2f}%)", flush=True)
    rows.sort(key=lambda row: (row["method"], int(row["train_seed"]),
                               row["topology_condition"], int(row["development_episode_id"])))
    with (out / "raw_episode_metrics.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    summary = []
    for arm in ARMS:
        for seed in SEEDS:
            for condition in tape["conditions"]:
                selected = [row for row in rows if row["method"] == arm and
                            int(row["train_seed"]) == seed and
                            row["topology_condition"] == condition["name"]]
                if len(selected) != 100:
                    raise RuntimeError("incomplete evaluation cell")
                summary.append({"method": arm, "train_seed": seed,
                    "condition": condition["name"], **{
                        key: sum(float(row[key]) for row in selected) / 100
                        for key in ("J", "collision", "timeout", "constraint_violation")}})
    with (out / "condition_summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary[0]))
        writer.writeheader(); writer.writerows(summary)

if __name__ == "__main__":
    main()
