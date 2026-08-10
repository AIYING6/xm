"""Write the one immutable F2 execution manifest after all worker outputs exist.

This script has no simulator or policy import.  It only assembles hashes and
provenance for outputs created by the checkpoint-isolated F2 workers.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from f2_r2_common import F2_PROTOCOL, sha256_file, write_new_json


def fail(message: str) -> None:
    raise RuntimeError(f"F2_R2_FINALIZE_FAILED: {message}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-root", type=Path, required=True)
    parser.add_argument("--expected-f1-source-commit", required=True)
    parser.add_argument("--expected-evaluator-source-commit", required=True)
    parser.add_argument("--f2-workers", type=int, required=True)
    args = parser.parse_args()
    if args.f2_workers not in {1, 2, 4}:
        raise SystemExit("F2 worker count must be one of 1, 2, or 4")
    plan_path = args.out_root / "F2_R2_LAUNCH_PREFLIGHT_MANIFEST.json"
    if not plan_path.exists():
        fail("launch preflight is missing")
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    if (
        plan.get("protocol_version") != F2_PROTOCOL
        or plan.get("f1_source_commit") != args.expected_f1_source_commit
        or plan.get("f2_evaluator_source_commit") != args.expected_evaluator_source_commit
        or plan.get("confirmatory_heldout_accessed") is not False
        or int(plan.get("evaluation_workers", -1)) != args.f2_workers
    ):
        fail("launch preflight provenance or frozen worker count mismatch")

    runs = []
    for checkpoint_plan in plan.get("checkpoint_plans", []):
        method = str(checkpoint_plan["method"])
        training_seed = int(checkpoint_plan["training_seed"])
        run_dir = args.out_root / f"{method}_seed{training_seed}"
        records_path = run_dir / "episode_event_records.csv"
        summary_path = run_dir / "summary.json"
        if not records_path.exists() or not summary_path.exists():
            fail(f"missing worker output for {method}/seed{training_seed}")
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        if (
            summary.get("method") != method
            or int(summary.get("training_seed", -1)) != training_seed
            or int(summary.get("selected_update", -1)) != int(checkpoint_plan["selected_update"])
            or summary.get("checkpoint_sha256") != checkpoint_plan["checkpoint_sha256"]
            or summary.get("f1_source_commit") != args.expected_f1_source_commit
            or summary.get("f2_evaluator_source_commit") != args.expected_evaluator_source_commit
        ):
            fail(f"worker summary provenance mismatch for {method}/seed{training_seed}")
        runs.append({
            "method": method,
            "training_seed": training_seed,
            "selected_update": int(checkpoint_plan["selected_update"]),
            "checkpoint_sha256": checkpoint_plan["checkpoint_sha256"],
            "episode_records_path": str(records_path.relative_to(args.out_root)),
            "episode_records_sha256": sha256_file(records_path),
            "summary_path": str(summary_path.relative_to(args.out_root)),
            "summary_sha256": sha256_file(summary_path),
        })
    if len(runs) != 24:
        fail("F2 execution matrix is not exactly 24 checkpoint evaluations")

    write_new_json(args.out_root / "F2_R2_EXECUTION_MANIFEST.json", {
        "status": "F2_R2_CONFIRMATORY_EVALUATION_COMPLETE__ANALYSIS_PENDING",
        "protocol_version": F2_PROTOCOL,
        "f1_source_commit": args.expected_f1_source_commit,
        "f2_evaluator_source_commit": args.expected_evaluator_source_commit,
        "launch_preflight_sha256": sha256_file(plan_path),
        "confirmatory_heldout_accessed": True,
        "evaluation_workers": args.f2_workers,
        "runs": runs,
    })
    print("F2 execution manifest finalized: 24 checkpoint-isolated outputs")


if __name__ == "__main__":
    main()
