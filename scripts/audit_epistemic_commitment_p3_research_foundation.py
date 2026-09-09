"""Audit whether P3 has a complete research foundation before scientific training."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FOUNDATION = ROOT / "configs" / "epistemic_commitment_p3_research_foundation_20260910.json"
Q0 = ROOT / "docs" / "strong_q2_clean_sheet_p0_20260909" / "P3_Q0_RESULT.json"
Q0B = ROOT / "docs" / "strong_q2_clean_sheet_p0_20260909" / "P3_Q0B_RESULT.json"


def audit() -> dict:
    foundation = json.loads(FOUNDATION.read_text(encoding="utf-8"))
    q0 = json.loads(Q0.read_text(encoding="utf-8"))
    q0b = json.loads(Q0B.read_text(encoding="utf-8"))
    cells = foundation["controlled_factorial"]["cells"]
    factor_cells = {(bool(row["A"]), bool(row["B"])) for row in cells}
    endpoints = foundation["endpoints"]
    statistics = foundation["statistics"]
    novelty = foundation["novelty_boundary"]
    checks = {
        "q0_environment_correct": q0["verdict"] == "P3_Q0_PASS_TO_TINY_LEARNABILITY_PILOT",
        "q0b_decision_relevant_information_gap": q0b["verdict"]
        == "P3_Q0B_INFORMATION_GAP_PASS_WITH_INDUCTIVE_BIAS_SCOPE",
        "novelty_claim_excludes_known_delay_and_belief_claims": len(novelty["not_claimed"]) >= 4,
        "novelty_search_complete": novelty["exhaustive_search_complete"] is True,
        "targeted_adjacent_search_complete": novelty["targeted_adjacent_search_complete"] is True,
        "full_method_math_frozen": foundation["full_method"]["mathematical_specification_frozen"] is True,
        "all_four_methods_implemented": foundation["full_method"]["implementation_complete"] is True,
        "factorial_cells_complete": factor_cells == {(False, False), (False, True), (True, False), (True, True)},
        "primary_endpoint_single_and_frozen": isinstance(endpoints["primary"], str)
        and bool(endpoints["primary"]),
        "reliability_and_safety_separated": bool(endpoints["reliability_secondary"])
        and bool(endpoints["safety_separate"]),
        "mechanism_metrics_predeclared": len(endpoints["mechanism"]) >= 6,
        "seed_is_independent_unit": statistics["independent_unit"] == "training_seed"
        and statistics["episodes_are_not_independent_replicates"] is True,
        "paired_factorial_and_multiplicity_plan_frozen": statistics["pairing"].startswith("same training seeds")
        and len(statistics["primary_contrasts"]) == 3
        and any("Holm" in item for item in statistics["reporting"]),
        "post_result_seed_extension_forbidden": statistics["seed_extension_after_results_forbidden"] is True,
        "budget_not_inherited_from_10m": "do not inherit 10M" in foundation["staging"]["formal_budget_rule"],
        "interpretation_outcomes_predeclared": len(foundation["interpretation_matrix"]) >= 6,
        "scientific_training_locked": foundation["training_authorized"] is False,
    }
    blockers = [name for name, passed in checks.items() if not passed]
    return {
        "protocol": "EPISTEMIC-COMMITMENT-P3-RESEARCH-FOUNDATION-AUDIT-V1",
        "verdict": (
            "P3_FOUNDATION_READY_FOR_STAGED_TRAINING"
            if not blockers
            else "P3_FOUNDATION_BLOCKS_TRAINING_PENDING_NOVELTY_AND_METHOD_FREEZE"
        ),
        "checks": checks,
        "blocking_items": blockers,
        "training_started": False,
        "next_authorized_action": (
            "complete bibliographic novelty audit and implement four controlled cells; do not run Q1 yet"
            if blockers
            else "run Q1 bounded baseline learnability pilot"
        ),
    }


if __name__ == "__main__":
    print(json.dumps(audit(), ensure_ascii=False, indent=2))
