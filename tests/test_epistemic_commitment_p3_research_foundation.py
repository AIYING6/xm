from scripts.audit_epistemic_commitment_p3_research_foundation import audit


def test_foundation_blocks_training_until_novelty_and_method_are_frozen():
    report = audit()
    assert report["verdict"] == "P3_FOUNDATION_BLOCKS_TRAINING_PENDING_NOVELTY_AND_METHOD_FREEZE"
    assert report["checks"]["q0_environment_correct"] is True
    assert report["checks"]["q0b_decision_relevant_information_gap"] is True
    assert report["checks"]["novelty_search_complete"] is False
    assert report["checks"]["targeted_adjacent_search_complete"] is True
    assert report["checks"]["full_method_math_frozen"] is True
    assert report["checks"]["all_four_methods_implemented"] is False
    assert report["checks"]["scientific_training_locked"] is True


def test_foundation_predeclares_factorial_metrics_and_statistics():
    report = audit()
    for key in (
        "factorial_cells_complete",
        "primary_endpoint_single_and_frozen",
        "reliability_and_safety_separated",
        "mechanism_metrics_predeclared",
        "seed_is_independent_unit",
        "paired_factorial_and_multiplicity_plan_frozen",
        "post_result_seed_extension_forbidden",
        "budget_not_inherited_from_10m",
        "interpretation_outcomes_predeclared",
    ):
        assert report["checks"][key] is True
