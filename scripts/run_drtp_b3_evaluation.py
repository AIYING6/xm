"""Final-1M evaluation for the frozen B3 development tape."""
from __future__ import annotations

import argparse, csv, hashlib, json, multiprocessing as mp, sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]
import run_drtp_sg_development_evaluation as base  # noqa: E402

ARMS, SEEDS = ("utr_sg", "drtp_sg"), (2701, 2702, 2703)
PROTOCOL = "DRTP-B-LINE-B3-DEVELOPMENT-EVALUATION-V1"

def evaluate(task):
    return base.evaluate_cell(task)

def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--output-root", type=Path, required=True); parser.add_argument("--workers", type=int, default=6); parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute or args.workers != 6: raise SystemExit("B3 requires --execute and exactly 6 workers")
    tape = json.loads((ROOT / "configs/drtp_b3_development_tape.json").read_text(encoding="utf-8"))
    target = args.output_root / "evaluations" / "final_1m"
    if target.exists() and any(target.iterdir()): raise FileExistsError(target)
    target.mkdir(parents=True, exist_ok=False)
    tasks=[]; manifests=[]
    for arm in ARMS:
      for seed in SEEDS:
        run = args.output_root / "runs" / arm / f"seed{seed}"; manifest=json.loads((run / "run_manifest.json").read_text(encoding="utf-8"))
        if manifest.get("status") != "completed" or manifest.get("protocol") != "DRTP-B-LINE-B3-DEVELOPMENT-V1" or manifest.get("seed") != seed or manifest.get("tape_hash") != tape["tape_hash"]: raise RuntimeError(f"invalid run: {run}")
        checkpoint=run / "actor_critic_latest.pt"
        for condition in tape["conditions"]:
          tasks.append((arm,seed,str(checkpoint),"1m",tape["episode_ids"],[condition],tape["tape_hash"]))
        manifests.append(manifest)
    rows=[]; done=0; total=len(tasks)*len(tape["episode_ids"])
    print(f"B3 evaluation: workers=6, cells={len(tasks)}, episodes={total}", flush=True)
    with ProcessPoolExecutor(max_workers=6, mp_context=mp.get_context("spawn")) as pool:
      futures=[pool.submit(evaluate, task) for task in tasks]
      for future in as_completed(futures):
        part=future.result(); rows.extend(part); done += len(part); print(f"B3 evaluation progress {done}/{total} ({100*done/total:.2f}%)", flush=True)
    order={c["name"]:i for i,c in enumerate(tape["conditions"])}
    rows.sort(key=lambda r:(r["method"],int(r["train_seed"]),order[r["topology_condition"]],int(r["development_episode_id"])))
    if len(rows)!=total: raise RuntimeError(f"B3 row count {len(rows)} != {total}")
    with (target / "raw_episode_metrics.csv").open("w",newline="",encoding="utf-8") as f:
      writer=csv.DictWriter(f,fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    payload={"protocol":PROTOCOL,"status":"completed","raw_rows":len(rows),"cells":len(tasks),"workers":6,"tape_hash":tape["tape_hash"],"source_runs":manifests,"all_original_episodes_retained":True}
    (target / "evaluation_manifest.json").write_text(json.dumps(payload,indent=2,default=str)+"\n",encoding="utf-8")

if __name__ == "__main__": main()
