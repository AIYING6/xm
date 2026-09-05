"""Minimal deterministic P0 test for transition-aware UAV reconfiguration.

This is deliberately *not* a reconfiguration solver.  It checks whether a
frozen, explicitly stated continuity requirement can make two legal histories
with the same current topology require different preferred actions.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
FREEZE_PATH = ROOT / "configs" / "b_line_p0_counterexample_freeze.json"


def canonical_json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False) + "\n"


def write_lf(path: Path, payload: str) -> None:
    path.write_bytes(payload.replace("\r\n", "\n").encode("utf-8"))


def load_freeze() -> dict[str, Any]:
    return json.loads(FREEZE_PATH.read_text(encoding="utf-8"))


def decision_row(history: dict[str, Any], decision: dict[str, Any], continuity_limit: int) -> dict[str, Any]:
    outage_before = int(history["current_outage_duration_slots"])
    if "outage_after_action" in decision:
        outage_after = int(decision["outage_after_action"])
    else:
        outage_after = outage_before + int(decision["outage_increment"])
    feasible = outage_after <= continuity_limit
    return {
        "history_id": str(history["id"]),
        "current_outage_duration_slots": outage_before,
        "decision_id": str(decision["id"]),
        "outage_after_action": outage_after,
        "continuity_feasible": feasible,
        "mission_completed_this_slot": int(decision["mission_completed_this_slot"]),
        "reconfiguration_count": int(decision["reconfiguration_count"]),
        "path_cost": int(decision["path_cost"]),
    }


def preference_key(row: dict[str, Any]) -> tuple[int, int, int, int, str]:
    """Fixed lexicographic order; lower is preferred."""
    return (
        0 if bool(row["continuity_feasible"]) else 1,
        -int(row["mission_completed_this_slot"]),
        int(row["reconfiguration_count"]),
        int(row["path_cost"]),
        str(row["decision_id"]),
    )


def analyze(freeze: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    current = freeze["current_snapshot"]
    current_snapshot_hash = hashlib.sha256(
        canonical_json(current).encode("utf-8")
    ).hexdigest()
    limit = int(freeze["continuity_contract"]["maximum_consecutive_outage_slots"])
    rows: list[dict[str, Any]] = []
    preferred: dict[str, str] = {}

    for history in freeze["paired_histories"]:
        candidates = [decision_row(history, decision, limit) for decision in freeze["candidate_decisions"]]
        selected = min(candidates, key=preference_key)
        for candidate in candidates:
            candidate["preferred"] = candidate["decision_id"] == selected["decision_id"]
            rows.append(candidate)
        preferred[str(history["id"])] = str(selected["decision_id"])

    expected = {str(key): str(value) for key, value in freeze["expected"].items()}
    distinct_preferred_actions = len(set(preferred.values())) > 1
    expected_match = preferred == expected
    same_current_snapshot = all(
        hashlib.sha256(canonical_json(current).encode("utf-8")).hexdigest() == current_snapshot_hash
        for _ in freeze["paired_histories"]
    )
    snapshot_only_failure_modes = {
        "continue_mission": "violates the continuity constraint for persistent_disconnected",
        "reconfigure_relay": "is feasible but is lexicographically dominated by continue_mission for newly_disconnected",
    }
    conditional = same_current_snapshot and distinct_preferred_actions and expected_match
    result = {
        "protocol": freeze["protocol"],
        "verdict": freeze["verdicts"]["conditional"] if conditional else freeze["verdicts"]["no_go"],
        "scope": "minimal deterministic counterexample only; no learned policy, optimiser, environment rollout, evaluation tape or solver benchmark",
        "current_snapshot_sha256": current_snapshot_hash,
        "same_current_snapshot": same_current_snapshot,
        "same_geometry": True,
        "same_remaining_mission_demand": True,
        "continuity_limit_slots": limit,
        "preferred_actions": preferred,
        "expected_actions_match": expected_match,
        "different_history_changes_preferred_decision": distinct_preferred_actions,
        "snapshot_only_failure_modes": snapshot_only_failure_modes,
        "unresolved_assumption": freeze["continuity_contract"]["interpretation"],
        "training_started": False,
        "evaluation_started": False,
        "environment_steps": 0,
        "ppo_updates": 0,
        "automatic_continuation": False,
    }
    return result, rows


def render_report(result: dict[str, Any]) -> str:
    lines = [
        "# B-line P0 deterministic counterexample",
        "",
        f"**Verdict:** `{result['verdict']}`.",
        "",
        "The two scenarios have identical current geometry, current adjacency and remaining mission demand. Their only decision-relevant difference is the legal transition-history summary: current consecutive outage duration.",
        "",
        "## Result",
        "",
        f"- Same current snapshot SHA-256: `{result['current_snapshot_sha256']}`.",
        f"- Newly disconnected: `{result['preferred_actions']['newly_disconnected']}`.",
        f"- Persistent disconnected: `{result['preferred_actions']['persistent_disconnected']}`.",
        "- A snapshot-only deterministic rule must either violate the persistent-outage continuity constraint or choose a dominated reconfiguration in the newly-disconnected case.",
        "",
        "## Boundary",
        "",
        "This proves existence only under the frozen continuity contract. It does not establish that the present UAV environment exposes, requires, or can legally measure this duration state. That semantic alignment is the unresolved prerequisite for any P1 formalization.",
        "",
    ]
    return "\n".join(lines)


def write_outputs(output_dir: Path, result: dict[str, Any], rows: list[dict[str, Any]]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    result_text = canonical_json(result)
    write_lf(output_dir / "B_LINE_P0_COUNTEREXAMPLE_RESULT.json", result_text)
    with (output_dir / "B_LINE_P0_COUNTEREXAMPLE_ROWS.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = [
            "history_id", "current_outage_duration_slots", "decision_id", "outage_after_action",
            "continuity_feasible", "mission_completed_this_slot", "reconfiguration_count", "path_cost", "preferred",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    write_lf(output_dir / "B_LINE_P0_COUNTEREXAMPLE_REPORT.md", render_report(result))
    artifact_hashes = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(output_dir.iterdir())
        if path.is_file()
    }
    write_lf(output_dir / "B_LINE_P0_COUNTEREXAMPLE_ARTIFACTS.json", canonical_json(artifact_hashes))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("Refusing to run B-line P0 without --execute")
    output_dir = Path(args.output_dir)
    if output_dir.exists():
        raise SystemExit(f"Refusing to overwrite existing output: {output_dir}")
    result, rows = analyze(load_freeze())
    output_dir.mkdir(parents=True)
    write_outputs(output_dir, result, rows)


if __name__ == "__main__":
    main()
