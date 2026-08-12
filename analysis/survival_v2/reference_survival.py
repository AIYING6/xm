"""Independent discrete-time Kaplan--Meier and RMST reference implementation.

The implementation groups equal event/censor times before updating the risk set.
It is deliberately independent from the historical survival script.
"""

from __future__ import annotations

import numpy as np


def km_curve(times: np.ndarray, events: np.ndarray, tau: float | None = None) -> tuple[np.ndarray, np.ndarray]:
    times = np.asarray(times, dtype=float)
    events = np.asarray(events, dtype=bool)
    if times.shape != events.shape or times.ndim != 1 or len(times) == 0:
        raise ValueError("times and events must be non-empty one-dimensional arrays of equal shape")
    if np.any(times < 0):
        raise ValueError("survival times must be non-negative")
    horizon = float(np.max(times) if tau is None else tau)
    if horizon < 0:
        raise ValueError("tau must be non-negative")
    unique = np.unique(times[(times <= horizon)])
    survival = 1.0
    n_risk = len(times)
    out_t = [0.0]
    out_s = [1.0]
    for t in unique:
        if t > horizon:
            break
        at_time = times == t
        d = int(np.sum(at_time & events))
        c = int(np.sum(at_time & ~events))
        if d:
            if n_risk <= 0:
                raise RuntimeError("risk set exhausted before event")
            survival *= 1.0 - d / n_risk
            out_t.append(float(t))
            out_s.append(float(survival))
        n_risk -= d + c
    return np.asarray(out_t), np.asarray(out_s)


def rmst(times: np.ndarray, events: np.ndarray, tau: float) -> float:
    if tau < 0:
        raise ValueError("tau must be non-negative")
    times = np.asarray(times, dtype=float)
    events = np.asarray(events, dtype=bool)
    if len(times) == 0:
        return 0.0
    unique = np.unique(times[times < tau])
    survival = 1.0
    n_risk = len(times)
    previous = 0.0
    area = 0.0
    for t in unique:
        area += survival * (float(t) - previous)
        at_time = times == t
        d = int(np.sum(at_time & events))
        c = int(np.sum(at_time & ~events))
        if d:
            survival *= 1.0 - d / n_risk
        n_risk -= d + c
        previous = float(t)
    area += survival * (float(tau) - previous)
    return float(area)


def hierarchical_delta_observed(
    full_by_seed: dict[int, tuple[np.ndarray, np.ndarray]],
    comparator_by_seed: dict[int, tuple[np.ndarray, np.ndarray]],
    tau: float,
) -> float:
    seeds = sorted(set(full_by_seed) & set(comparator_by_seed))
    if not seeds:
        raise ValueError("no common seeds")
    deltas = [
        rmst(*full_by_seed[seed], tau) - rmst(*comparator_by_seed[seed], tau)
        for seed in seeds
    ]
    return float(np.mean(deltas))
