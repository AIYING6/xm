from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

import torch


ROOT = Path(__file__).resolve().parents[1]
METHODS = (
    "no_graph",
    "single_graph",
    "param_matched_single",
    "ea_rg_mappo_s_gate_prior",
    "happo",
)
SEEDS = (0, 1, 2)

TARGET_UPDATES = 977


def read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def parse_update(row: dict[str, str]) -> int:
    try:
        return int(row.get("update", "0"))
    except (ValueError, TypeError):
        return 0


def max_update(rows: list[dict[str, str]]) -> int:
    if not rows:
        return 0
    return max(parse_update(row) for row in rows)


def duplicate_count(rows: list[dict[str, str]]) -> int:
    updates = [parse_update(row) for row in rows]
    return len(updates) - len(set(updates))


def out_of_order_count(rows: list[dict[str, str]]) -> int:
    updates = [parse_update(row) for row in rows]
    return sum(1 for a, b in zip(updates, updates[1:]) if b < a)


def latest_eval(rows: list[dict[str, str]]) -> dict[str, str] | None:
    eval_rows = [row for row in rows if row.get("eval_success_rate", "") != ""]
    if not eval_rows:
        return None
    return max(enumerate(eval_rows), key=lambda item: (parse_update(item[1]), item[0]))[1]


def training_state_path(run_dir: Path, method: str) -> Path:
    if method == "happo":
        return run_dir / "happo_training_state_latest.pt"
    return run_dir / "actor_critic_training_state_latest.pt"


def latest_actor_path(run_dir: Path, method: str) -> Path:
    if method == "happo":
        return run_dir / "happo_latest.pt"
    return run_dir / "actor_critic_latest.pt"


def inspect_training_checkpoint(run_dir: Path, method: str) -> dict:
    """Load the training-state checkpoint on CPU and report authoritative fields.

    The training-state checkpoint (not train_log.csv) is the authoritative resume
    source because it carries optimizer/RNG state. train_log.csv is audit-only.
    """
    state = training_state_path(run_dir, method)
    info = {
        "training_state_exists": False,
        "model_state_exists": False,
        "optimizer_state_exists": False,
        "checkpoint_loadable": False,
        "training_checkpoint_update": 0,
        "has_update_field": False,
    }
    if not state.exists():
        return info
    info["training_state_exists"] = True
    try:
        checkpoint = torch.load(state, map_location="cpu", weights_only=False)
    except Exception:
        return info
    info["checkpoint_loadable"] = True
    info["has_update_field"] = "update" in checkpoint
    info["training_checkpoint_update"] = int(checkpoint.get("update", 0))
    info["model_state_exists"] = bool(checkpoint.get("model_state") or checkpoint.get("actor_critic_state"))
    info["optimizer_state_exists"] = bool(
        checkpoint.get("optimizer_state") or checkpoint.get("optimizer_states")
    )
    return info


def model_state_exists(run_dir: Path, method: str) -> bool:
    return latest_actor_path(run_dir, method).exists()


def bc_exists(run_dir: Path, method: str) -> bool:
    # run_dir name pattern: ppo_seed<seed>_1m ; method is the parent dir name.
    seed = "0"
    m = re.search(r"seed(\d+)", run_dir.name)
    if m:
        seed = m.group(1)
    bc_name = "happo_bc_latest.pt" if method == "happo" else "actor_critic_latest.pt"
    bc_path = run_dir.parent.parent / method / f"bc_seed{seed}" / bc_name
    return bc_path.exists()


def snapshot_exists(run_dir: Path, method: str) -> bool:
    pattern = "happo_update_*.pt" if method == "happo" else "actor_critic_update_*.pt"
    return any(run_dir.glob(pattern))


def decide_status(
    *,
    log_max_update: int,
    dup: int,
    ooo: int,
    ckpt: dict,
    target_updates: int,
    bc_exists: bool = False,
    snapshot_exists: bool = False,
) -> str:
    if log_max_update >= target_updates:
        return "COMPLETE"
    # FRESH: no training state, no log, no PPO snapshot, but a valid BC init exists.
    # This is the intended pre-PPO state; gating allows FRESH before launch.
    if (
        not ckpt["training_state_exists"]
        and log_max_update == 0
        and not snapshot_exists
        and bc_exists
    ):
        return "FRESH"
    # PARTIAL_FRESH_STATE-like: no training state but partial artifacts exist.
    if not ckpt["training_state_exists"] and (log_max_update > 0 or snapshot_exists):
        return "PARTIAL_FRESH_STATE"
    if not ckpt["training_state_exists"]:
        return "MISSING_TRAINING_STATE"
    if not ckpt["checkpoint_loadable"]:
        return "CHECKPOINT_LOAD_FAILED"
    if not ckpt["model_state_exists"]:
        return "MISSING_MODEL_STATE"
    if not ckpt["has_update_field"] or ckpt["training_checkpoint_update"] == 0:
        return "MISSING_UPDATE_FIELD"
    if not ckpt["optimizer_state_exists"]:
        return "MISSING_OPTIMIZER_STATE"
    if dup > 0 or ooo > 0:
        return "DIRTY_LOG"
    if log_max_update < ckpt["training_checkpoint_update"]:
        return "LOG_BEHIND_CHECKPOINT"
    if log_max_update > ckpt["training_checkpoint_update"]:
        return "LOG_AHEAD_OF_CHECKPOINT"
    return "READY"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Check post-sixth-freeze formal 1M PPO three-way consistency gate."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=ROOT / "results" / "paper_config_runs" / "formal_budget_post_sixth_freeze_v1",
    )
    parser.add_argument("--target-updates", type=int, default=TARGET_UPDATES)
    args = parser.parse_args()

    rows_out: list[dict[str, str]] = []
    for method in METHODS:
        for seed in SEEDS:
            run_dir = args.root / method / f"ppo_seed{seed}_1m"
            rows = read_rows(run_dir / "train_log.csv")
            log_max_update = max_update(rows)
            dup = duplicate_count(rows)
            ooo = out_of_order_count(rows)
            pct = 100.0 * float(log_max_update) / float(args.target_updates)
            eval_row = latest_eval(rows)
            ckpt = inspect_training_checkpoint(run_dir, method)
            ckpt["model_state_exists"] = model_state_exists(run_dir, method)
            has_bc = bc_exists(run_dir, method)
            has_snapshot = snapshot_exists(run_dir, method)

            status = decide_status(
                log_max_update=log_max_update,
                dup=dup,
                ooo=ooo,
                ckpt=ckpt,
                target_updates=args.target_updates,
                bc_exists=has_bc,
                snapshot_exists=has_snapshot,
            )
            resume_start_update = (
                ckpt["training_checkpoint_update"] if status in ("READY", "LOG_BEHIND_CHECKPOINT") else 0
            )

            rows_out.append(
                {
                    "method": method,
                    "seed": str(seed),
                    "log_max_update": str(log_max_update),
                    "training_checkpoint_update": str(ckpt["training_checkpoint_update"]),
                    "resume_start_update": str(resume_start_update),
                    "duplicate_count": str(dup),
                    "out_of_order_count": str(ooo),
                    "training_state_exists": "yes" if ckpt["training_state_exists"] else "no",
                    "model_state_exists": "yes" if ckpt["model_state_exists"] else "no",
                    "optimizer_state_exists": "yes" if ckpt["optimizer_state_exists"] else "no",
                    "checkpoint_loadable": "yes" if ckpt["checkpoint_loadable"] else "no",
                    "status": status,
                    "percent": f"{pct:.1f}",
                    "last_eval_success": "" if eval_row is None else eval_row.get("eval_success_rate", ""),
                    "last_eval_collision": "" if eval_row is None else eval_row.get("eval_collision_rate", ""),
                    "last_eval_timeout": "" if eval_row is None else eval_row.get("eval_timeout_rate", ""),
                    "run_dir": str(run_dir.relative_to(ROOT)),
                }
            )

    total = len(rows_out)
    fresh = sum(1 for r in rows_out if r["status"] == "FRESH")
    ready = sum(1 for r in rows_out if r["status"] == "READY")
    complete = sum(1 for r in rows_out if r["status"] == "COMPLETE")
    blocked = sum(1 for r in rows_out if r["status"] not in ("FRESH", "READY", "COMPLETE"))
    inconsistent = [
        r for r in rows_out
        if r["status"] in ("READY", "LOG_BEHIND_CHECKPOINT", "LOG_AHEAD_OF_CHECKPOINT")
        and r["log_max_update"] != r["training_checkpoint_update"]
    ]

    print(f"target_updates: {args.target_updates}")
    print(f"total_runs: {total}")
    print(f"FRESH: {fresh}")
    print(f"READY: {ready}")
    print(f"COMPLETE: {complete}")
    print(f"BLOCKED: {blocked}")
    print(f"inconsistent_log_vs_ckpt: {len(inconsistent)}")
    print()
    print(
        "| Method | Seed | Log max | Ckpt update | Resume start | Dup | OOO | "
        "State? | Model? | Optim? | Loadable? | Status |"
    )
    print("|---|---:|---:|---:|---:|---:|---:|---|---|---|---|---|")
    for r in rows_out:
        print(
            f"| {r['method']} | {r['seed']} | {r['log_max_update']} | "
            f"{r['training_checkpoint_update']} | {r['resume_start_update']} | "
            f"{r['duplicate_count']} | {r['out_of_order_count']} | "
            f"{r['training_state_exists']} | {r['model_state_exists']} | "
            f"{r['optimizer_state_exists']} | {r['checkpoint_loadable']} | {r['status']} |"
        )

    print("\n| Method | Seed | Checkpoint | Last eval success | Collision | Timeout |")
    print("|---|---:|---|---:|---:|---:|")
    for r in rows_out:
        print(
            f"| {r['method']} | {r['seed']} | {r['model_state_exists']} | "
            f"{r['last_eval_success']} | {r['last_eval_collision']} | {r['last_eval_timeout']} |"
        )

    if blocked:
        print("\nBLOCKED runs (must NOT resume until resolved):")
        for r in rows_out:
            if r["status"] not in ("FRESH", "READY", "COMPLETE"):
                print(f"- {r['method']} seed{r['seed']}: {r['status']}")
    if inconsistent:
        print("\nINCONSISTENT (log_max_update != training_checkpoint_update):")
        for r in inconsistent:
            print(
                f"- {r['method']} seed{r['seed']}: "
                f"log={r['log_max_update']} ckpt={r['training_checkpoint_update']}"
            )

    # Gate summary for caller scripts.
    # Two-stage gate:
    #  - pre-PPO (after BC): allow FRESH=15, BLOCKED=0
    #  - post-launch: require READY+COMPLETE=15, FRESH=0, BLOCKED=0
    print(
        f"\nGATE: FRESH={fresh} READY+COMPLETE={ready + complete}/{total}, "
        f"BLOCKED={blocked}, inconsistent={len(inconsistent)}"
    )
    if blocked or inconsistent:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
