from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.evaluate_3d_checkpoint_sweep import SELECTION_COLUMNS, SUMMARY_COLUMNS
from scripts.evaluate_ri_gmappo_3d import CSV_COLUMNS


SCHEMA_PATH = ROOT / "configs" / "paper" / "checkpoint_selection_schema.yaml"

ELIGIBLE_UPDATES = [100, 200, 300, 400, 500, 600, 700, 800, 900, 977]


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


def audit_policy(schema: dict) -> None:
    """Check that selection_policy encodes the frozen v1.4 (Case-C) rule."""
    policy = schema.get("selection_policy", {})
    expected_scalars = {
        "selection_metric": "legacy_recovery",
        "selection_success_weight": 100,
        "tie_breaker": "larger checkpoint_update",
        "collision_threshold": 0.0,
        "collision_above_threshold_is_ineligible": True,
        "selection_per_train_seed": True,
        "happo_same_rule": True,
        "checkpoint_sha256_recorded": True,
        "test_must_use_selection_csv": True,
        "validation_must_not_use_test_results": True,
    }
    for key, expected_value in expected_scalars.items():
        actual = policy.get(key)
        if actual != expected_value:
            raise SystemExit(f"selection_policy.{key} mismatch: expected {expected_value!r}, got {actual!r}")

    eligible = policy.get("eligible_snapshots")
    if eligible != ELIGIBLE_UPDATES:
        raise SystemExit(f"selection_policy.eligible_snapshots mismatch: expected {ELIGIBLE_UPDATES}, got {eligible}")

    score = policy.get("score", "")
    if "1000 * post_failure_chain_recovered_mean + 100 * success_mean - post_failure_chain_recovery_steps_mean" not in score:
        raise SystemExit(f"selection_policy.score does not encode the frozen weighted formula: {score!r}")

    ranking = policy.get("ranking", "")
    if "selection_score" not in ranking or "larger checkpoint_update" not in ranking:
        raise SystemExit(f"selection_policy.ranking does not encode the frozen rule: {ranking!r}")

    print("selection_policy audit passed (metric=legacy_recovery, success_weight=100, collision<=0.0 eligible, larger-update tie-break)")


def audit_selection_csv(path: Path, result_root: Path, schema: dict) -> None:
    """Row-level audit of the produced selection CSV."""
    if not path.exists():
        raise SystemExit(f"missing selection CSV: {path}")
    with path.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    policy = schema["selection_policy"]
    eligible = set(policy["eligible_snapshots"])

    seen: set[tuple[str, str, str, str, str]] = set()
    for i, row in enumerate(rows):
        metric = row.get("selection_metric", "")
        if metric != "legacy_recovery":
            raise SystemExit(f"row {i}: selection_metric={metric!r}, expected legacy_recovery")
        try:
            weight = float(row.get("selection_success_weight", ""))
        except ValueError:
            raise SystemExit(f"row {i}: non-numeric selection_success_weight={row.get('selection_success_weight')!r}")
        if weight != 100.0:
            raise SystemExit(f"row {i}: selection_success_weight={weight}, expected 100")
        try:
            upd = int(row["selected_checkpoint_update"])
        except (KeyError, ValueError):
            raise SystemExit(f"row {i}: bad selected_checkpoint_update={row.get('selected_checkpoint_update')!r}")
        if upd not in eligible:
            raise SystemExit(f"row {i}: selected_checkpoint_update={upd} not in eligible {sorted(eligible)}")

        key = (
            row["graph_encoder"],
            row.get("graph_relation_ablation", "none"),
            row.get("graph_message_ablation", "none"),
            row.get("graph_input_ablation", "none"),
            row["train_seed"],
        )
        if key in seen:
            raise SystemExit(f"duplicate selection for method/seed group: {key}")
        seen.add(key)

        cp = Path(row["selected_checkpoint"])
        if not cp.is_absolute():
            cp = result_root / cp
        if not cp.exists():
            raise SystemExit(f"row {i}: selected checkpoint file missing: {cp}")
        declared_sha = row.get("checkpoint_sha256", "")
        if not declared_sha:
            raise SystemExit(f"row {i}: missing checkpoint_sha256")
        actual_sha = hashlib.sha256(cp.read_bytes()).hexdigest().upper()
        if actual_sha != declared_sha.upper():
            raise SystemExit(f"row {i}: checkpoint SHA mismatch for {cp}\n  declared {declared_sha}\n  actual   {actual_sha}")

    print(f"selection CSV row checks passed: {len(rows)} rows (metric/weight/eligible-update/group-uniqueness/file+SHA)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit checkpoint-selection schema constants, policy, and optional CSV files.")
    parser.add_argument("--summary-csv", type=Path, default=None)
    parser.add_argument("--selection-csv", type=Path, default=None)
    parser.add_argument("--episode-csv", type=Path, default=None)
    parser.add_argument("--result-root", type=Path, default=ROOT, help="Root used to resolve selected checkpoint paths (default: repo ROOT).")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    schema = load_schema()
    assert_equal("SUMMARY_COLUMNS", SUMMARY_COLUMNS, schema["summary_columns"])
    assert_equal("SELECTION_COLUMNS", SELECTION_COLUMNS, schema["selection_columns"])
    episode_columns = [*schema["episode_prefix_columns"], *CSV_COLUMNS]
    audit_policy(schema)

    if args.summary_csv is not None:
        audit_file(args.summary_csv, schema["summary_columns"])
    if args.selection_csv is not None:
        audit_file(args.selection_csv, schema["selection_columns"])
        audit_selection_csv(args.selection_csv, args.result_root, schema)
    if args.episode_csv is not None:
        audit_file(args.episode_csv, episode_columns)

    print("checkpoint selection schema audit passed")
    print(f"summary columns: {len(schema['summary_columns'])}")
    print(f"selection columns: {len(schema['selection_columns'])}")
    print(f"episode columns: {len(episode_columns)}")


if __name__ == "__main__":
    main()
