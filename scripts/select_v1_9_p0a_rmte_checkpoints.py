"""Verify P0-A immutable records and apply the frozen RMTE selector read-only."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.simple_ri_gmappo import (  # noqa: E402
    rmte_selector_key,
    summarize_validation_event_records,
)

REQUIRED_METRICS = (
    "eval_rmte80", "eval_establishment_probability80", "eval_terminal_failure_incidence80",
    "eval_active_not_established_probability80", "eval_rmte220",
    "eval_establishment_probability220", "eval_terminal_failure_incidence220",
    "eval_active_not_established_probability220",
)
REQUIRED_RECORD_FIELDS = (
    "episode_seed", "failure_onset_step", "event_observed", "first_stable_establishment_step",
    "event_time", "termination_reason", "terminal_failure_observed",
    "terminal_failure_time", "terminal_step",
)


def fail(message: str) -> None:
    raise RuntimeError(f"P0_A_IMMUTABLE_ARTIFACT_VERIFICATION_FAILED: {message}")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_manifest(run_dir: Path) -> list[dict]:
    path = run_dir / "snapshot_manifest.jsonl"
    if not path.exists():
        fail(f"missing snapshot manifest: {path}")
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not rows:
        fail(f"empty snapshot manifest: {path}")
    return rows


def read_records(path: Path) -> list[dict]:
    rows = list(csv.DictReader(path.open(encoding="utf-8", newline="")))
    if not rows or any(not set(REQUIRED_RECORD_FIELDS).issubset(row) for row in rows):
        fail(f"missing P0-A event-record fields: {path}")
    parsed = []
    for row in rows:
        parsed.append({
            "event_observed": int(row["event_observed"]),
            "event_time": int(row["event_time"]),
            "terminal_failure_observed": int(row["terminal_failure_observed"]),
            "terminal_failure_time": int(row["terminal_failure_time"]),
        })
    return parsed


def verify_and_select(run_dir: Path, method: str, seed: int, protocol_version: str) -> tuple[dict, list[dict]]:
    candidates, seen = [], set()
    for row in read_manifest(run_dir):
        update = int(row["update"])
        if update in seen:
            fail(f"duplicate validation update {update}: {run_dir}")
        seen.add(update)
        if row.get("method") != method or int(row.get("training_seed")) != seed:
            fail(f"method/seed provenance mismatch at update {update}: {run_dir}")
        if row.get("protocol_version") != protocol_version:
            fail(f"protocol provenance mismatch at update {update}: {run_dir}")
        snapshot, summary_path, record_path = (
            run_dir / row["snapshot_path"], run_dir / row["summary_path"], run_dir / row["episode_records_path"],
        )
        for path, expected in ((snapshot, row["snapshot_sha256"]), (summary_path, row["summary_sha256"]), (record_path, row["episode_records_sha256"])):
            if not path.exists() or sha256_file(path) != expected:
                fail(f"missing or hash-mismatched immutable artifact at update {update}: {path}")
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        if not set(REQUIRED_METRICS).issubset(summary):
            fail(f"missing P0-A selector fields at update {update}")
        if summary.get("snapshot_sha256") != row["snapshot_sha256"]:
            fail(f"summary snapshot hash mismatch at update {update}")
        records = read_records(record_path)
        recomputed = summarize_validation_event_records(records)
        for name in REQUIRED_METRICS:
            if not math.isclose(float(summary[name]), float(recomputed[name]), rel_tol=0.0, abs_tol=1e-12):
                fail(f"summary {name} differs from immutable episode records at update {update}")
        candidate = {**row, **{name: float(summary[name]) for name in REQUIRED_METRICS}}
        candidate["selection_key"] = rmte_selector_key(candidate, update)
        candidates.append(candidate)
    return min(candidates, key=lambda item: item["selection_key"]), sorted(candidates, key=lambda item: int(item["update"]))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--method", required=True)
    parser.add_argument("--seed", required=True, type=int)
    parser.add_argument("--protocol-version", required=True)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    winner, candidates = verify_and_select(args.run_dir, args.method, args.seed, args.protocol_version)
    result = {
        "method": args.method,
        "seed": args.seed,
        "protocol_version": args.protocol_version,
        "selected_update": int(winner["update"]),
        "checkpoint_path": winner["snapshot_path"],
        "checkpoint_sha256": winner["snapshot_sha256"],
        "rmte80": winner["eval_rmte80"],
        "establishment_probability80": winner["eval_establishment_probability80"],
        "terminal_failure_incidence80": winner["eval_terminal_failure_incidence80"],
        "rmte220": winner["eval_rmte220"],
        "validated_updates": [int(row["update"]) for row in candidates],
    }
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        if args.output.exists():
            fail(f"refusing to overwrite output: {args.output}")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    print(encoded, end="")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2)
