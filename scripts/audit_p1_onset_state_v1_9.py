"""Static P1 audit of whether the R2 evaluator controls the failure-onset state.

This is deliberately not a policy-performance experiment.  It records the
current evaluator's causal scope before any F1 run: reset-to-terminal
end-to-end evaluation, or a matched state intervention at failure onset.
"""
from __future__ import annotations

import inspect
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.simple_ri_gmappo import eval_policy  # noqa: E402
from envs.uav_intercept_3d_env import UAVIntercept3DConfig, UAVIntercept3DEnv  # noqa: E402


FORMAL_FAILURE_ONSET = 40
FORMAL_FAILURE_DURATION = 80


def test_formal_failure_window_is_known() -> None:
    cfg = UAVIntercept3DConfig(
        failed_blue_agent=1,
        node_failure_start_step=FORMAL_FAILURE_ONSET,
        node_failure_duration_steps=FORMAL_FAILURE_DURATION,
    )
    env = UAVIntercept3DEnv(cfg)
    env.step_count = FORMAL_FAILURE_ONSET - 1
    assert not env._is_comm_failed(1)
    env.step_count = FORMAL_FAILURE_ONSET
    assert env._is_comm_failed(1)
    env.step_count = FORMAL_FAILURE_ONSET + FORMAL_FAILURE_DURATION
    assert not env._is_comm_failed(1)


def test_current_evaluator_is_reset_to_terminal() -> None:
    source = inspect.getsource(eval_policy)
    parameters = inspect.signature(eval_policy).parameters
    assert "env = make_env(cfg, base_seed + ep, training=False)" in source
    assert "obs, share_obs, graph = env.reset()" in source
    assert "initial_state" not in parameters
    assert "onset_state" not in parameters
    assert "restore" not in source


def test_environment_exposes_no_state_restore_intervention() -> None:
    forbidden = {"set_state", "load_state", "restore_state", "snapshot_state"}
    public = set(dir(UAVIntercept3DEnv))
    assert forbidden.isdisjoint(public)


def main() -> None:
    tests = [
        test_formal_failure_window_is_known,
        test_current_evaluator_is_reset_to_terminal,
        test_environment_exposes_no_state_restore_intervention,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("P1_ONSET_STATE_AUDIT_V1_9: BLOCKED (current protocol is end-to-end only; no common-onset-state intervention exists)")


if __name__ == "__main__":
    main()
