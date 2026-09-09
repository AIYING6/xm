"""Audit differentiability and fairness of the frozen P1F actor objective."""

from __future__ import annotations

import argparse
import inspect
import json
from pathlib import Path
import sys

import torch


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from algorithms.epistemic_commitment import (
    CapacityMatchedRecurrentActor,
    CommitmentActorConfig,
    InformationSetCommitmentActor,
    parameter_count,
)
from algorithms.epistemic_commitment_objective import commitment_actor_loss


PILOT_SEEDS = (98101, 98102, 98103)
METHODS = ("information_set_commitment", "capacity_and_risk_matched_recurrent")


def _gradient_summary(model: torch.nn.Module, loss: torch.Tensor) -> dict[str, bool]:
    model.zero_grad(set_to_none=True)
    loss.backward()
    summary: dict[str, bool] = {}
    for name, parameter in model.named_parameters():
        summary[name] = parameter.grad is not None and bool(torch.isfinite(parameter.grad).all())
    return summary


def run_p1f_audit(seed: int = 20260909) -> dict:
    torch.manual_seed(seed)
    config = CommitmentActorConfig(
        input_dim=39,
        hidden_dim=32,
        robust_softmin_temperature=0.10,
    )
    candidate = InformationSetCommitmentActor(config)
    baseline = CapacityMatchedRecurrentActor(config)
    history = torch.randn(12, 2, config.input_dim)
    priors = torch.tensor([0.15, 0.45, 0.85] * 4, dtype=torch.float32)
    actions = torch.tensor([0, 1, 2] * 4, dtype=torch.int64)
    advantages = torch.tensor([1.0, -0.5, 0.75, -1.0, 0.4, 1.2] * 2, dtype=torch.float32)

    candidate_output = candidate(history)
    baseline_output = baseline(history)
    with torch.no_grad():
        candidate_old = torch.distributions.Categorical(logits=candidate_output["mode_logits"]).log_prob(actions)
        baseline_old = torch.distributions.Categorical(logits=baseline_output["mode_logits"]).log_prob(actions)

    candidate_loss, candidate_telemetry = commitment_actor_loss(
        candidate_output, actions, candidate_old, advantages, priors
    )
    baseline_loss, baseline_telemetry = commitment_actor_loss(
        baseline_output, actions, baseline_old, advantages, priors
    )
    candidate_gradients = _gradient_summary(candidate, candidate_loss)
    baseline_gradients = _gradient_summary(baseline, baseline_loss)

    candidate_probs = torch.softmax(candidate_output["mode_logits"], dim=-1)
    baseline_probs = torch.softmax(baseline_output["mode_logits"], dim=-1)
    objective_parameters = set(inspect.signature(commitment_actor_loss).parameters)
    forbidden = {"delivered", "delivery", "ack", "global_state", "teammate_belief"}
    candidate_count = parameter_count(candidate)
    baseline_count = parameter_count(baseline)
    checks = {
        "candidate_and_baseline_parameter_counts_exact": candidate_count == baseline_count,
        "candidate_mode_distribution_finite_and_normalized": bool(torch.isfinite(candidate_probs).all())
        and bool(torch.allclose(candidate_probs.sum(-1), torch.ones(12))),
        "baseline_mode_distribution_finite_and_normalized": bool(torch.isfinite(baseline_probs).all())
        and bool(torch.allclose(baseline_probs.sum(-1), torch.ones(12))),
        "candidate_loss_finite": bool(torch.isfinite(candidate_loss)),
        "baseline_loss_finite": bool(torch.isfinite(baseline_loss)),
        "candidate_interval_and_value_heads_receive_gradient": all(candidate_gradients.values()),
        "baseline_active_mode_head_receives_gradient": all(baseline_gradients.values()),
        "same_actor_loss_function_used_for_both": candidate_telemetry.keys() == baseline_telemetry.keys(),
        "objective_interface_contains_no_delivery_truth": not bool(objective_parameters & forbidden),
        "calibration_targets_public_prior_not_realized_delivery": "reliability_prior" in objective_parameters
        and "delivered" not in objective_parameters,
        "pilot_budget_within_15m_cap": len(PILOT_SEEDS) * len(METHODS) * 1_000_000 <= 15_000_000,
        "pilot_seeds_exact": PILOT_SEEDS == (98101, 98102, 98103),
    }
    passed = all(checks.values())
    return {
        "protocol": "EPISTEMIC-COMMITMENT-P1F-OBJECTIVE-AUDIT-V1",
        "verdict": "P1F_OBJECTIVE_AND_FAIRNESS_AUDIT_PASS" if passed else "P1F_OBJECTIVE_AND_FAIRNESS_AUDIT_FAIL",
        "checks": checks,
        "parameter_counts": {"candidate": candidate_count, "capacity_matched_recurrent": baseline_count},
        "gradient_paths": {"candidate": candidate_gradients, "baseline": baseline_gradients},
        "frozen_hyperparameters": {
            "ppo_clip_epsilon": 0.20,
            "calibration_weight": 0.10,
            "ambiguity_radius": 0.05,
            "robust_softmin_temperature": 0.10,
        },
        "pilot": {
            "methods": list(METHODS),
            "training_seeds": list(PILOT_SEEDS),
            "fixed_endpoint_steps_per_run": 1_000_000,
            "maximum_total_environment_steps": 6_000_000,
        },
        "evidence_boundary": (
            "This audit proves a finite differentiable loss, active gradient paths, exact capacity matching, "
            "and absence of realized-delivery labels from the actor objective. It does not prove calibration, "
            "learnability, novelty, or empirical improvement."
        ),
        "training_started": False,
        "training_environment_steps": 0,
        "ppo_updates": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = run_p1f_audit()
    payload = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(payload + "\n")
    print(payload)
    if report["verdict"].endswith("FAIL"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
