from __future__ import annotations

import numpy as np

from envs.acfid_sequential_recovery_env import ACFIDSequentialConfig, ACFIDSequentialRecoveryEnv, all_sets_of_orders


def make_env():
    return ACFIDSequentialRecoveryEnv(ACFIDSequentialConfig(all_sets_of_orders(1, 2), seed=21))


def test_fault_signature_appears_only_after_detection() -> None:
    env = make_env(); env.reset(fault_set=frozenset({"sense_0", "relay_0"}))
    assert env._observation()["active_faults"].sum() == 0
    env.step(0); env.step(0)
    assert env._observation()["active_faults"].sum() == 2


def test_only_one_recovery_decision_is_accepted() -> None:
    env = make_env(); env.reset(fault_set=frozenset({"relay_0"})); env.step(0); env.step(0); env.step(2)
    selected = env.selected_action; env.step(4)
    assert env.selected_action == selected


def test_runtime_clone_reproduces_counterfactual_value() -> None:
    env = make_env(); env.reset(fault_set=frozenset({"sense_1", "act_1"})); env.step(0); env.step(0)
    state = env.runtime_state(); env.step(3); first = env.terminal_value
    env.restore_runtime_state(state); env.step(3)
    assert np.isclose(first, env.terminal_value)
