from __future__ import annotations

import numpy as np

from envs.acfid_compound_fault_env import ACFIDCompoundFaultEnv
from scripts.p8b_acfid_shared_interaction_gate import pair_features


def test_structured_features_are_shared_across_branch_renaming() -> None:
    env = ACFIDCompoundFaultEnv(); context = env.sample_context(np.random.default_rng(3))
    left = pair_features(frozenset({"sense_0", "relay_0"}), context, True)
    right = pair_features(frozenset({"sense_1", "relay_1"}), context, True)
    assert left.shape == right.shape
    assert left.size > pair_features(frozenset({"sense_0", "relay_0"}), context, False).size


def test_type_only_features_ignore_branch_relation() -> None:
    env = ACFIDCompoundFaultEnv(); context = env.sample_context(np.random.default_rng(4))
    same = pair_features(frozenset({"sense_0", "relay_0"}), context, False)
    cross = pair_features(frozenset({"sense_0", "relay_1"}), context, False)
    assert np.array_equal(same, cross)
