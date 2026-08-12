"""Project-facing wrapper for canonical survival calculations."""

from __future__ import annotations

import numpy as np

from .reference_survival import km_curve, rmst


def build_exposure(
    recovery_steps: np.ndarray,
    recovered: np.ndarray,
    censor_steps: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    recovery_steps = np.asarray(recovery_steps, dtype=float)
    recovered = np.asarray(recovered, dtype=bool)
    censor_steps = np.asarray(censor_steps, dtype=float)
    if not (recovery_steps.shape == recovered.shape == censor_steps.shape):
        raise ValueError("recovery_steps, recovered, and censor_steps must have equal shape")
    durations = np.where(recovered, recovery_steps, censor_steps)
    return durations, recovered


def tau_specific_observed_delta(
    full_by_seed: dict[int, tuple[np.ndarray, np.ndarray]],
    comparator_by_seed: dict[int, tuple[np.ndarray, np.ndarray]],
    tau: float,
) -> float:
    seeds = sorted(set(full_by_seed) & set(comparator_by_seed))
    return float(
        np.mean(
            [rmst(*full_by_seed[s], tau) - rmst(*comparator_by_seed[s], tau) for s in seeds]
        )
    )
