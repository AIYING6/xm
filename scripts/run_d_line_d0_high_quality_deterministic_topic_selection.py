"""Zero-training D0 toy enumerator and machine-readable topic decision.

This script is deliberately not a solver, simulator, or benchmark.  It enumerates
three fixed two-slot feasibility toys used only to test whether each proposed topic
has a genuine temporal decision conflict before any environment is redesigned.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


TOYS = [
    {
        "candidate": "A",
        "decisions": "migrate_service_1_now|reserve_relay_for_service_2",
        "myopic_action": "migrate_service_1_now",
        "myopic_value": 6,
        "optimal_action": "reserve_relay_for_service_2",
        "optimal_value": 10,
        "hard_coupling": "one relay slot at t=0; service 2 has an unrecoverable t=1 continuity deadline",
    },
    {
        "candidate": "B",
        "decisions": "execute_local_task_now|synchronize_feasibility_version",
        "myopic_action": "execute_local_task_now",
        "myopic_value": 4,
        "optimal_action": "synchronize_feasibility_version",
        "optimal_value": 9,
        "hard_coupling": "one broadcast at t=0; the high-value t=1 joint action is infeasible until both agents hold the same version",
    },
    {
        "candidate": "C",
        "decisions": "fail_back_to_recovered_route_now|hold_temporary_reservation",
        "myopic_action": "fail_back_to_recovered_route_now",
        "myopic_value": 5,
        "optimal_action": "hold_temporary_reservation",
        "optimal_value": 8,
        "hard_coupling": "one capacity reservation; immediate failback consumes the only recovery buffer required by a t=1 service deadline",
    },
]

SCORES = {
    "A": {"novelty": 3, "solver_depth": 3, "theory": 4, "deterministic_reproducibility": 10, "environment_cost": 6, "baselines": 10, "strong_q2_potential": 2},
    "B": {"novelty": 9, "solver_depth": 6, "theory": 8, "deterministic_reproducibility": 10, "environment_cost": 5, "baselines": 9, "strong_q2_potential": 5},
    "C": {"novelty": 4, "solver_depth": 4, "theory": 5, "deterministic_reproducibility": 10, "environment_cost": 5, "baselines": 10, "strong_q2_potential": 3},
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", default="docs/d_line_d0_20260905")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("Refusing dry run: pass --execute. This creates only D0 audit artifacts.")
    root = Path(args.output_root)
    root.mkdir(parents=True, exist_ok=True)
    with (root / "D0_COUNTEREXAMPLE_TRUTH_TABLE.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(TOYS[0]))
        writer.writeheader()
        writer.writerows(TOYS)
    results = []
    for toy in TOYS:
        score = SCORES[toy["candidate"]]
        results.append({
            "candidate": toy["candidate"],
            "strict_counterexample": toy["optimal_value"] > toy["myopic_value"],
            "score": sum(score.values()),
            "hard_gate_pass": False,
        })
    payload = {
        "protocol": "D0-HIGH-QUALITY-DETERMINISTIC-TOPIC-SELECTION-V1",
        "verdict": "D0_NO_CLEAR_WINNER",
        "winner": None,
        "reason": "All three candidates have a temporal toy conflict, but none survives both nearest-neighbor novelty and non-generic-solver hard gates.",
        "scores": SCORES,
        "toy_results": results,
        "training_started": False,
        "environment_modified": False,
        "solver_implemented": False,
        "automatic_continuation": False,
    }
    (root / "D0_RESULT.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
