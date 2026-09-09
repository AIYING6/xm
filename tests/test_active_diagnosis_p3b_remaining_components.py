from scripts.audit_active_diagnosis_p3b_remaining_components import collect_result


def test_p3b_remaining_components_gate_passes_without_performance_training() -> None:
    result = collect_result()
    assert result["verdict"] == "P3B_REMAINING_COMPONENTS_PASS"
    assert result["environment_steps"] == 0
    assert result["ppo_performance_updates"] == 0
    assert result["performance_pilot_authorized"] is False
