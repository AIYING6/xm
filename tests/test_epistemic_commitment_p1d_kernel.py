from __future__ import annotations

import torch

from algorithms.epistemic_commitment import (
    CapacityMatchedRecurrentActor,
    CommitmentActorConfig,
    InformationSetCommitmentActor,
    MODE_COMMIT,
    MODE_DEFER,
    MODE_FALLBACK,
    parameter_count,
    probability_interval,
    select_robust_mode,
)
from scripts.audit_epistemic_commitment_p1d_kernel import run_kernel_audit


def test_probability_interval_is_ordered_and_bounded() -> None:
    logits = torch.tensor([[-20.0, 20.0], [0.0, 0.0], [20.0, 20.0]])
    interval = probability_interval(logits)
    assert torch.all(interval[:, 0] >= 0.0)
    assert torch.all(interval[:, 1] <= 1.0)
    assert torch.all(interval[:, 0] <= interval[:, 1])


def test_analytic_counterfactual_mode_ordering() -> None:
    endpoints = torch.tensor([[[-8.0, 10.0], [1.0, 5.0], [2.0, 2.0]]])
    low, _ = select_robust_mode(endpoints, torch.tensor([[0.10, 0.20]]))
    middle, _ = select_robust_mode(endpoints, torch.tensor([[0.40, 0.50]]))
    high, _ = select_robust_mode(endpoints, torch.tensor([[0.80, 0.90]]))
    assert int(low.item()) == MODE_FALLBACK
    assert int(middle.item()) == MODE_DEFER
    assert int(high.item()) == MODE_COMMIT


def test_candidate_and_baseline_are_exactly_parameter_matched() -> None:
    config = CommitmentActorConfig(input_dim=37, hidden_dim=32)
    candidate = InformationSetCommitmentActor(config)
    baseline = CapacityMatchedRecurrentActor(config)
    assert parameter_count(candidate) == parameter_count(baseline)
    assert torch.all(torch.any(baseline.mode_projection != 0.0, dim=0))


def test_p1d_kernel_audit_passes_without_training() -> None:
    report = run_kernel_audit()
    assert report["verdict"] == "P1D_COMMITMENT_KERNEL_AUDIT_PASS"
    assert all(report["checks"].values())
    assert report["training_started"] is False
