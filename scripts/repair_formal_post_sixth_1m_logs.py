from __future__ import annotations

import argparse
import csv
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
METHODS = (
    "no_graph",
    "single_graph",
    "param_matched_single",
    "ea_rg_mappo_s_gate_prior",
    "happo",
)
SEEDS = (0, 1, 2)


def parse_update(row: dict[str, str]) -> int:
    try:
        return int(row.get("update", "0"))
    except ValueError:
        return -1


def read_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames or []), list(reader)


def is_nonmonotonic(updates: list[int]) -> bool:
    return any(b < a for a, b in zip(updates, updates[1:]))


def normalize_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    by_update: dict[int, dict[str, str]] = {}
    for row in rows:
        update = parse_update(row)
        if update < 0:
            continue
        by_update[update] = row
    return [by_update[update] for update in sorted(by_update)]


def repair_log(path: Path, dry_run: bool) -> dict[str, str | int | bool]:
    if not path.exists():
        return {
            "path": str(path),
            "status": "missing",
            "rows_before": 0,
            "rows_after": 0,
            "max_update": 0,
            "duplicates_removed": 0,
            "nonmonotonic": False,
        }

    fieldnames, rows = read_rows(path)
    updates = [parse_update(row) for row in rows]
    normalized = normalize_rows(rows)
    duplicate_count = len(rows) - len({update for update in updates if update >= 0})
    nonmonotonic = is_nonmonotonic(updates)
    needs_repair = duplicate_count > 0 or nonmonotonic or len(normalized) != len(rows)
    max_seen = max([parse_update(row) for row in normalized], default=0)

    if needs_repair and not dry_run:
        backup = path.with_suffix(path.suffix + ".bak_unsorted")
        if not backup.exists():
            shutil.copy2(path, backup)
        with path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(normalized)

    return {
        "path": str(path),
        "status": "repaired" if needs_repair and not dry_run else ("would-repair" if needs_repair else "ok"),
        "rows_before": len(rows),
        "rows_after": len(normalized),
        "max_update": max_seen,
        "duplicates_removed": duplicate_count,
        "nonmonotonic": nonmonotonic,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Normalize formal post-sixth 1M train_log.csv files after interrupted overlapping chunks."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=ROOT / "results" / "paper_config_runs" / "formal_budget_post_sixth_freeze",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    print("| Method | Seed | Status | Rows before | Rows after | Max update | Duplicates removed | Nonmonotonic |")
    print("|---|---:|---|---:|---:|---:|---:|---|")
    for method in METHODS:
        for seed in SEEDS:
            path = args.root / method / f"ppo_seed{seed}_1m" / "train_log.csv"
            result = repair_log(path, args.dry_run)
            print(
                f"| {method} | {seed} | {result['status']} | {result['rows_before']} | "
                f"{result['rows_after']} | {result['max_update']} | "
                f"{result['duplicates_removed']} | {result['nonmonotonic']} |"
            )


if __name__ == "__main__":
    main()
