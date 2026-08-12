"""Non-performance unit checks for the Phase 2IA5 E0 executor."""
from __future__ import annotations

import tempfile
from pathlib import Path

from run_phase2ia5_e0_eligibility_validation import ARMS, SEEDS, episode_id, eligibility_trigger_step


def main() -> None:
    assert tuple(ARMS) == ("full_gate", "no_role_gate")
    assert SEEDS == (101, 202, 303)
    assert episode_id(101, 0) == 1_520_000
    assert episode_id(303, 99) == 3_540_099
    assert eligibility_trigger_step([False, True, True, True]) is None
    assert eligibility_trigger_step([True, True, True, True]) == 4
    assert eligibility_trigger_step([False, True, True, True, True]) == 5
    assert eligibility_trigger_step([False] * 216 + [True] * 4) == 220
    try:
        eligibility_trigger_step([True] * 5, hold_steps=3)
    except ValueError:
        pass
    else:
        raise AssertionError("hold length must be fixed at four")
    # Integration-level timing check for the existing environment failure
    # mechanism.  No policy action, performance field, or checkpoint is used.
    from envs.uav_intercept_3d_env import UAVIntercept3DConfig, UAVIntercept3DEnv
    env = UAVIntercept3DEnv(UAVIntercept3DConfig(seed=17, failed_blue_agent=-1, node_failure_duration_steps=0))
    env.config.failed_blue_agent = 1
    env.config.node_failure_start_step = 12
    env.config.node_failure_duration_steps = 80
    for step in (11, 92):
        env.step_count = step
        assert not env._is_comm_failed(1)
    for step in (12, 91):
        env.step_count = step
        assert env._is_comm_failed(1)
    with tempfile.TemporaryDirectory() as tmp:
        assert not (Path(tmp) / "results").exists()
    print("PHASE2IA5_E0_EXECUTOR_UNIT_TEST=PASS")


if __name__ == "__main__":
    main()
