"""Run the frozen PR-DRTP B4 selector and disjoint outcome evaluations."""
from __future__ import annotations

import argparse
import csv
from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import json
import multiprocessing as mp
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]
import run_drtp_sg_development_evaluation as base  # noqa: E402
from pr_drtp_b4_common import ARMS, PROTOCOL, select_seed, selector_score, sha256  # noqa: E402


FREEZE = ROOT / "configs" / "pr_drtp_b4_feasibility_freeze.json"
SELECTOR_TAPE = ROOT / "configs" / "pr_drtp_b4_selector_tape.json"
OUTCOME_TAPE = ROOT / "configs" / "pr_drtp_b4_outcome_tape.json"


def evaluate_asset_cell(task: tuple) -> list[dict]:
    cohort, phase, base_task = task
    rows = base.evaluate_cell(base_task)
    for row in rows:
        row["source_cohort"] = cohort
        row["pr_b4_phase"] = phase
        row["pr_b4_protocol"] = PROTOCOL
    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise RuntimeError(f"refusing empty CSV: {path}")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def summarize(
    rows: list[dict], arms: tuple[str, ...], seeds: list[int], conditions: list[dict], episodes: int
) -> list[dict]:
    summary = []
    for arm in arms:
        for seed in seeds:
            for condition in conditions:
                selected = [
                    row for row in rows
                    if row["method"] == arm
                    and int(row["train_seed"]) == seed
                    and row["topology_condition"] == condition["name"]
                ]
                if len(selected) != episodes:
                    raise RuntimeError(
                        f"incomplete evaluation cell: {arm}/seed{seed}/{condition['name']}"
                    )
                summary.append({
                    "method": arm,
                    "train_seed": seed,
                    "source_cohort": selected[0]["source_cohort"],
                    "condition": condition["name"],
                    **{
                        key: sum(float(row[key]) for row in selected) / episodes
                        for key in ("J", "collision", "timeout", "constraint_violation")
                    },
                })
    return summary


def run_tasks(tasks: list[tuple], workers: int, phase: str, total: int) -> list[dict]:
    rows: list[dict] = []
    done = 0
    with ProcessPoolExecutor(
        max_workers=min(workers, len(tasks)), mp_context=mp.get_context("spawn")
    ) as pool:
        futures = [pool.submit(evaluate_asset_cell, task) for task in tasks]
        for future in as_completed(futures):
            received = future.result()
            rows.extend(received)
            done += len(received)
            print(
                f"PR-DRTP B4 {phase} progress {done}/{total} ({100 * done / total:.2f}%)",
                flush=True,
            )
    return rows


def validate_assets(asset_root: Path, freeze: dict) -> tuple[dict[int, dict], dict]:
    manifest_path = asset_root / "ASSET_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("protocol") != "PR-DRTP-B4-ASSET-MANIFEST-V1":
        raise RuntimeError("invalid B4 asset protocol")
    if manifest.get("freeze_sha256") != sha256(FREEZE):
        raise RuntimeError("asset/freeze hash mismatch")
    records = {(int(row["seed"]), row["arm"]): row for row in manifest["records"]}
    if len(records) != 30:
        raise RuntimeError("B4 requires exactly 30 checkpoint assets")
    inventory: dict[int, dict] = {}
    for expected in freeze["checkpoints"]:
        seed = int(expected["seed"])
        inventory[seed] = {"cohort": expected["cohort"]}
        for arm, key in (("utr_sg", "utr_sha256"), ("drtp_sg", "drtp_sha256")):
            record = records.get((seed, arm))
            if record is None or record["cohort"] != expected["cohort"]:
                raise RuntimeError(f"missing/mismatched asset seed{seed}/{arm}")
            checkpoint = asset_root / expected["cohort"] / arm / f"seed{seed}" / "actor_critic_latest.pt"
            if not checkpoint.is_file() or sha256(checkpoint) != expected[key]:
                raise RuntimeError(f"checkpoint integrity failure: {checkpoint}")
            inventory[seed][arm] = checkpoint
    return inventory, manifest


def task(
    cohort: str, phase: str, arm: str, seed: int, checkpoint: Path,
    episode_ids: list[int], condition: dict, tape_hash: str,
) -> tuple:
    return (
        cohort,
        phase,
        (arm, seed, str(checkpoint), "500k", episode_ids, [condition], tape_hash),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--asset-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=20)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("--execute required")
    if args.workers < 1 or args.workers > 20:
        raise ValueError("workers must be between 1 and 20")
    if args.output_root.exists():
        raise FileExistsError(f"refusing existing output: {args.output_root}")
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    if freeze.get("training_authorized") is not False:
        raise RuntimeError("B4 freeze must prohibit training")
    selector_tape = json.loads(SELECTOR_TAPE.read_text(encoding="utf-8"))
    if sha256(SELECTOR_TAPE) != freeze["selector_tape_sha256"]:
        raise RuntimeError("selector tape hash mismatch")
    if set(selector_tape["episode_ids"]) & set(range(590000, 590100)):
        raise RuntimeError("selector/outcome episode namespaces overlap")
    inventory, asset_manifest = validate_assets(args.asset_root.resolve(), freeze)
    seeds = sorted(inventory)
    args.output_root.mkdir(parents=True)
    selector_dir = args.output_root / "selector"
    selector_dir.mkdir()
    selector_tasks = [
        task(
            inventory[seed]["cohort"], "selector", "drtp_sg", seed,
            inventory[seed]["drtp_sg"], selector_tape["episode_ids"],
            condition, freeze["selector_tape_sha256"],
        )
        for seed in seeds for condition in selector_tape["conditions"]
    ]
    selector_total = len(seeds) * len(selector_tape["conditions"]) * len(selector_tape["episode_ids"])
    print(
        f"PR-DRTP B4 selector: workers={args.workers}, cells={len(selector_tasks)}, "
        f"episodes={selector_total}", flush=True,
    )
    selector_rows = run_tasks(selector_tasks, args.workers, "selector", selector_total)
    selector_rows.sort(key=lambda row: (
        int(row["train_seed"]), row["topology_condition"], int(row["development_episode_id"])
    ))
    write_csv(selector_dir / "raw_episode_metrics.csv", selector_rows)
    selector_summary = summarize(
        selector_rows, ("drtp_sg",), seeds, selector_tape["conditions"],
        len(selector_tape["episode_ids"]),
    )
    write_csv(selector_dir / "condition_summary.csv", selector_summary)
    selector_index: dict[int, dict[str, dict]] = {}
    for row in selector_summary:
        selector_index.setdefault(int(row["train_seed"]), {})[row["condition"]] = row
    scores = {seed: selector_score(selector_index[seed]) for seed in seeds}
    decisions = []
    for population in freeze["populations"]:
        chosen = select_seed(population["members"], scores)
        decisions.append({
            "population": population["population"],
            "members": population["members"],
            "baseline_seed": population["baseline_seed"],
            "selected_seed": chosen,
            "member_scores": {str(seed): scores[seed] for seed in population["members"]},
        })
    selection_payload = {
        "protocol": PROTOCOL,
        "selector_tape_sha256": freeze["selector_tape_sha256"],
        "outcome_tape_loaded_during_selection": False,
        "decisions": decisions,
    }
    (selector_dir / "SELECTION_DECISIONS.json").write_text(
        json.dumps(selection_payload, indent=2) + "\n", encoding="utf-8"
    )

    # Outcome tape is intentionally loaded only after immutable selection decisions exist.
    outcome_tape = json.loads(OUTCOME_TAPE.read_text(encoding="utf-8"))
    if sha256(OUTCOME_TAPE) != freeze["outcome_tape_sha256"]:
        raise RuntimeError("outcome tape hash mismatch")
    if set(selector_tape["episode_ids"]) & set(outcome_tape["episode_ids"]):
        raise RuntimeError("selector and outcome tapes overlap")
    outcome_dir = args.output_root / "outcome"
    outcome_dir.mkdir()
    outcome_tasks = [
        task(
            inventory[seed]["cohort"], "outcome", arm, seed, inventory[seed][arm],
            outcome_tape["episode_ids"], condition, freeze["outcome_tape_sha256"],
        )
        for arm in ARMS for seed in seeds for condition in outcome_tape["conditions"]
    ]
    outcome_total = len(ARMS) * len(seeds) * len(outcome_tape["conditions"]) * len(outcome_tape["episode_ids"])
    print(
        f"PR-DRTP B4 outcome: workers={args.workers}, cells={len(outcome_tasks)}, "
        f"episodes={outcome_total}", flush=True,
    )
    outcome_rows = run_tasks(outcome_tasks, args.workers, "outcome", outcome_total)
    outcome_rows.sort(key=lambda row: (
        row["method"], int(row["train_seed"]), row["topology_condition"],
        int(row["development_episode_id"]),
    ))
    write_csv(outcome_dir / "raw_episode_metrics.csv", outcome_rows)
    outcome_summary = summarize(
        outcome_rows, ARMS, seeds, outcome_tape["conditions"], len(outcome_tape["episode_ids"])
    )
    write_csv(outcome_dir / "condition_summary.csv", outcome_summary)
    manifest = {
        "protocol": PROTOCOL,
        "status": "evaluation_complete",
        "training_started": False,
        "workers": args.workers,
        "seeds": seeds,
        "selector_rows": len(selector_rows),
        "outcome_rows": len(outcome_rows),
        "selector_tape_sha256": freeze["selector_tape_sha256"],
        "outcome_tape_sha256": freeze["outcome_tape_sha256"],
        "asset_manifest_sha256": hashlib.sha256(
            (args.asset_root / "ASSET_MANIFEST.json").read_bytes()
        ).hexdigest(),
        "asset_checkpoint_count": asset_manifest["checkpoint_count"],
        "selection_decisions_sha256": sha256(selector_dir / "SELECTION_DECISIONS.json"),
    }
    (args.output_root / "EVALUATION_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2), flush=True)


if __name__ == "__main__":
    main()
