from __future__ import annotations

import torch

from algorithms.epistemic_commitment import (
    CapacityMatchedRecurrentActor,
    CommitmentActorConfig,
    InformationSetCommitmentActor,
    smooth_robust_mode_values,
)
from algorithms.epistemic_commitment_objective import (
    commitment_actor_loss,
    target_probability_interval,
)
from scripts.audit_epistemic_commitment_p1f_objective import run_p1f_audit


def test_calibration_target_uses_public_prior_and_frozen_radius() -> None:
    target = target_probability_interval(torch.tensor([0.15, 0.45, 0.85]), radius=0.05)
    expected = torch.tensor([[0.10, 0.20], [0.40, 0.50], [0.80, 0.90]])
    assert torch.allclose(target, expected)


def test_smooth_robust_values_are_finite_and_differentiable() -> None:
    endpoints = torch.tensor([[[-8.0, 10.0], [1.0, 5.0], [2.0, 2.0]]], requires_grad=True)
    interval = torch.tensor([[0.4, 0.5]], requires_grad=True)
    values = smooth_robust_mode_values(endpoints, interval, 0.10)
    assert torch.isfinite(values).all()
    values.sum().backward()
    assert endpoints.grad is not None and torch.isfinite(endpoints.grad).all()
    assert interval.grad is not None and torch.isfinite(interval.grad).all()


def test_identical_loss_contract_accepts_candidate_and_baseline() -> None:
    config = CommitmentActorConfig(input_dim=39, hidden_dim=16)
    history = torch.randn(6, 2, 39)
    actions = torch.tensor([0, 1, 2, 0, 1, 2])
    old_log_prob = torch.zeros(6)
    advantages = torch.ones(6)
    priors = torch.tensor([0.15, 0.45, 0.85, 0.15, 0.45, 0.85])
    for model in (InformationSetCommitmentActor(config), CapacityMatchedRecurrentActor(config)):
        output = model(history)
        loss, telemetry = commitment_actor_loss(output, actions, old_log_prob, advantages, priors)
        assert torch.isfinite(loss)
        assert set(telemetry) == {
            "new_log_prob",
            "ratio",
            "entropy",
            "policy_loss",
            "calibration_loss",
            "total_actor_loss",
        }


def test_p1f_objective_audit_passes_without_training() -> None:
    report = run_p1f_audit()
    assert report["verdict"] == "P1F_OBJECTIVE_AND_FAIRNESS_AUDIT_PASS"
    assert all(report["checks"].values())
    assert report["training_started"] is False
