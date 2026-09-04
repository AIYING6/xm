"""Zero-training mechanical audit of the frozen RACG-PPO C0.5 formula."""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy.optimize import minimize


ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class RACGResult:
    direction: np.ndarray
    ordinary: np.ndarray
    correction: np.ndarray
    reliability: float
    group_agreement: np.ndarray
    pooled_agreement: float
    strength: float
    weights: np.ndarray
    solver_ok: bool


def positive_cosine(left: np.ndarray, right: np.ndarray, relative_epsilon: float) -> float:
    left = np.asarray(left, dtype=np.float64)
    right = np.asarray(right, dtype=np.float64)
    scale = max(float(np.linalg.norm(left)), float(np.linalg.norm(right)))
    if not np.isfinite(scale) or scale == 0.0:
        return 0.0
    denominator = float(np.linalg.norm(left) * np.linalg.norm(right))
    epsilon = relative_epsilon * scale * scale
    value = float(np.dot(left, right) / (denominator + epsilon))
    return float(np.clip(value, 0.0, 1.0))


def solve_simplex_proposal(
    gradients: np.ndarray,
    anchor: np.ndarray,
    strength: float,
    initial: np.ndarray,
    relative_epsilon: float,
    ftol: float,
    max_iterations: int,
) -> tuple[np.ndarray, bool]:
    """Solve the seven-coefficient average-anchored CAGrad subproblem."""
    gradients = np.asarray(gradients, dtype=np.float64)
    anchor = np.asarray(anchor, dtype=np.float64)
    initial = np.asarray(initial, dtype=np.float64)
    anchor_norm = float(np.linalg.norm(anchor))
    scale = max(anchor_norm, float(np.max(np.linalg.norm(gradients, axis=0))), np.finfo(float).tiny)
    # This objective is homogeneous of degree two. A common normalization
    # preserves its minimizer and makes SLSQP termination scale-independent.
    normalized_gradients = gradients / scale
    normalized_anchor = anchor / scale
    normalized_anchor_norm = float(np.linalg.norm(normalized_anchor))
    epsilon = relative_epsilon

    def objective(weights: np.ndarray) -> float:
        proposal = normalized_gradients @ weights
        smooth_norm = float(np.sqrt(np.dot(proposal, proposal) + epsilon * epsilon))
        return float(np.dot(proposal, normalized_anchor) + strength * normalized_anchor_norm * smooth_norm)

    def jacobian(weights: np.ndarray) -> np.ndarray:
        proposal = normalized_gradients @ weights
        smooth_norm = float(np.sqrt(np.dot(proposal, proposal) + epsilon * epsilon))
        return normalized_gradients.T @ normalized_anchor + strength * normalized_anchor_norm * (normalized_gradients.T @ proposal) / smooth_norm

    result = minimize(
        objective,
        initial,
        method="SLSQP",
        jac=jacobian,
        bounds=[(0.0, 1.0)] * initial.size,
        constraints=[{"type": "eq", "fun": lambda w: float(np.sum(w) - 1.0), "jac": lambda w: np.ones_like(w)}],
        options={"ftol": ftol, "maxiter": max_iterations, "disp": False},
    )
    weights = np.asarray(result.x, dtype=np.float64)
    valid = bool(
        result.success
        and np.all(np.isfinite(weights))
        and np.min(weights) >= -1e-9
        and abs(float(np.sum(weights)) - 1.0) <= 1e-8
    )
    if not valid:
        return initial.copy(), False
    weights = np.clip(weights, 0.0, 1.0)
    weights /= float(np.sum(weights))
    return weights, True


def racg_direction(
    split_a: np.ndarray,
    split_b: np.ndarray,
    entropy_gradient: np.ndarray,
    masses: np.ndarray,
    maximum_strength: float = 0.5,
    correction_cap: float = 0.5,
    relative_epsilon: float = 1e-12,
    solver_ftol: float = 1e-12,
    solver_max_iterations: int = 256,
) -> RACGResult:
    """Compute the frozen pre-Adam RACG direction from training-only gradients."""
    split_a = np.asarray(split_a, dtype=np.float64)
    split_b = np.asarray(split_b, dtype=np.float64)
    entropy_gradient = np.asarray(entropy_gradient, dtype=np.float64)
    masses = np.asarray(masses, dtype=np.float64)
    if split_a.shape != split_b.shape or split_a.ndim != 2:
        raise ValueError("cross-fit arrays must have matching [parameters, groups] shapes")
    if split_a.shape[1] != masses.size or entropy_gradient.shape != (split_a.shape[0],):
        raise ValueError("gradient dimensions do not match masses or entropy gradient")
    if not np.all(np.isfinite(split_a)) or not np.all(np.isfinite(split_b)) or not np.all(np.isfinite(entropy_gradient)):
        raise ValueError("input gradients must be finite")
    if np.any(masses < 0.0) or abs(float(np.sum(masses)) - 1.0) > 1e-12:
        raise ValueError("group masses must lie on the simplex")

    agreement = np.array(
        [positive_cosine(split_a[:, index], split_b[:, index], relative_epsilon) for index in range(masses.size)]
    )
    pooled_a = split_a @ masses
    pooled_b = split_b @ masses
    pooled_agreement = positive_cosine(pooled_a, pooled_b, relative_epsilon)
    reliability = float(np.clip(pooled_agreement * float(np.dot(masses, agreement)), 0.0, 1.0))

    group_mean = 0.5 * (split_a + split_b)
    surrogate_anchor = group_mean @ masses
    ordinary = surrogate_anchor + entropy_gradient
    shrunk = agreement[np.newaxis, :] * group_mean + (1.0 - agreement[np.newaxis, :]) * surrogate_anchor[:, np.newaxis]
    strength = float(maximum_strength * reliability)

    if strength == 0.0 or float(np.linalg.norm(surrogate_anchor)) == 0.0:
        return RACGResult(
            direction=ordinary.copy(), ordinary=ordinary, correction=np.zeros_like(ordinary), reliability=reliability,
            group_agreement=agreement, pooled_agreement=pooled_agreement, strength=0.0,
            weights=masses.copy(), solver_ok=True,
        )

    weights, solver_ok = solve_simplex_proposal(
        shrunk, surrogate_anchor, strength, masses, relative_epsilon, solver_ftol, solver_max_iterations
    )
    if not solver_ok:
        return RACGResult(
            direction=ordinary.copy(), ordinary=ordinary, correction=np.zeros_like(ordinary), reliability=reliability,
            group_agreement=agreement, pooled_agreement=pooled_agreement, strength=0.0,
            weights=masses.copy(), solver_ok=False,
        )

    proposal = shrunk @ weights
    proposal_norm = float(np.linalg.norm(proposal))
    scale = max(float(np.linalg.norm(surrogate_anchor)), float(np.max(np.linalg.norm(shrunk, axis=0))), np.finfo(float).tiny)
    epsilon = relative_epsilon * scale
    correction = strength * float(np.linalg.norm(surrogate_anchor)) * proposal / max(proposal_norm, epsilon)
    ordinary_norm = float(np.linalg.norm(ordinary))
    correction_norm = float(np.linalg.norm(correction))
    if ordinary_norm == 0.0 or correction_norm == 0.0:
        correction = np.zeros_like(ordinary)
    else:
        correction *= min(1.0, correction_cap * ordinary_norm / correction_norm)
    direction = ordinary + correction
    if not np.all(np.isfinite(direction)):
        direction = ordinary.copy()
        correction = np.zeros_like(ordinary)
        solver_ok = False
        strength = 0.0
    return RACGResult(
        direction=direction, ordinary=ordinary, correction=correction, reliability=reliability,
        group_agreement=agreement, pooled_agreement=pooled_agreement, strength=strength,
        weights=weights, solver_ok=solver_ok,
    )


def run_audit(freeze: dict) -> dict:
    masses = np.asarray(freeze["group_mass"], dtype=np.float64)
    proposal = freeze["proposal"]
    correction = freeze["correction"]
    numerics = freeze["numerics"]
    kwargs = {
        "maximum_strength": float(proposal["maximum_strength"]),
        "correction_cap": float(correction["norm_cap_fraction_of_complete_ordinary_direction"]),
        "relative_epsilon": float(numerics["relative_epsilon"]),
        "solver_ftol": float(proposal["solver_ftol"]),
        "solver_max_iterations": int(proposal["solver_max_iterations"]),
    }
    rng = np.random.default_rng(20260904)
    a = rng.normal(size=(97, 7))
    b = a + rng.normal(scale=0.35, size=(97, 7))
    entropy = rng.normal(scale=0.05, size=97)
    base = racg_direction(a, b, entropy, masses, **kwargs)
    swapped = racg_direction(b, a, entropy, masses, **kwargs)
    scaled = racg_direction(3.25 * a, 3.25 * b, 3.25 * entropy, masses, **kwargs)

    permutation = np.array([0, 3, 6, 2, 5, 1, 4])
    permuted = racg_direction(a[:, permutation], b[:, permutation], entropy, masses[permutation], **kwargs)
    opposite = racg_direction(a, -a, entropy, masses, **kwargs)

    lower_bound_ok = True
    simplex_ok = True
    finite_ok = True
    fallback_ok = True
    material_count = 0
    for _ in range(512):
        left = rng.normal(size=(53, 7))
        right = left + rng.normal(scale=rng.uniform(0.0, 3.0), size=(53, 7))
        entropy_case = rng.normal(scale=0.1, size=53)
        result = racg_direction(left, right, entropy_case, masses, **kwargs)
        lower_bound_ok &= bool(np.linalg.norm(result.direction) + 1e-10 >= 0.5 * np.linalg.norm(result.ordinary))
        simplex_ok &= bool(np.min(result.weights) >= -1e-10 and abs(float(np.sum(result.weights)) - 1.0) <= 1e-8)
        finite_ok &= bool(np.all(np.isfinite(result.direction)))
        fallback_ok &= bool(result.solver_ok or np.array_equal(result.direction, result.ordinary))
        material_count += int(np.linalg.norm(result.correction) > 1e-10)

    checks = {
        "seven_groups_and_frozen_mass": freeze["groups"] == ["N", "F0", "TE", "TL", "DS", "DL", "CP"] and abs(float(np.sum(masses)) - 1.0) < 1e-12,
        "cross_fit_swap_invariant": np.allclose(base.direction, swapped.direction, atol=1e-10, rtol=1e-10),
        "positive_scale_equivariant": np.allclose(scaled.direction, 3.25 * base.direction, atol=1e-9, rtol=1e-9),
        "failure_group_permutation_invariant": np.allclose(permuted.direction, base.direction, atol=1e-6, rtol=1e-6),
        "zero_reliability_exact_ordinary_fallback": opposite.reliability == 0.0 and np.array_equal(opposite.direction, opposite.ordinary),
        "correction_cap_nonfreeze_bound": lower_bound_ok,
        "simplex_solver_valid": simplex_ok,
        "finite_direction_or_exact_fallback": finite_ok and fallback_ok,
        "formula_has_nonzero_actuation": material_count > 0,
        "no_hard_certificate_or_zero_rejection": correction["hard_group_certificate"] is False and correction["zero_step_rejection"] is False,
        "training_only_and_no_adaptive_collection": freeze["information_boundary"]["training_only"] is True and freeze["information_boundary"]["evaluation_input"] is False and freeze["information_boundary"]["adaptive_collection"] is False,
        "c1_and_training_not_authorized": freeze["authorization"]["c1_implementation"] is False and freeze["authorization"]["ppo_updates"] is False and freeze["authorization"]["fresh_seed_training"] is False,
        "automatic_continuation_absent": freeze["authorization"]["automatic_continuation"] is False
    }
    verdict = "RACG_C05_FORMULA_FROZEN_FOR_C1_IMPLEMENTATION" if all(checks.values()) else "RACG_C05_FORMULA_NO_GO"
    return {
        "protocol": freeze["protocol"], "verdict": verdict, "checks": checks,
        "witness": {
            "base_reliability": base.reliability,
            "base_strength": base.strength,
            "base_correction_to_ordinary_norm": float(np.linalg.norm(base.correction) / np.linalg.norm(base.ordinary)),
            "random_cases": 512,
            "material_correction_cases": material_count,
            "maximum_strength": kwargs["maximum_strength"],
            "correction_cap": kwargs["correction_cap"],
            "minimum_pre_adam_direction_fraction": 1.0 - kwargs["correction_cap"]
        },
        "environment_steps": 0, "ppo_updates": 0, "evaluation_started": False,
        "implementation_started": False, "fresh_seed_training_authorized": False,
        "automatic_continuation": False
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze", type=Path, default=ROOT / "configs" / "racg_ppo_c05_formula_freeze.json")
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("--execute is required")
    freeze = json.loads(args.freeze.read_text(encoding="utf-8"))
    result = run_audit(freeze)
    args.output_root.mkdir(parents=True, exist_ok=False)
    (args.output_root / "RACG_C05_RESULT.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
