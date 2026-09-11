"""Deterministic pressure-band audit for M1, with no learning involved."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from envs.freshness_uncertainty_monitoring_env import M1_SCENARIOS, FreshnessUncertaintyMonitoringEnv


def _target_by_uncertainty(env: FreshnessUncertaintyMonitoringEnv) -> int:
    return int(np.argmax(env.posterior_variance))


def _target_by_freshness(env: FreshnessUncertaintyMonitoringEnv) -> int:
    urgency = np.asarray(env.scenario.urgency_rate, dtype=np.float32)
    return int(np.argmax(env.age * urgency))


def _target_by_coupled_value(env: FreshnessUncertaintyMonitoringEnv) -> int:
    """Auditable illustrative rule, not the proposed learning method.

    The normalizers make the rule compare public quantities on a common scale.
    In a formal learner, the value representation is learned rather than this
    hard-coded score.
    """
    uncertainty = env.posterior_variance / max(float(np.max(env.posterior_variance)), 1e-6)
    freshness = env.age * np.asarray(env.scenario.urgency_rate, dtype=np.float32)
    freshness /= max(float(np.max(freshness)), 1e-6)
    return int(np.argmax(uncertainty + freshness))


def _hold(env: FreshnessUncertaintyMonitoringEnv, steps: int) -> None:
    for _ in range(steps):
        env.step(np.zeros(env.num_agents, dtype=np.int64))


def main() -> None:
    scenario = {item.name: item for item in M1_SCENARIOS}

    uncertainty_env = FreshnessUncertaintyMonitoringEnv(scenario["uncertainty_dominant"], seed=7)
    uncertainty_env.reset()
    uncertainty_choice = _target_by_uncertainty(uncertainty_env)
    assert uncertainty_choice == 0

    freshness_env = FreshnessUncertaintyMonitoringEnv(scenario["freshness_dominant"], seed=7)
    freshness_env.reset()
    _hold(freshness_env, 4)
    freshness_choice = _target_by_freshness(freshness_env)
    assert freshness_choice == 3

    conflict_env = FreshnessUncertaintyMonitoringEnv(scenario["conflict_band"], seed=7)
    conflict_env.reset()
    early_choice = _target_by_coupled_value(conflict_env)
    assert early_choice == 0
    # Measuring region 0 removes its initial epistemic advantage.  Holding for
    # three later steps lets the high-urgency region acquire a freshness risk.
    conflict_env.step(np.asarray((1, 0, 0), dtype=np.int64))
    _hold(conflict_env, 3)
    late_choice = _target_by_coupled_value(conflict_env)
    assert late_choice == 3
    assert early_choice != late_choice

    output = {
        "protocol": "M1-PRESSURE-BAND-RULE-AUDIT-V1",
        "verdict": "M1_PRESSURE_BANDS_PASS",
        "learning_started": False,
        "checks": {
            "uncertainty_dominant_selects_high_variance_region": uncertainty_choice == 0,
            "freshness_dominant_selects_high_urgency_age_region": freshness_choice == 3,
            "conflict_band_changes_public_value_preference_over_time": early_choice == 0 and late_choice == 3,
        },
        "choices": {
            "uncertainty_dominant": uncertainty_choice,
            "freshness_dominant": freshness_choice,
            "conflict_band_early": early_choice,
            "conflict_band_late": late_choice,
        },
        "interpretation": (
            "The audit proves only that public uncertainty and freshness signals "
            "induce distinct rule choices in frozen pressure bands. It does not "
            "prove learnability, method superiority, or a causal benefit of FUM-MAPPO."
        ),
    }
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
