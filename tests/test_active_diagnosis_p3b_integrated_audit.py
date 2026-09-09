from scripts.audit_active_diagnosis_p3b_integrated_runner import collect_result


def test_integrated_runner_real_environment_gate_passes() -> None:
    result = collect_result()
    assert result["verdict"] == "P3B_INTEGRATED_RUNNER_PASS"
    assert result["ppo_smoke_updates"] == 3
    assert result["performance_training_started"] is False
    assert result["performance_pilot_authorized"] is False
