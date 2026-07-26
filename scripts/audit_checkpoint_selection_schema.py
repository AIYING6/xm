from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.evaluate_3d_checkpoint_sweep import SELECTION_COLUMNS, SUMMARY_COLUMNS
from scripts.evaluate_ri_gmappo_3d import CSV_COLUMNS


SCHEMA_PATH = ROOT / "configs" / "paper" / "checkpoint_selection_schema.yaml"


def load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def assert_equal(name: str, actual: tuple[str, ...] | list[str], expected: tuple[str, ...] | list[str]) -> None:
    actual_list = list(actual)
    expected_list = list(expected)
    if actual_list != expected_list:
        raise SystemExit(
            f"{name} mismatch\n"
            f"actual:   {actual_list}\n"
            f"expected: {expected_list}"
        )


def read_header(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        return next(reader)


def audit_file(path: Path, expected: list[str]) -> None:
    if not path.exists():
        raise SystemExit(f"missing CSV for schema audit: {path}")
    assert_equal(path.as_posix(), read_header(path), expected)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit checkpoint-selection schema constants and optional CSV files.")
    parser.add_argument("--summary-csv", type=Path, default=None)
    parser.add_argument("--selection-csv", type=Path, default=None)
    parser.add_argument("--episode-csv", type=Path, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    schema = load_schema()
    assert_equal("SUMMARY_COLUMNS", SUMMARY_COLUMNS, schema["summary_columns"])
    assert_equal("SELECTION_COLUMNS", SELECTION_COLUMNS, schema["selection_columns"])
    episode_columns = [*schema["episode_prefix_columns"], *CSV_COLUMNS]

    if args.summary_csv is not None:
        audit_file(args.summary_csv, schema["summary_columns"])
    if args.selection_csv is not None:
        audit_file(args.selection_csv, schema["selection_columns"])
    if args.episode_csv is not None:
        audit_file(args.episode_csv, episode_columns)

    print("checkpoint selection schema audit passed")
    print(f"summary columns: {len(schema['summary_columns'])}")
    print(f"selection columns: {len(schema['selection_columns'])}")
    print(f"episode columns: {len(episode_columns)}")


if __name__ == "__main__":
    main()
