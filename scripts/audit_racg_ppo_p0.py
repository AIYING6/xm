"""Mechanical zero-training audit for the RACG-PPO design contract.

The audit has no environment, model, checkpoint, evaluation-tape or optimizer
dependency.  It checks algebraic invariants that distinguish RACG-PPO from the
closed TGTR formulation.  It does not implement or train the candidate.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]


def cross_fitted_gram(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    """Symmetric cross-fitted estimate of the group-gradient Gram matrix."""
    return 0.5 * (left.T @ right + right.T @ left)


def bounded_anchored_direction(
    ordinary: np.ndarray,
    robust: np.ndarray,
    reliability: float,
    cap_fraction: float,
) -> np.ndarray:
    """Blend a robust proposal into an ordinary anchor without permitting freeze."""
    ordinary = np.asarray(ordinary, dtype=np.float64)
    robust = np.asarray(robust, dtype=np.float64)
    if ordinary.shape != robust.shape:
        raise ValueError("ordinary and robust directions must have the same shape")
    if not 0.0 <= reliability <= 1.0:
        raise ValueError("reliability must lie in [0, 1]")
    if not 0.0 <= cap_fraction < 1.0:
        raise ValueError("cap_fraction must lie in [0, 1)")
    anchor_norm = float(np.linalg.norm(ordinary))
    correction = robust - ordinary
    correction_norm = float(np.linalg.norm(correction))
    if anchor_norm == 0.0 or correction_norm == 0.0:
        return ordinary.copy()
    correction *= min(1.0, cap_fraction * anchor_norm / correction_norm)
    return ordinary + reliability * correction


def run_audit(freeze: dict) -> dict:
    candidate = freeze["candidate"]
    masses = candidate["group_mass"]
    groups = candidate["groups"]
    cap = float(candidate["correction_norm_cap_fraction"])

    # Deterministic algebra checks.
    rng = np.random.default_rng(20260904)
    ordinary = rng.normal(size=257)
    robust = rng.normal(size=257)
    fallback = bounded_anchored_direction(ordinary, robust, 0.0, cap)
    for reliability in np.linspace(0.0, 1.0, 101):
        direction = bounded_anchored_direction(ordinary, robust, float(reliability), cap)
        lower_bound = (1.0 - cap) * np.linalg.norm(ordinary)
        if np.linalg.norm(direction) + 1e-12 < lower_bound:
            raise AssertionError("bounded correction violated the non-freeze lower bound")

    # Cross-fitting identity: independent zero-mean noise removes the positive
    # covariance term E[E^T E] present in a same-sample Gram estimate.  A fixed
    # Monte-Carlo check protects the implementation formula; the proof is in the
    # mathematical contract and this simulation is not scientific evidence.
    true_gradient = rng.normal(size=(31, len(groups)))
    true_gram = true_gradient.T @ true_gradient
    naive_error = []
    cross_error = []
    for _ in range(4096):
        left = true_gradient + rng.normal(scale=1.25, size=true_gradient.shape)
        right = true_gradient + rng.normal(scale=1.25, size=true_gradient.shape)
        naive = left.T @ left
        cross = cross_fitted_gram(left, right)
        naive_error.append(np.linalg.norm(naive - true_gram, ord="fro"))
        cross_error.append(np.linalg.norm(cross - true_gram, ord="fro"))

    checks = {
        "seven_groups_exact": groups == ["N", "F0", "TE", "TL", "DS", "DL", "CP"],
        "group_mass_sums_to_one": abs(sum(float(masses[g]) for g in groups) - 1.0) < 1e-12,
        "nominal_mass_half": abs(float(masses["N"]) - 0.5) < 1e-12,
        "failure_mass_equal": len({round(float(masses[g]), 14) for g in groups[1:]}) == 1,
        "ordinary_fallback_exact": np.array_equal(fallback, ordinary),
        "nonfreeze_bound_verified": cap < 1.0,
        "cross_fit_reduces_noise_bias": float(np.mean(cross_error)) < float(np.mean(naive_error)),
        "hard_certificate_absent": candidate["hard_group_nonharm_certificate"] is False,
        "zero_step_rejection_absent": candidate["rejection_to_zero_step"] is False,
        "adaptive_sampler_absent": candidate["adaptive_sampler"] is False,
        "evaluation_input_absent": candidate["evaluation_input"] is False,
        "c1_not_authorized": freeze["authorization"]["c1_implementation"] is False,
        "training_not_authorized": freeze["authorization"]["fresh_seed_training"] is False,
        "automatic_continuation_absent": freeze["authorization"]["automatic_continuation"] is False
    }
    verdict = "RACG_P0_FEASIBLE_FOR_C1_DESIGN_ONLY" if all(checks.values()) else "RACG_P0_NO_GO"
    return {
        "protocol": freeze["protocol"],
        "verdict": verdict,
        "checks": checks,
        "proof_witness": {
            "correction_norm_cap_fraction": cap,
            "minimum_actor_direction_fraction_of_ordinary": 1.0 - cap,
            "mean_naive_gram_error": float(np.mean(naive_error)),
            "mean_cross_fitted_gram_error": float(np.mean(cross_error)),
            "cross_fit_error_ratio": float(np.mean(cross_error) / np.mean(naive_error))
        },
        "environment_steps": 0,
        "ppo_updates": 0,
        "evaluation_started": False,
        "implementation_started": False,
        "fresh_seed_training_authorized": False,
        "automatic_continuation": False
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze", type=Path, default=ROOT / "configs" / "racg_ppo_p0_freeze.json")
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("--execute is required")
    freeze = json.loads(args.freeze.read_text(encoding="utf-8"))
    result = run_audit(freeze)
    args.output_root.mkdir(parents=True, exist_ok=False)
    (args.output_root / "RACG_P0_RESULT.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    (args.output_root / "RACG_P0_FINAL_VERDICT.md").write_text(
        "# RACG-PPO P0 final verdict\n\n"
        f"`{result['verdict']}`\n\n"
        "This is a zero-training design result. It authorizes no implementation, rollout, PPO update, "
        "fresh-seed experiment, cloud launch, or automatic continuation.\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
