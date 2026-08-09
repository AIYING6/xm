"""Read-only P0-A audit for terminal outcomes in the v1.9 event-time estimand."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.simple_ri_gmappo import km_rmst_from_event_records  # noqa: E402


def main() -> None:
    # A terminal collision at t=20 makes establishment impossible.  A surviving
    # episode establishes at t=50.  The current implementation censors the
    # collision at t=20, changing the risk set before the t=50 establishment.
    terminal_as_right_censor = [
        {"event_observed": 0, "event_time": -1, "censor_time": 20},
        {"event_observed": 1, "event_time": 50, "censor_time": 50},
    ]
    terminal_as_no_establishment_by_horizon = [
        {"event_observed": 0, "event_time": -1, "censor_time": 80},
        {"event_observed": 1, "event_time": 50, "censor_time": 50},
    ]
    current_rmst80 = km_rmst_from_event_records(terminal_as_right_censor, 80.0)
    horizon_capped_rmst80 = km_rmst_from_event_records(
        terminal_as_no_establishment_by_horizon, 80.0
    )
    if not horizon_capped_rmst80 > current_rmst80:
        raise RuntimeError("P0-A counterexample did not expose a changed risk set")
    report = {
        "audit": "P0_A_EVENT_ESTIMAND",
        "status": "P0_STATISTICAL_BLOCK",
        "current_record_semantics": {
            "terminal_collision_or_constraint": "event_observed=0; censor_time=terminal_step-onset",
            "administrative_horizon": "event_observed=0; censor_time=horizon-onset",
        },
        "counterexample": {
            "terminal_failure_time": 20,
            "other_episode_establishment_time": 50,
            "tau": 80,
            "current_km_rmst80": current_rmst80,
            "terminal_as_no_establishment_through_tau_rmst80": horizon_capped_rmst80,
            "difference": horizon_capped_rmst80 - current_rmst80,
        },
        "finding": (
            "An irreversible terminal failure is currently treated as ordinary right censoring, "
            "so it leaves the KM risk set before later establishment events."
        ),
        "required_before_D2": [
            "freeze an administrative-censor versus terminal-competing-outcome taxonomy",
            "define RMST and establishment-probability estimands under that taxonomy",
            "change event records and selector implementation only after author approval",
            "repeat D0 and D1 after an approved implementation repair",
        ],
    }
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
