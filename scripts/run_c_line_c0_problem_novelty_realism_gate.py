"""Zero-training C-line C0 falsification gate.

This script deliberately does not import or instantiate an environment, a
learner, a planner, or an evaluator.  It hashes the fixed audit inputs and
enumerates a two-action truth table that tests only the claimed non-myopic
property.  It is not a solver implementation.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def git_revision() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, encoding="utf-8"
    ).strip()


def toy_rows() -> list[dict[str, Any]]:
    """Enumerate the frozen two-slot counterexample without optimization.

    Capacity is one relay-slot per time.  Service A can be delivered at slot 0
    for immediate priority 6.  Service B has zero immediate delivery at slot
    0, but a disruption-free route migration must reserve that slot and enables
    its deadline-limited priority-10 delivery at slot 1.  Hence a one-slot
    payoff rule chooses A, while the two-slot total-priority objective chooses
    the B migration.  Values are fixed illustrative priorities, not tuned
    rewards, and the report labels the exact migration latency an abstraction.
    """
    return [
        {
            "policy": "myopic_serve_A",
            "slot0_action": "serve_A",
            "slot0_immediate_priority": 6,
            "B_route_staged_after_slot0": False,
            "slot1_action": "stage_B_too_late",
            "B_deadline_met": False,
            "total_completed_priority": 6,
            "finite_horizon_feasible_for_B": False,
            "is_one_slot_optimum": True,
            "is_two_slot_optimum": False,
        },
        {
            "policy": "nonmyopic_stage_B_then_serve_B",
            "slot0_action": "reserve_capacity_for_disruption_free_B_migration",
            "slot0_immediate_priority": 0,
            "B_route_staged_after_slot0": True,
            "slot1_action": "serve_B_before_deadline",
            "B_deadline_met": True,
            "total_completed_priority": 10,
            "finite_horizon_feasible_for_B": True,
            "is_one_slot_optimum": False,
            "is_two_slot_optimum": True,
        },
    ]


def run(output_root: Path) -> dict[str, Any]:
    config = ROOT / "configs" / "c_line_c0_problem_novelty_realism_gate_freeze.json"
    literature_map = ROOT / "docs" / "c_line_c0_20260905" / "C_LINE_C0_NOVELTY_MAP.md"
    source_files = [
        ROOT / "envs" / "redundant_topology_uav_env.py",
        ROOT / "envs" / "uav_intercept_3d_env.py",
        ROOT / "docs" / "b_line_p15_20260905" / "B_LINE_P15_FINAL_STATUS.md",
    ]
    if not config.is_file() or not literature_map.is_file() or any(not p.is_file() for p in source_files):
        raise FileNotFoundError("C0 fixed inputs are missing")

    output_root.mkdir(parents=True, exist_ok=False)
    rows = toy_rows()
    csv_path = output_root / "C_LINE_C0_NONMYOPIC_TRUTH_TABLE.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    myopic = next(row for row in rows if row["is_one_slot_optimum"])
    horizon = next(row for row in rows if row["is_two_slot_optimum"])
    strict_nonmyopic = (
        myopic["policy"] != horizon["policy"]
        and myopic["slot0_immediate_priority"] > horizon["slot0_immediate_priority"]
        and myopic["total_completed_priority"] < horizon["total_completed_priority"]
        and not myopic["B_deadline_met"]
        and horizon["B_deadline_met"]
    )

    # The literature/solver findings are deliberately conservative.  This
    # script must not promote C0 to GO merely because a toy has a conflict.
    result = {
        "protocol": "C-LINE-C0-PROBLEM-NOVELTY-REALISM-GATE-V1",
        "verdict": "C0_CONDITIONAL",
        "checks": {
            "real_semantics_supported_by_literature": True,
            "two_competing_decision_variables_specified": True,
            "strict_nonmyopic_counterexample": strict_nonmyopic,
            "tg_vm_non_overlap": True,
            "nearest_neighbor_not_full_cover_proven": False,
            "structured_solver_innovation_space_proven": False,
        },
        "blocking_reasons": [
            "A direct UAV-relay reconfiguration paper already contains route refreshment, limited link capacity, connection migration, and disruption-free migration conditions.",
            "A UAV-failure online reconfiguration paper already optimizes trajectories/connectivity under failure.",
            "The current candidate is therefore not novel merely by combining failures, relay reconfiguration, and freshness.",
            "No non-generic exploitable structure or theorem target is established beyond a time-expanded multi-commodity assignment/flow formulation.",
            "The repository's existing environments do not expose a transition-effective relay/routing/capacity control interface, so C cannot claim an unmodified native realization.",
        ],
        "permitted_next_step_only": "C0R: a zero-training exact-overlap and structure audit that either identifies a formally distinct restricted problem with a theorem target, or closes C-line.",
        "prohibited_next_steps": ["C1", "solver", "environment changes", "training", "benchmarking", "objective tuning"],
        "counterexample": {
            "horizon_slots": 2,
            "relay_capacity_per_slot": 1,
            "myopic_policy": myopic["policy"],
            "finite_horizon_policy": horizon["policy"],
            "strict_difference": strict_nonmyopic,
            "truth_table_sha256": sha256(csv_path),
        },
        "literature_audit": {
            "nearest_neighbor_count": 12,
            "novelty_map_sha256": sha256(literature_map),
            "screening_level": "publisher or DOI record plus abstract/full publisher description; not a claim of exhaustive systematic review",
        },
        "source_revision_before_c0_commit": git_revision(),
        "input_sha256": {str(p.relative_to(ROOT)).replace("\\", "/"): sha256(p) for p in [config, *source_files]},
        "training_started": False,
        "evaluation_started": False,
        "automatic_continuation": False,
    }
    write_json(output_root / "C_LINE_C0_RESULT.json", result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("Refusing a silent run: pass --execute")
    result = run(args.output_root)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
