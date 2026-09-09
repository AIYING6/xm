from scripts.audit_active_diagnosis_p3b_recovery_grounding import run_grounding_audit


def test_p3b_recovery_grounding_passes() -> None:
    result = run_grounding_audit()
    assert result["verdict"] == "P3B_RECOVERY_GROUNDING_PASS"
    assert result["balanced_prior_return_gain"] > 0.0
    assert result["training_started"] is False
    assert result["performance_pilot_authorized"] is False

