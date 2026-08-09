"""Verify immutable v1.8 repair artifacts and apply the frozen selector.

This tool never evaluates a policy.  It reads only training-time validation
records and the snapshots that were created at those validation events.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def fail(message: str) -> None:
    raise RuntimeError(f"IMMUTABLE_ARTIFACT_VERIFICATION_FAILED: {message}")


def read_manifest(run_dir: Path) -> list[dict]:
    path = run_dir / "snapshot_manifest.jsonl"
    if not path.exists():
        fail(f"missing snapshot manifest: {path}")
    rows = []
    with path.open(encoding="utf-8") as f:
        for line_number, line in enumerate(f, 1):
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    fail(f"invalid JSON at {path}:{line_number}: {exc}")
    if not rows:
        fail("snapshot manifest is empty")
    return rows


def verify_and_select(
    run_dir: Path, method: str, seed: int, protocol_version: str
) -> tuple[dict, list[dict]]:
    candidates = []
    seen_updates: set[int] = set()
    for row in read_manifest(run_dir):
        update = int(row["update"])
        if update in seen_updates:
            fail(f"duplicate immutable validation update {update}")
        seen_updates.add(update)
        if row.get("method") != method:
            fail(f"method provenance mismatch at update {update}: {row.get('method')!r}")
        if int(row.get("training_seed")) != seed:
            fail(f"seed provenance mismatch at update {update}: {row.get('training_seed')!r}")
        if row.get("protocol_version") != protocol_version:
            fail(f"protocol provenance mismatch at update {update}: {row.get('protocol_version')!r}")
        snapshot = run_dir / row["snapshot_path"]
        summary_path = run_dir / row["summary_path"]
        records_path = run_dir / row["episode_records_path"]
        for path, expected, kind in (
            (snapshot, row["snapshot_sha256"], "snapshot"),
            (summary_path, row["summary_sha256"], "summary"),
            (records_path, row["episode_records_sha256"], "episode records"),
        ):
            if not path.exists():
                fail(f"missing {kind} for update {update}: {path}")
            if sha256_file(path) != expected:
                fail(f"SHA256 mismatch for {kind} at update {update}")
        metadata_path = run_dir / f"actor_critic_update_{update:04d}.metadata.json"
        if not metadata_path.exists():
            fail(f"missing snapshot metadata for update {update}")
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if (
            metadata.get("method") != method
            or int(metadata.get("training_seed")) != seed
            or int(metadata.get("update")) != update
            or metadata.get("protocol_version") != protocol_version
            or metadata.get("sha256") != row["snapshot_sha256"]
        ):
            fail(f"snapshot metadata provenance/hash mismatch at update {update}")
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        required = ("eval_rmst80", "eval_establishment_probability", "eval_censoring_rate", "eval_rmst220")
        if any(key not in summary for key in required):
            fail(f"missing frozen selector metric at update {update}")
        if (
            summary.get("method") != method
            or int(summary.get("training_seed")) != seed
            or int(summary.get("update")) != update
            or summary.get("protocol_version") != protocol_version
            or summary.get("snapshot_sha256") != row["snapshot_sha256"]
        ):
            fail(f"validation summary provenance mismatch at update {update}")
        candidate = {**row, **{key: float(summary[key]) for key in required}}
        # Frozen selection: lower RMST80; higher establishment; lower censoring;
        # lower RMST220; earlier update on an exact tie.
        candidate["selection_key"] = (
            candidate["eval_rmst80"],
            -candidate["eval_establishment_probability"],
            candidate["eval_censoring_rate"],
            candidate["eval_rmst220"],
            update,
        )
        candidates.append(candidate)
    winner = min(candidates, key=lambda candidate: candidate["selection_key"])
    return winner, sorted(candidates, key=lambda candidate: int(candidate["update"]))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--method", required=True)
    parser.add_argument("--seed", required=True, type=int)
    parser.add_argument("--protocol-version", required=True)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    winner, candidates = verify_and_select(
        args.run_dir, args.method, args.seed, args.protocol_version
    )
    result = {
        "method": args.method,
        "seed": args.seed,
        "protocol_version": args.protocol_version,
        "selected_update": int(winner["update"]),
        "checkpoint_path": winner["snapshot_path"],
        "checkpoint_sha256": winner["snapshot_sha256"],
        "rmst80": winner["eval_rmst80"],
        "establishment_probability": winner["eval_establishment_probability"],
        "censoring_rate": winner["eval_censoring_rate"],
        "rmst220": winner["eval_rmst220"],
        "validated_updates": [int(row["update"]) for row in candidates],
    }
    encoded = json.dumps(result, sort_keys=True, indent=2) + "\n"
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
