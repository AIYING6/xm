"""Deterministic geometry utilities for A0 observability qualification.

This module is deliberately not a reinforcement-learning environment.  It
implements the smallest auditable bearing-only sensing model needed to decide
whether a later cooperative active-perception task can contain a genuine
viewpoint-complementarity decision.
"""
from __future__ import annotations

import numpy as np


def bearing_information(uav_position: np.ndarray, target_position: np.ndarray, measurement_variance: float) -> np.ndarray:
    """Return the 2-D Fisher information of a bearing observation.

    For bearing ``atan2(y_t-y_u, x_t-x_u)``, the Jacobian with respect to the
    target position is ``[-dy/r^2, dx/r^2]``.  The result is defined only for
    non-coincident UAV and target positions.
    """
    delta = np.asarray(target_position, dtype=np.float64) - np.asarray(uav_position, dtype=np.float64)
    squared_range = float(delta @ delta)
    if squared_range <= 1e-12:
        raise ValueError("bearing information is undefined at zero range")
    jacobian = np.asarray((-delta[1] / squared_range, delta[0] / squared_range), dtype=np.float64)
    return np.outer(jacobian, jacobian) / float(measurement_variance)


def posterior_covariance(prior_covariance: np.ndarray, information_terms: list[np.ndarray]) -> np.ndarray:
    """Compute the linear-Gaussian posterior covariance from Fisher terms."""
    precision = np.linalg.inv(np.asarray(prior_covariance, dtype=np.float64))
    for term in information_terms:
        precision = precision + np.asarray(term, dtype=np.float64)
    return np.linalg.inv(precision)


def log_determinant(covariance: np.ndarray) -> float:
    """Return log(det(P)); lower values indicate a more informative posterior."""
    sign, value = np.linalg.slogdet(np.asarray(covariance, dtype=np.float64))
    if sign <= 0:
        raise ValueError("covariance must be positive definite")
    return float(value)


def marginal_bearing_contributions(
    prior_covariance: np.ndarray,
    belief_position: np.ndarray,
    sensor_positions: list[np.ndarray] | np.ndarray,
    sensing_ranges: list[float] | np.ndarray,
    measurement_variances: list[float] | np.ndarray,
) -> np.ndarray:
    """Return each legal sensor's marginal reduction in posterior log-det.

    A contribution is the difference between the posterior without that
    sensor's legal bearing measurement and the posterior with all legal
    measurements.  The calculation uses the public belief position, not target
    truth, so it is eligible as training-time telemetry in a later CTDE study.
    Sensors outside their range receive zero contribution.
    """
    positions = np.asarray(sensor_positions, dtype=np.float64)
    ranges = np.asarray(sensing_ranges, dtype=np.float64)
    variances = np.asarray(measurement_variances, dtype=np.float64)
    terms: list[np.ndarray | None] = []
    for position, sensing_range, variance in zip(positions, ranges, variances):
        delta = np.asarray(belief_position, dtype=np.float64) - position
        if float(delta @ delta) > sensing_range ** 2 or float(delta @ delta) <= 1e-12:
            terms.append(None)
        else:
            terms.append(bearing_information(position, belief_position, float(variance)))
    active = [term for term in terms if term is not None]
    full_logdet = log_determinant(posterior_covariance(prior_covariance, active))
    values = np.zeros(len(terms), dtype=np.float64)
    for index, term in enumerate(terms):
        if term is None:
            continue
        without = [other for other_index, other in enumerate(terms) if other_index != index and other is not None]
        values[index] = log_determinant(posterior_covariance(prior_covariance, without)) - full_logdet
    return values
