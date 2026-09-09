from scripts.audit_epistemic_commitment_p3_q0b_identifiability import audit


def test_q0b_information_gap_contract_passes():
    report = audit()
    assert report["verdict"] == "P3_Q0B_INFORMATION_GAP_PASS_WITH_INDUCTIVE_BIAS_SCOPE"
    assert report["exact_check_registry"] is True
    assert all(report["checks"].values())


def test_q0b_keeps_bayes_and_maximin_claims_separate():
    report = audit()
    assert report["bayes_information_aware_choice"] == "defer_for_ack"
    assert report["robust_pre_ack_choice"] == "fallback_now"
    assert report["representational_impossibility_claim_allowed"] is False
