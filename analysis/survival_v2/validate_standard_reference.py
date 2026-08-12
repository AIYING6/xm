"""Cross-check v2 KM/RMST against lifelines when installed.

This is intentionally fail-closed: absence of lifelines is a Gate B1 blocker,
not a reason to silently accept the project implementation as a third-party
reference.
"""

from __future__ import annotations

import importlib.metadata
import sys

import numpy as np

from reference_survival import rmst


TOLERANCE = 1e-10


def main() -> int:
    try:
        from lifelines import KaplanMeierFitter
    except ImportError:
        print("GATE_B1_BLOCKED: lifelines is not installed", file=sys.stderr)
        return 2

    version = importlib.metadata.version("lifelines")
    cases = {
        "no_censoring": (np.array([1.0, 2.0, 3.0]), np.ones(3, dtype=bool)),
        "all_censoring": (np.array([1.0, 2.0, 3.0]), np.zeros(3, dtype=bool)),
        "ties": (np.array([1.0, 1.0, 2.0, 2.0]), np.array([1, 0, 1, 0], dtype=bool)),
        "horizon_censoring": (np.array([1.0, 2.0, 10.0]), np.array([1, 1, 0], dtype=bool)),
    }
    for name, (times, events) in cases.items():
        tau = 2.5
        fitter = KaplanMeierFitter().fit(times, event_observed=events)
        reference_rmst = float(fitter.survival_function_at_times(0).iloc[0])  # construction sanity check
        del reference_rmst
        # lifelines exposes the same step function; integrate its timeline on
        # the union of event/censor times and the requested horizon.
        grid = sorted(set([0.0, tau, *times[times < tau].tolist()]))
        area = 0.0
        for left, right in zip(grid, grid[1:]):
            s = float(fitter.survival_function_at_times(left).iloc[0])
            area += s * (right - left)
        ours = rmst(times, events, tau)
        if abs(ours - area) > TOLERANCE:
            print(f"FAIL {name}: ours={ours} lifelines={area} tol={TOLERANCE}", file=sys.stderr)
            return 1
    print(f"PASS lifelines={version} tolerance={TOLERANCE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
