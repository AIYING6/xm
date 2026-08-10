"""Integrity gate for a completed v1.9 F2-R2 confirmatory evaluation."""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.simple_ri_gmappo import summarize_validation_event_records  # noqa: E402
from f2_r2_common import F2_EPISODE_IDS, F2_PROTOCOL, METHOD_SPECS, sha256_file, write_new_json


REQUIRED_RECORD_FIELDS = {
    "episode_seed", "failure_onset_step", "event_observed", "event_time", "termination_reason",
    "terminal_failure_observed", "terminal_failure_time", "terminal_step",
    "physical_event_observed", "physical_event_time",
}
REQUIRED_SUMMARY_FIELDS = {
    "rmte80", "establishment_probability80", "terminal_failure_incidence80",
    "active_not_established_probability80", "rmte220", "establishment_probability220",
    "terminal_failure_incidence220", "active_not_established_probability220", "rmpe80",
    "physical_engagement_probability80", "rmpe220", "physical_engagement_probability220",
}


def fail(message: str) -> None:
    raise RuntimeError(f"F2_R2_ARTIFACT_GATE_FAILED: {message}")


def read_json(path: Path) -> dict:
    if not path.exists():
        fail(f"missing file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def validate(root: Path, expected_f1_source_commit: str, expected_evaluator_source_commit: str) -> dict:
    preflight_path = root / "F2_R2_LAUNCH_PREFLIGHT_MANIFEST.json"
    execution_path = root / "F2_R2_EXECUTION_MANIFEST.json"
    preflight = read_json(preflight_path)
    execution = read_json(execution_path)
    if (
        preflight.get("protocol_version") != F2_PROTOCOL
        or preflight.get("f1_source_commit") != expected_f1_source_commit
        or preflight.get("f2_evaluator_source_commit") != expected_evaluator_source_commit
        or preflight.get("confirmatory_heldout_accessed") is not False
    ):
        fail("launch preflight provenance mismatch")
    if (
        execution.get("status") != "F2_R2_CONFIRMATORY_EVALUATION_COMPLETE__ANALYSIS_PENDING"
        or execution.get("protocol_version") != F2_PROTOCOL
        or execution.get("f1_source_commit") != expected_f1_source_commit
        or execution.get("f2_evaluator_source_commit") != expected_evaluator_source_commit
        or execution.get("launch_preflight_sha256") != sha256_file(preflight_path)
        or execution.get("confirmatory_heldout_accessed") is not True
        or int(execution.get("evaluation_workers", -1)) not in {1, 2, 4}
        or int(execution.get("evaluation_workers", -1)) != int(preflight.get("evaluation_workers", -2))
    ):
        fail("execution manifest provenance mismatch")

    planned = {(row["method"], int(row["training_seed"])): row for row in preflight.get("checkpoint_plans", [])}
    executed = {(row["method"], int(row["training_seed"])): row for row in execution.get("runs", [])}
    expected = {(method, seed) for method, _, _ in METHOD_SPECS for seed in range(8)}
    if set(planned) != expected or set(executed) != expected:
        fail("F2 matrix is not exactly 3 methods x 8 seeds")

    verified_runs = []
    for method, _, _ in METHOD_SPECS:
        for seed in range(8):
            plan = planned[(method, seed)]
            run = executed[(method, seed)]
            records_path = root / run["episode_records_path"]
            summary_path = root / run["summary_path"]
            if sha256_file(records_path) != run["episode_records_sha256"]:
                fail(f"{method}/seed{seed}: event-record SHA256 mismatch")
            if sha256_file(summary_path) != run["summary_sha256"]:
                fail(f"{method}/seed{seed}: summary SHA256 mismatch")
            summary = read_json(summary_path)
            if (
                summary.get("protocol_version") != F2_PROTOCOL
                or summary.get("f1_source_commit") != expected_f1_source_commit
                or summary.get("f2_evaluator_source_commit") != expected_evaluator_source_commit
                or summary.get("method") != method
                or int(summary.get("training_seed", -1)) != seed
                or int(summary.get("selected_update", -1)) != int(plan["selected_update"])
                or summary.get("checkpoint_sha256") != plan["checkpoint_sha256"]
                or int(summary.get("episodes", -1)) != len(F2_EPISODE_IDS)
                or summary.get("episode_records_sha256") != run["episode_records_sha256"]
            ):
                fail(f"{method}/seed{seed}: summary provenance mismatch")
            if not REQUIRED_SUMMARY_FIELDS.issubset(summary):
                fail(f"{method}/seed{seed}: incomplete endpoint summary")
            if not all(math.isfinite(float(summary[field])) for field in REQUIRED_SUMMARY_FIELDS):
                fail(f"{method}/seed{seed}: non-finite endpoint summary")
            with records_path.open(encoding="utf-8", newline="") as handle:
                reader = csv.DictReader(handle)
                if reader.fieldnames is None or not REQUIRED_RECORD_FIELDS.issubset(reader.fieldnames):
                    fail(f"{method}/seed{seed}: event-record schema mismatch")
                records = list(reader)
            if [int(row["episode_seed"]) for row in records] != list(F2_EPISODE_IDS):
                fail(f"{method}/seed{seed}: episode bank is missing, duplicated, or reordered")
            recomputed = {
                field[5:] if field.startswith("eval_") else field: float(value)
                for field, value in summarize_validation_event_records(records).items()
            }
            for field in REQUIRED_SUMMARY_FIELDS:
                if not math.isclose(float(summary[field]), recomputed[field], rel_tol=0.0, abs_tol=1e-12):
                    fail(f"{method}/seed{seed}: {field} does not match immutable episode records")
            verified_runs.append({
                "method": method,
                "training_seed": seed,
                "checkpoint_sha256": plan["checkpoint_sha256"],
                "episode_records_sha256": run["episode_records_sha256"],
                "summary_sha256": run["summary_sha256"],
            })
    return {
        "status": "F2_R2_CONFIRMATORY_ARTIFACT_GATE_PASS",
        "protocol_version": F2_PROTOCOL,
        "f1_source_commit": expected_f1_source_commit,
        "f2_evaluator_source_commit": expected_evaluator_source_commit,
        "confirmatory_heldout_accessed": True,
        "runs": verified_runs,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--expected-f1-source-commit", required=True)
    parser.add_argument("--expected-evaluator-source-commit", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = validate(args.root, args.expected_f1_source_commit, args.expected_evaluator_source_commit)
    write_new_json(args.output, result)
    print("F2_R2_CONFIRMATORY_ARTIFACT_GATE_PASS: 24 checkpoints x 300 paired episodes")


if __name__ == "__main__":
    main()
