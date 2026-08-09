"""Deterministic P0-A regression tests; no training or policy evaluation."""
from __future__ import annotations

import sys
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.simple_ri_gmappo import (  # noqa: E402
    active_not_established_probability,
    establishment_cumulative_incidence,
    restricted_mean_time_to_establishment,
    rmte_selector_key,
    summarize_validation_event_records,
    terminal_failure_cumulative_incidence,
)


def record(*, event: bool, event_time: int = -1, terminal: bool = False, terminal_time: int = -1) -> dict:
    return {
        "event_observed": int(event),
        "event_time": event_time,
        "terminal_failure_observed": int(terminal),
        "terminal_failure_time": terminal_time,
    }


def test_terminal_failure_contributes_horizon() -> None:
    records = [record(event=False, terminal=True, terminal_time=20), record(event=True, event_time=50)]
    assert restricted_mean_time_to_establishment(records, 80.0) == 65.0


def test_administrative_horizon_contributes_horizon() -> None:
    records = [record(event=True, event_time=20), record(event=False)]
    assert restricted_mean_time_to_establishment(records, 80.0) == 50.0


def test_complete_follow_up_outcome_decomposition() -> None:
    records = [
        record(event=True, event_time=20),
        record(event=False, terminal=True, terminal_time=30),
        record(event=False),
    ]
    assert math.isclose(establishment_cumulative_incidence(records, 80.0), 1.0 / 3.0)
    assert math.isclose(terminal_failure_cumulative_incidence(records, 80.0), 1.0 / 3.0)
    assert math.isclose(active_not_established_probability(records, 80.0), 1.0 / 3.0)


def test_summary_has_no_censoring_primary_metric() -> None:
    summary = summarize_validation_event_records([
        record(event=True, event_time=20), record(event=False, terminal=True, terminal_time=30)
    ])
    required = {
        "eval_rmte80", "eval_establishment_probability80", "eval_terminal_failure_incidence80",
        "eval_active_not_established_probability80", "eval_rmte220",
    }
    assert required.issubset(summary)
    assert not any("censor" in key for key in summary)


def test_selector_prefers_terminal_safe_tie_then_earlier_update() -> None:
    common = {
        "eval_rmte80": 20.0,
        "eval_establishment_probability80": 0.5,
        "eval_rmte220": 60.0,
    }
    safer = {**common, "eval_terminal_failure_incidence80": 0.1}
    riskier = {**common, "eval_terminal_failure_incidence80": 0.2}
    assert rmte_selector_key(safer, 20) < rmte_selector_key(riskier, 10)
    assert rmte_selector_key(safer, 10) < rmte_selector_key(safer, 20)


def main() -> None:
    tests = [
        test_terminal_failure_contributes_horizon,
        test_administrative_horizon_contributes_horizon,
        test_complete_follow_up_outcome_decomposition,
        test_summary_has_no_censoring_primary_metric,
        test_selector_prefers_terminal_safe_tie_then_earlier_update,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"P0_A_TERMINAL_ESTIMAND_TEST_REPORT_V1_9: PASS ({len(tests)} tests)")


if __name__ == "__main__":
    main()
