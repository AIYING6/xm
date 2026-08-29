"""Evaluate frozen S1 UTR/original-DRTP checkpoints plus S2 Conservative-DRTP."""
from __future__ import annotations

import argparse, csv, json, multiprocessing as mp, sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]
import run_drtp_sg_development_evaluation as base  # noqa: E402

ARMS, SEEDS = ("utr_sg", "drtp_sg", "conservative_drtp_sg"), (2901, 2902, 2903)
TAPE = ROOT / "configs" / "drtp_stabilization_s1_development_tape.json"

def average(rows: list[dict], key: str) -> float: return sum(float(row[key]) for row in rows) / len(rows)

def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--output-root", type=Path, required=True); parser.add_argument("--s1-root", type=Path, required=True); parser.add_argument("--workers", type=int, default=3); parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute or args.workers != 3: raise SystemExit("S2 requires --execute and exactly 3 workers")
    tape = json.loads(TAPE.read_text(encoding="utf-8")); target = args.output_root / "evaluations" / "final_05m"
    if target.exists() and any(target.iterdir()): raise FileExistsError(target)
    target.mkdir(parents=True, exist_ok=False); tasks, manifests = [], []
    roots = {"utr_sg": args.s1_root, "drtp_sg": args.s1_root, "conservative_drtp_sg": args.output_root}
    # S2 does not rerun the six frozen S1 baseline evaluations.  Their raw
    # fixed-tape records are copied verbatim into the combined S2 evidence
    # product; only the three new Conservative-DRTP checkpoints are rolled out.
    source_eval = args.s1_root / "evaluations" / "final_05m"
    source_manifest = json.loads((source_eval / "evaluation_manifest.json").read_text(encoding="utf-8"))
    source_rows = list(csv.DictReader((source_eval / "raw_episode_metrics.csv").open(newline="", encoding="utf-8")))
    source_summary = list(csv.DictReader((source_eval / "per_seed_condition_summary.csv").open(newline="", encoding="utf-8")))
    if source_manifest.get("status") != "completed" or source_manifest.get("raw_rows") != 3000 or len(source_rows) != 3000:
        raise RuntimeError("invalid frozen S1 baseline evaluation")
    for arm in ARMS:
        for seed in SEEDS:
            run = roots[arm] / "runs" / arm / f"seed{seed}"; manifest = json.loads((run / "run_manifest.json").read_text(encoding="utf-8"))
            expected = "DRTP-STABILIZATION-S2-STAGE1-V1" if arm == "conservative_drtp_sg" else "DRTP-STABILIZATION-S1-STAGE1-V1"
            if manifest.get("status") != "completed" or manifest.get("protocol") != expected or manifest.get("seed") != seed or manifest.get("updates") != 1953 or manifest.get("tape_hash") != tape["tape_hash"]: raise RuntimeError(f"invalid S2 evaluation source: {run}")
            if arm == "conservative_drtp_sg":
                for condition in tape["conditions"]: tasks.append((arm, seed, str(run / "actor_critic_latest.pt"), "500k", tape["episode_ids"], [condition], tape["tape_hash"]))
            manifests.append({"arm": arm, "seed": seed, "root": str(roots[arm]), "manifest": manifest})
    total, done, rows = len(tasks) * len(tape["episode_ids"]), 0, list(source_rows)
    print(f"S2 evaluation: workers=3, new_cells={len(tasks)}, new_episodes={total}; reusing 3000 frozen baseline records", flush=True)
    with ProcessPoolExecutor(max_workers=3, mp_context=mp.get_context("spawn")) as pool:
        futures = [pool.submit(base.evaluate_cell, task) for task in tasks]
        for future in as_completed(futures):
            part = future.result(); rows.extend(part); done += len(part); print(f"S2 evaluation progress {done}/{total} ({100*done/total:.2f}%)", flush=True)
    order = {condition["name"]: index for index, condition in enumerate(tape["conditions"])}
    rows.sort(key=lambda row: (row["method"], int(row["train_seed"]), order[row["topology_condition"]], int(row["development_episode_id"])))
    if len(rows) != total + 3000: raise RuntimeError(f"S2 raw row count {len(rows)} != {total + 3000}")
    with (target / "raw_episode_metrics.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    summary = list(source_summary)
    for arm in ("conservative_drtp_sg",):
        for seed in SEEDS:
            for condition in tape["conditions"]:
                part=[row for row in rows if row["method"] == arm and int(row["train_seed"]) == seed and row["topology_condition"] == condition["name"]]
                if len(part) != 100: raise RuntimeError(f"incomplete S2 cell {arm}/seed{seed}/{condition['name']}")
                summary.append({"method":arm,"train_seed":seed,"condition":condition["name"],"J":average(part,"J"),"collision":average(part,"collision"),"timeout":average(part,"timeout"),"constraint_violation":average(part,"constraint_violation")})
    with (target / "per_seed_condition_summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer=csv.DictWriter(handle, fieldnames=list(summary[0])); writer.writeheader(); writer.writerows(summary)
    payload={"protocol":"DRTP-STABILIZATION-S2-STAGE1-EVALUATION-V1","status":"completed","raw_rows":len(rows),"cells":len(ARMS)*len(SEEDS)*len(tape["conditions"]),"new_s2_cells":len(tasks),"new_s2_episodes":total,"reused_s1_baseline_records":len(source_rows),"episodes_per_condition":100,"workers":3,"tape_hash":tape["tape_hash"],"source_runs":manifests,"all_original_episodes_retained":True,"automatic_follow_on_started":False}
    (target / "evaluation_manifest.json").write_text(json.dumps(payload,indent=2,default=str)+"\n",encoding="utf-8")

if __name__ == "__main__": main()
