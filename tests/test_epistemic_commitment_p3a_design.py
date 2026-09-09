from scripts.audit_epistemic_commitment_p3a_design import audit


def test_p3a_submission_task_contract_passes_without_training():
    report = audit()
    assert report["verdict"] == "P3A_DESIGN_CONTRACT_PASS_TO_Q0_IMPLEMENTATION"
    assert all(report["checks"].values())
    assert report["environment_steps"] == 0
    assert report["training_started"] is False
