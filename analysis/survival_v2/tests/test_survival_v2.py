from __future__ import annotations

import numpy as np

from analysis.survival_v2.project_survival import tau_specific_observed_delta
from analysis.survival_v2.reference_survival import km_curve, rmst


def test_no_censor_manual_rmst():
    times = np.array([1.0, 2.0, 3.0])
    events = np.array([1, 1, 1], dtype=bool)
    assert np.isclose(rmst(times, events, 3.0), 2.0)


def test_all_censor_survival_is_one():
    times = np.array([1.0, 2.0, 3.0])
    events = np.array([0, 0, 0], dtype=bool)
    assert np.isclose(rmst(times, events, 3.0), 3.0)


def test_event_and_censor_tie_remove_both_from_risk_set():
    times = np.array([1.0, 1.0, 2.0])
    events = np.array([1, 0, 1], dtype=bool)
    # S(1) = 2/3, then both observations at t=1 leave the risk set;
    # the t=2 event cannot change S because the risk set is empty.
    assert np.isclose(rmst(times, events, 2.0), 1.0 + 2.0 / 3.0)


def test_horizon_censoring_is_not_an_event():
    times = np.array([2.0, 2.0])
    events = np.array([0, 0], dtype=bool)
    assert np.isclose(rmst(times, events, 2.0), 2.0)


def test_km_curve_starts_at_one_and_is_monotone():
    t, s = km_curve(np.array([1.0, 2.0, 4.0]), np.array([1, 0, 1], dtype=bool), tau=4.0)
    assert t[0] == 0.0 and s[0] == 1.0
    assert np.all(np.diff(s) <= 1e-12)


def test_tau_specific_observed_delta_changes_with_tau():
    full = {0: (np.array([1.0, 3.0]), np.array([1, 1], dtype=bool))}
    comp = {0: (np.array([2.0, 3.0]), np.array([1, 1], dtype=bool))}
    assert tau_specific_observed_delta(full, comp, 1.0) != tau_specific_observed_delta(full, comp, 3.0)
