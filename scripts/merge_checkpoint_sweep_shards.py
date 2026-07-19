from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.evaluate_3d_checkpoint_sweep import SELECTION_COLUMNS, SUMMARY_COLUMNS, select_checkpoints, write_csv
from scripts.evaluate_ri_gmappo_3d import CSV_COLUMNS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Merge checkpoint-sweep shard directories into one sweep directory.")
    parser.add_argument("--split", choices=("validation", "test"), required=True)
    parser.add_argument("--shard-dir", type=Path, action="append", required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument(
        "--skip-missing",
        action="store_true",
        help="Ignore shard directories that do not yet contain the requested split CSVs.",
    )
    return parser.parse_args()


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def require_or_skip(path: Path, skip_missing: bool) -> bool:
    if path.exists():
        return True
    if skip_missing:
        return False
    raise FileNotFoundError(path)


def summary_key(row: dict[str, str]) -> tuple[str, str, int, int]:
    return (
        row["scenario"],
        row["graph_encoder"],
        int(row["train_seed"]),
        int(row["checkpoint_update"]),
    )


def episode_key(row: dict[str, str]) -> tuple[str, str, int, int]:
    return (
        row.get("split", ""),
        row.get("scenario", ""),
        row.get("graph_encoder", ""),
        row.get("train_seed", ""),
        row.get("checkpoint_update", ""),
        row["checkpoint"],
        row["seed"],
        int(row["episode"]),
        int(row.get("failed_blue_agent", -1)),
    )


def deduplicate(rows: list[dict[str, str]], key_fn) -> list[dict[str, str]]:
    seen: set[tuple[object, ...]] = set()
    unique: list[dict[str, str]] = []
    for row in rows:
        key = key_fn(row)
        if key in seen:
            continue
        seen.add(key)
        unique.append(row)
    return unique


def filter_columns(rows: list[dict[str, str]], columns: tuple[str, ...]) -> list[dict[str, str]]:
    return [{column: row.get(column, "") for column in columns} for row in rows]


def extended_columns(rows: list[dict[str, str]], base_columns: tuple[str, ...]) -> tuple[str, ...]:
    extras: list[str] = []
    base = set(base_columns)
    for row in rows:
        for key in row:
            if key not in base and key not in extras:
                extras.append(key)
    return (*base_columns, *extras)


def write_csv_any(path: Path, rows: list[dict[str, str]], columns: tuple[str, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})


def main() -> None:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    summary_rows: list[dict[str, str]] = []
    episode_rows: list[dict[str, str]] = []
    for shard_dir in args.shard_dir:
        summary_path = shard_dir / f"{args.split}_checkpoint_summary.csv"
        episode_path = shard_dir / f"{args.split}_episode_metrics.csv"
        if not require_or_skip(summary_path, args.skip_missing):
            continue
        summary_rows.extend(read_rows(summary_path))
        if require_or_skip(episode_path, args.skip_missing):
            episode_rows.extend(read_rows(episode_path))

    summary_rows = deduplicate(summary_rows, summary_key)
    summary_rows.sort(key=summary_key)
    episode_rows = deduplicate(episode_rows, episode_key)

    write_csv(args.out_dir / f"{args.split}_checkpoint_summary.csv", filter_columns(summary_rows, SUMMARY_COLUMNS), SUMMARY_COLUMNS)
    if episode_rows:
        episode_columns = extended_columns(episode_rows, CSV_COLUMNS)
        write_csv_any(args.out_dir / f"{args.split}_episode_metrics.csv", episode_rows, episode_columns)

    selected_rows = select_checkpoints(summary_rows)
    write_csv(args.out_dir / f"{args.split}_selected_checkpoints.csv", selected_rows, SELECTION_COLUMNS)

    print(args.out_dir / f"{args.split}_checkpoint_summary.csv")
    if episode_rows:
        print(args.out_dir / f"{args.split}_episode_metrics.csv")
    print(args.out_dir / f"{args.split}_selected_checkpoints.csv")


if __name__ == "__main__":
    main()
