from __future__ import annotations

import numpy as np

from envs.acfid_compound_fault_env import ACTIONS, ACFIDCompoundFaultEnv


def test_counterfactual_evaluation_is_deterministic_with_common_noise() -> None:
    env = ACFIDCompoundFaultEnv(); rng = np.random.default_rng(7)
    context = env.sample_context(rng); noise = rng.lognormal(0.0, 0.05, size=(16, 2))
    faults = frozenset({"sense_0", "relay_0"})
    assert env.q_values(context, faults, noise) == env.q_values(context, faults, noise)


def test_all_recovery_actions_are_finite() -> None:
    env = ACFIDCompoundFaultEnv(); rng = np.random.default_rng(8)
    context = env.sample_context(rng); noise = np.ones((8, 2))
    values = env.q_values(context, frozenset({"relay_0", "act_1"}), noise)
    assert set(values) == set(ACTIONS)
    assert all(np.isfinite(value) for value in values.values())


def test_vectorized_q_matches_scalar_rollouts() -> None:
    env = ACFIDCompoundFaultEnv(); rng = np.random.default_rng(9)
    context = env.sample_context(rng); noise = rng.lognormal(0.0, 0.05, size=(12, 2))
    faults = frozenset({"sense_1", "act_1"})
    vectorized = env.q_values(context, faults, noise)
    scalar = {action: float(np.mean([env.value(context, faults, action, row) for row in noise])) for action in ACTIONS}
    assert all(np.isclose(vectorized[action], scalar[action]) for action in ACTIONS)


def test_dependency_distance_separates_branches() -> None:
    env = ACFIDCompoundFaultEnv()
    assert env.dependency_distance("sense_0", "act_0") < env.dependency_distance("sense_0", "act_1")
