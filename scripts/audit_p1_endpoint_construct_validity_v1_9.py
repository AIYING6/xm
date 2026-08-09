"""Static P1 audit of what the repaired RMTE endpoint does and does not measure."""
from __future__ import annotations

import inspect
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.simple_ri_gmappo import eval_policy  # noqa: E402
from envs.uav_intercept_3d_env import UAVIntercept3DEnv  # noqa: E402


def test_establishment_is_a_four_step_operational_task_chain() -> None:
    source = inspect.getsource(UAVIntercept3DEnv.step)
    assert "self.attack_hold += 1" in source
    assert "self.attack_hold = 0" in source
    assert "chain_closed = self.attack_hold >= self.config.attack_hold_steps" in source
    assert "window > 0.5 and tracking > 0.0 and self._comm_has_chain_to_attacker()" in source


def test_event_record_is_exactly_post_onset_task_chain_establishment() -> None:
    source = inspect.getsource(eval_policy)
    assert "int(info.get(\"step\", 0)) >= cfg.node_failure_start_step" in source
    assert "float(info.get(\"chain_closed\", 0.0)) > 0.5" in source
    assert "post_failure_chain_step is None" in source
    assert "event_time = (post_failure_chain_step - onset)" in source


def test_environment_success_is_not_an_independent_interception_outcome() -> None:
    source = inspect.getsource(UAVIntercept3DEnv.step)
    assert "self.success = chain_closed and self.step_count >= self.config.min_success_step" in source
    assert "capture" not in source
    assert "intercept" not in source


def test_terminal_outcomes_are_separately_recorded() -> None:
    source = inspect.getsource(eval_policy)
    assert "terminal_failure_observed" in source
    assert "terminal_failure_time" in source
    assert "reason in {" in source
    assert '"collision"' in source and '"constraint_violation"' in source


def main() -> None:
    tests = [
        test_establishment_is_a_four_step_operational_task_chain,
        test_event_record_is_exactly_post_onset_task_chain_establishment,
        test_environment_success_is_not_an_independent_interception_outcome,
        test_terminal_outcomes_are_separately_recorded,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("P1_ENDPOINT_CONSTRUCT_VALIDITY_AUDIT_V1_9: BLOCKED (RMTE valid for task-chain establishment, not independently validated interception success)")


if __name__ == "__main__":
    main()
