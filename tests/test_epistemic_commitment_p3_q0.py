from __future__ import annotations

import numpy as np

from envs.epistemic_commitment_p3_env import (
    MODE_COMMIT,
    MODE_DEFER,
    MODE_FALLBACK,
    EpistemicCommitmentP3Env,
    P3CommunicationSpec,
)
from scripts.audit_epistemic_commitment_p3_q0 import audit


def _action(*modes: int) -> np.ndarray:
    value = np.zeros((3, 3), dtype=np.float32)
    value[:, 0] = modes
    return value


def test_q0_frozen_registry_passes_without_training() -> None:
    report = audit()
    assert report["verdict"] == "P3_Q0_PASS_TO_TINY_LEARNABILITY_PILOT"
    assert report["exact_check_registry"] is True
    assert all(report["checks"].values())
    assert report["training_started"] is False
    assert report["ppo_updates"] == 0


def test_hidden_delivery_truth_is_not_in_initial_actor_observation() -> None:
    delivered = EpistemicCommitmentP3Env(
        P3CommunicationSpec("delivered", "delivered", "current"), seed=20260909
    )
    lost = EpistemicCommitmentP3Env(
        P3CommunicationSpec("lost", "not_applicable", "current"), seed=20260909
    )
    delivered_obs, delivered_share, _ = delivered.reset()
    lost_obs, lost_share, _ = lost.reset()
    np.testing.assert_array_equal(delivered_obs, lost_obs)
    np.testing.assert_array_equal(delivered_share, lost_share)


def test_endpoints_are_separated_by_closed_loop_trajectory() -> None:
    nominal = P3CommunicationSpec("delivered", "delivered", "current")
    lost = P3CommunicationSpec("lost", "not_applicable", "current")
    commit = _action(MODE_COMMIT, MODE_COMMIT, MODE_COMMIT)
    unilateral = _action(MODE_COMMIT, MODE_DEFER, MODE_FALLBACK)
    fallback = _action(MODE_FALLBACK, MODE_FALLBACK, MODE_FALLBACK)

    success_env = EpistemicCommitmentP3Env(nominal)
    failure_env = EpistemicCommitmentP3Env(lost)
    recovery_env = EpistemicCommitmentP3Env(lost)
    for action in [_action(MODE_DEFER, MODE_DEFER, MODE_DEFER)] * 3 + [commit] * 5:
        *_, success = success_env.step(action)
    for _ in range(8):
        *_, failure = failure_env.step(unilateral)
    for action in [unilateral] * 3 + [fallback] * 5:
        *_, recovery = recovery_env.step(action)

    assert success["endpoint"] == "joint_task_success"
    assert failure["endpoint"] == "unsupported_corridor_entry"
    assert recovery["endpoint"] == "recovery_after_mismatch"
    assert success["final_pair_separation"] < failure["final_pair_separation"]


def test_state_restore_reproduces_future_outputs_exactly() -> None:
    spec = P3CommunicationSpec("delivered", "delivered", "current")
    action = _action(MODE_COMMIT, MODE_COMMIT, MODE_COMMIT)
    env = EpistemicCommitmentP3Env(spec)
    env.step(action)
    state = env.state_dict()
    expected = env.step(action)
    restored = EpistemicCommitmentP3Env(spec)
    restored.load_state_dict(state)
    actual = restored.step(action)
    np.testing.assert_array_equal(expected[0], actual[0])
    np.testing.assert_array_equal(expected[1], actual[1])
    np.testing.assert_array_equal(expected[3], actual[3])
    np.testing.assert_array_equal(expected[4], actual[4])
    assert expected[5] == actual[5]
