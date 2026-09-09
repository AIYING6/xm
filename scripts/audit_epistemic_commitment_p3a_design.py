"""Zero-training audit of the P3 submission-task design contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "configs" / "epistemic_commitment_p3_task_contract_20260909.json"


def audit() -> dict:
    value = json.loads(CONTRACT.read_text(encoding="utf-8"))
    task = value["task"]
    boundary = value["information_boundary"]
    methods = value["controlled_methods"]
    method_cells = {
        (bool(row["interval_estimation"]), bool(row["robust_task_value"]))
        for row in methods
    }
    actor = set(boundary["actor_visible"])
    evaluator = set(boundary["evaluator_only"])
    checks = {
        "submission_role_not_pilot": value["scientific_role"] == "submission_task_candidate",
        "multistage_decision_exact": int(task["decision_epochs"]) >= 4
        and len(task["stages"]) >= 6,
        "continuous_closed_loop_backend": task["physical_backend"]
        == "UAVIntercept3DEnv.step_guidance",
        "high_level_and_guidance_jointly_learned": {
            "commit",
            "defer",
            "fallback",
            "turn_guidance",
            "climb_guidance",
        }.issubset(set(task["learned_outputs"]["leader_and_attacker"])),
        "communication_mismatch_family_nontrivial": len(value["frozen_training_cells"]) >= 5
        and len(value["heldout_compositional_cells"]) >= 2,
        "actor_evaluator_truth_disjoint": actor.isdisjoint(evaluator),
        "critic_adds_no_oracle_truth": boundary["critic_visible"]
        == "union_of_legal_actor_observations_only",
        "all_endpoints_trajectory_derived": len(value["trajectory_derived_endpoints"]) >= 8
        and len(value["forbidden_endpoint_construction"]) == 3,
        "factorial_mechanism_ablation_complete": method_cells
        == {(False, False), (False, True), (True, False), (True, True)},
        "oracle_is_upper_bound_only": value["upper_bound_only"] == "delivery_truth_oracle",
        "q0_gate_complete": len(value["q0_required_checks"]) == 12,
        "training_still_forbidden": value["training_authorized"] is False
        and value["automatic_training_start"] is False,
    }
    return {
        "protocol": "EPISTEMIC-COMMITMENT-P3A-DESIGN-AUDIT-V1",
        "verdict": "P3A_DESIGN_CONTRACT_PASS_TO_Q0_IMPLEMENTATION"
        if all(checks.values())
        else "P3A_DESIGN_CONTRACT_FAIL",
        "checks": checks,
        "training_started": False,
        "environment_steps": 0,
        "next_authorized_action": "implement environment and run zero-training Q0 only",
        "evidence_boundary": (
            "This audit establishes a non-toy design contract and identifiable ablation matrix. "
            "It does not establish environment correctness, learnability, novelty, or performance."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = audit()
    payload = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        if args.output.exists():
            raise FileExistsError(f"refusing to overwrite {args.output}")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    if report["verdict"] == "P3A_DESIGN_CONTRACT_FAIL":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
