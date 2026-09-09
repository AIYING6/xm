"""Task-regret value of information for budgeted active diagnosis.

The functions are deliberately independent of PPO.  They define the frozen
decision object that a later policy may approximate, and are testable without
environment interaction or trainable parameters.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import numpy as np


@dataclass(frozen=True)
class ProbeValue:
    prior_regret: float
    expected_posterior_regret: float
    cost: float
    net_value: float
    observation_probabilities: tuple[float, ...]


def _probability_vector(values: np.ndarray, name: str) -> np.ndarray:
    vector = np.asarray(values, dtype=np.float64)
    if vector.ndim != 1 or vector.size == 0:
        raise ValueError(f"{name} must be a non-empty vector")
    if np.any(vector < 0.0) or not np.isclose(vector.sum(), 1.0, atol=1e-10):
        raise ValueError(f"{name} must be a probability vector")
    return vector


def _task_values(task_values: np.ndarray, hypothesis_count: int) -> np.ndarray:
    values = np.asarray(task_values, dtype=np.float64)
    if values.ndim != 2 or values.shape[0] != hypothesis_count or values.shape[1] == 0:
        raise ValueError("task_values must have shape [hypothesis, recovery_action]")
    if not np.all(np.isfinite(values)):
        raise ValueError("task_values must be finite")
    return values


def bayes_task_regret(belief: np.ndarray, task_values: np.ndarray) -> float:
    """Return oracle value minus the best action value under the belief."""
    belief = _probability_vector(belief, "belief")
    values = _task_values(task_values, belief.size)
    oracle = float(np.dot(belief, np.max(values, axis=1)))
    informed_only_by_belief = float(np.max(belief @ values))
    regret = oracle - informed_only_by_belief
    if regret < -1e-10:
        raise AssertionError("Bayes task regret cannot be negative")
    return max(0.0, regret)


def decision_equivalence_classes(task_values: np.ndarray, atol: float = 1e-10) -> tuple[tuple[int, ...], ...]:
    """Group hypotheses sharing the same set of optimal recovery actions."""
    values = np.asarray(task_values, dtype=np.float64)
    if values.ndim != 2 or values.shape[0] == 0 or values.shape[1] == 0:
        raise ValueError("task_values must be a non-empty matrix")
    groups: dict[tuple[int, ...], list[int]] = {}
    for hypothesis, row in enumerate(values):
        best = float(np.max(row))
        signature = tuple(int(index) for index in np.flatnonzero(np.isclose(row, best, atol=atol, rtol=0.0)))
        groups.setdefault(signature, []).append(hypothesis)
    return tuple(tuple(indices) for indices in groups.values())


def decision_relevant_probe_value(
    belief: np.ndarray,
    task_values: np.ndarray,
    observation_kernel: np.ndarray,
    cost: float,
) -> ProbeValue:
    """Compute expected Bayes-task-regret reduction net of physical cost."""
    belief = _probability_vector(belief, "belief")
    values = _task_values(task_values, belief.size)
    kernel = np.asarray(observation_kernel, dtype=np.float64)
    if kernel.ndim != 2 or kernel.shape[0] != belief.size or kernel.shape[1] == 0:
        raise ValueError("observation_kernel must have shape [hypothesis, observation]")
    if np.any(kernel < 0.0) or not np.allclose(kernel.sum(axis=1), 1.0, atol=1e-10):
        raise ValueError("each observation-kernel row must be a probability vector")
    if cost < 0.0 or not np.isfinite(cost):
        raise ValueError("probe cost must be finite and nonnegative")

    prior_regret = bayes_task_regret(belief, values)
    observation_probabilities = belief @ kernel
    expected_posterior_regret = 0.0
    for observation, probability in enumerate(observation_probabilities):
        if probability <= 0.0:
            continue
        posterior = belief * kernel[:, observation] / probability
        expected_posterior_regret += float(probability) * bayes_task_regret(posterior, values)
    net = prior_regret - expected_posterior_regret - float(cost)
    return ProbeValue(
        prior_regret=prior_regret,
        expected_posterior_regret=expected_posterior_regret,
        cost=float(cost),
        net_value=net,
        observation_probabilities=tuple(float(value) for value in observation_probabilities),
    )


def select_probe(
    belief: np.ndarray,
    task_values: np.ndarray,
    kernels: Mapping[str, np.ndarray],
    costs: Mapping[str, float],
    budget_remaining: bool,
) -> tuple[str | None, dict[str, ProbeValue]]:
    """Select the highest positive-value legal probe, or decline to probe."""
    if kernels.keys() != costs.keys():
        raise ValueError("probe kernels and costs must use identical names")
    values = {
        name: decision_relevant_probe_value(belief, task_values, kernel, costs[name])
        for name, kernel in kernels.items()
    }
    if not budget_remaining or not values:
        return None, values
    best = max(values, key=lambda name: values[name].net_value)
    return (best if values[best].net_value > 0.0 else None), values
