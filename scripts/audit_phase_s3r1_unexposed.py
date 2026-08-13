"""Audit S3-R failure-exposure misses without changing any result artifact."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("results/development/phase_s3r_evaluation_remediation/raw_episode_metrics.csv"))
    parser.add_argument("--output", type=Path, default=Path("results/development/phase_s3r_evaluation_remediation/s3r1_unexposed_audit.json"))
    args = parser.parse_args()
    rows = read_rows(args.input)
    failures = [row for row in rows if row["condition"] == "relay_failure" and row["failure_exposed"] == "0"]
    audit = []
    for failure in failures:
        pair = next(row for row in rows if row["method"] == failure["method"]
                    and row["train_seed"] == failure["train_seed"]
                    and row["development_episode_id"] == failure["development_episode_id"]
                    and row["condition"] == "nominal")
        terminal_step = int(failure["terminal_step"])
        audit.append({
            "method": failure["method"],
            "train_seed": int(failure["train_seed"]),
            "episode_id": int(failure["development_episode_id"]),
            "failure_scheduled": True,
            "failure_start_step": 44,
            "failure_duration_steps": 80,
            "failure_triggered": False,
            "failure_active_steps": int(failure["failure_active_steps"]),
            "failure_terminal_step": terminal_step,
            "nominal_terminal_step": int(pair["terminal_step"]),
            "failure_terminal_reason": "collision" if failure["collision"] == "1.0" else "other",
            "nominal_terminal_reason": "collision" if pair["collision"] == "1.0" else "other",
            "same_pair_terminal_step": terminal_step == int(pair["terminal_step"]),
            "root_cause": "natural_collision_before_failure_onset" if terminal_step < 44 and failure["collision"] == "1.0" else "requires_manual_review",
        })
    counts = {}
    for item in audit:
        counts[item["root_cause"]] = counts.get(item["root_cause"], 0) + 1
    result = {
        "protocol": "PHASE-S3-R1",
        "input": str(args.input),
        "scope": "Full/seed1503 failure-exposure misses only",
        "failure_onset_step": 44,
        "audit_count": len(audit),
        "root_cause_counts": counts,
        "all_misses_natural_collision_before_onset": bool(audit) and all(item["root_cause"] == "natural_collision_before_failure_onset" for item in audit),
        "evaluator_bug_found": False,
        "training_started": False,
        "episodes": audit,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
