from scripts.audit_epistemic_commitment_counterexample import audit, best_decentralized_action, values


def test_each_action_is_optimal_on_a_nonempty_prior_interval() -> None:
    assert best_decentralized_action(0.10) == "fallback"
    assert best_decentralized_action(0.50) == "defer"
    assert best_decentralized_action(0.90) == "commit"


def test_information_gap_is_strict_away_from_extreme_priors() -> None:
    for probability in (0.25, 0.50, 0.75):
        action_values = values(probability)
        decentralized = max(action_values[name] for name in ("commit", "defer", "fallback"))
        assert action_values["centralized_oracle"] > decentralized


def test_zero_training_audit_passes() -> None:
    result = audit()
    assert result["verdict"] == "P1B_ANALYTIC_COUNTEREXAMPLE_PASS"
    assert result["training_started"] is False
    assert result["environment_steps"] == 0
    assert all(result["checks"].values())

