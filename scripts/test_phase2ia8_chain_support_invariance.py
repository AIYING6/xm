"""P0 tests for explicit nonterminal chain-support instrumentation."""
from __future__ import annotations

import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from envs.uav_intercept_3d_env import UAVIntercept3DConfig, UAVIntercept3DEnv


def rollout(with_check: bool) -> list[tuple[float, float, float, float]]:
    env = UAVIntercept3DEnv(UAVIntercept3DConfig(seed=812, target_policy="straight", communication_dropout_prob=.30,
        message_delay_steps=2, strict_target_sensing=True, agent_target_info_bottleneck=True))
    env.reset()
    rows = []
    actions = np.asarray([13, 13, 13], dtype=np.int64)
    while not env.done:
        prior_hold = env.attack_hold
        _, _, _, reward, done, info = env.step(actions)
        support = float(info["chain_support_t"])
        expected_hold = prior_hold + 1 if support > .5 else 0
        if with_check:
            assert env.attack_hold == expected_hold, (prior_hold, support, env.attack_hold)
            assert info["chain_closed"] == float(env.attack_hold >= env.config.attack_hold_steps)
        rows.append((float(np.sum(reward)), float(done[0, 0]), support, float(info["chain_closed"])))
    return rows


def main() -> None:
    first = rollout(True)
    second = rollout(True)
    # The instrumentation is a pure info field: deterministic rollout remains
    # exactly identical on repeated execution with the same seed/actions.
    assert first == second
    print("PHASE2IA8_CHAIN_SUPPORT_P0_TEST=PASS")


if __name__ == "__main__":
    main()
