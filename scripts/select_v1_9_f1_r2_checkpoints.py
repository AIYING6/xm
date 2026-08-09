"""Apply the frozen F1-R2 RMTE selector to immutable training-time records only."""
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

from algorithms.ri_gmappo.simple_ri_gmappo import rmte_selector_key  # noqa: E402

PROTOCOL = "V1_9_F1_R2_FORMAL_TRAINING"
UPDATES = [1, *range(10, 301, 10)]
FORMAL_SEEDS = tuple(range(8))
METHODS = (
    ("pcrf_r2", "pcrf_r2", 128),
    ("single_r2", "single_r2", 147),
    ("matched_nongraph_r2", "matched_nongraph_r2", 152),
)
VALIDATION_BASE_SEED = 410_000
VALIDATION_EPISODES = 16
REQUIRED_SUMMARY = {
    "eval_rmte80", "eval_establishment_probability80", "eval_terminal_failure_incidence80", "eval_rmte220",
    "eval_rmpe80", "eval_physical_engagement_probability80", "eval_rmpe220", "eval_physical_engagement_probability220",
}
REQUIRED_RECORDS = {
    "episode_seed", "failure_onset_step", "event_observed", "event_time", "termination_reason",
    "terminal_failure_observed", "terminal_failure_time", "physical_event_observed",
    "first_stable_physical_engagement_step", "physical_event_time",
}


def fail(message: str) -> None:
    raise RuntimeError(f"F1_R2_IMMUTABLE_SELECTION_FAILED: {message}")


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        fail(f"missing snapshot manifest: {path}")
    rows = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            fail(f"invalid JSON at {path}:{line_number}: {exc}")
    return rows


def verify_and_select(run_dir: Path, method: str, seed: int, expected_commit: str) -> tuple[dict, list[dict]]:
    rows = _read_jsonl(run_dir / "snapshot_manifest.jsonl")
    by_update: dict[int, dict] = {}
    for row in rows:
        update = int(row.get("update", -1))
        if update in by_update:
            fail(f"{run_dir}: duplicate update {update}")
        by_update[update] = row
    if sorted(by_update) != UPDATES:
        fail(f"{run_dir}: frozen validation updates differ from {UPDATES}")

    candidates = []
    for update in UPDATES:
        row = by_update[update]
        if (
            row.get("protocol_version") != PROTOCOL
            or row.get("git_commit") != expected_commit
            or row.get("method") != method
            or int(row.get("training_seed", -1)) != seed
            or int(row.get("update", -1)) != update
        ):
            fail(f"{run_dir}: snapshot manifest provenance mismatch at update {update}")
        paths = {
            "snapshot": run_dir / row["snapshot_path"],
            "summary": run_dir / row["summary_path"],
            "records": run_dir / row["episode_records_path"],
        }
        expected_hashes = {
            "snapshot": row["snapshot_sha256"],
            "summary": row["summary_sha256"],
            "records": row["episode_records_sha256"],
        }
        for kind, path in paths.items():
            if not path.exists() or digest(path) != expected_hashes[kind]:
                fail(f"{run_dir}: immutable {kind} SHA256 mismatch at update {update}")
        metadata_path = run_dir / f"actor_critic_update_{update:04d}.metadata.json"
        if not metadata_path.exists():
            fail(f"{run_dir}: missing snapshot metadata at update {update}")
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if (
            metadata.get("protocol_version") != PROTOCOL
            or metadata.get("git_commit") != expected_commit
            or metadata.get("method") != method
            or int(metadata.get("training_seed", -1)) != seed
            or int(metadata.get("update", -1)) != update
            or metadata.get("sha256") != row["snapshot_sha256"]
        ):
            fail(f"{run_dir}: snapshot metadata mismatch at update {update}")
        summary = json.loads(paths["summary"].read_text(encoding="utf-8"))
        if not REQUIRED_SUMMARY.issubset(summary):
            fail(f"{run_dir}: frozen endpoint fields absent at update {update}")
        if (
            summary.get("protocol_version") != PROTOCOL
            or summary.get("method") != method
            or int(summary.get("training_seed", -1)) != seed
            or int(summary.get("update", -1)) != update
            or int(summary.get("validation_base_seed", -1)) != VALIDATION_BASE_SEED
            or int(summary.get("episodes", -1)) != VALIDATION_EPISODES
            or summary.get("snapshot_sha256") != row["snapshot_sha256"]
        ):
            fail(f"{run_dir}: validation summary provenance mismatch at update {update}")
        with paths["records"].open(encoding="utf-8", newline="") as f:
            header = set(next(csv.reader(f), []))
        if not REQUIRED_RECORDS.issubset(header):
            fail(f"{run_dir}: frozen event-record fields absent at update {update}")
        metrics = {key: float(summary[key]) for key in REQUIRED_SUMMARY}
        if not all(math.isfinite(value) for value in metrics.values()):
            fail(f"{run_dir}: non-finite validation endpoint at update {update}")
        candidates.append({
            "update": update,
            "snapshot_path": row["snapshot_path"],
            "snapshot_sha256": row["snapshot_sha256"],
            "summary_path": row["summary_path"],
            "summary_sha256": row["summary_sha256"],
            "episode_records_path": row["episode_records_path"],
            "episode_records_sha256": row["episode_records_sha256"],
            **metrics,
        })
    winner = min(candidates, key=lambda row: rmte_selector_key(row, int(row["update"])))
    return winner, candidates


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--expected-source-commit", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        fail(f"refusing to overwrite frozen output: {args.output}")
    selections = []
    for method, _, _ in METHODS:
        for seed in FORMAL_SEEDS:
            winner, candidates = verify_and_select(args.root / f"{method}_seed{seed}", method, seed, args.expected_source_commit)
            selections.append({
                "method": method,
                "seed": seed,
                "selected_update": int(winner["update"]),
                "selected_checkpoint_path": winner["snapshot_path"],
                "selected_checkpoint_sha256": winner["snapshot_sha256"],
                "selected_validation_summary_sha256": winner["summary_sha256"],
                "selected_event_records_sha256": winner["episode_records_sha256"],
                "rmte80": winner["eval_rmte80"],
                "establishment_probability80": winner["eval_establishment_probability80"],
                "terminal_failure_incidence80": winner["eval_terminal_failure_incidence80"],
                "rmte220": winner["eval_rmte220"],
                "validated_updates": [int(row["update"]) for row in candidates],
            })
    result = {
        "status": "F1_R2_FORMAL_TRAINING_COMPLETE__CHECKPOINTS_FROZEN__READY_FOR_F2_AUTHORIZATION",
        "protocol_version": PROTOCOL,
        "confirmatory_heldout_accessed": False,
        "selector": "lower RMTE80; higher establishment probability80; lower terminal-failure incidence80; lower RMTE220; earlier update",
        "source_commit": args.expected_source_commit,
        "validation_base_seed": VALIDATION_BASE_SEED,
        "validation_episodes": VALIDATION_EPISODES,
        "selections": selections,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
        raise SystemExit(2)
