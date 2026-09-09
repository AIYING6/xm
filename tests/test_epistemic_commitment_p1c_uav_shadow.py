from __future__ import annotations

import numpy as np

from envs.epistemic_commitment_uav_shadow_env import (
    COMMIT,
    FALLBACK,
    CommitmentChoice,
    EpistemicCommitmentUAVShadowEnv,
)
from scripts.audit_epistemic_commitment_p1c_uav_shadow import run_p1c_gate


def test_delivery_is_private_and_sender_history_is_matched() -> None:
    delivered = EpistemicCommitmentUAVShadowEnv(True, 17).actor_observation()
    lost = EpistemicCommitmentUAVShadowEnv(False, 17).actor_observation()
    assert np.array_equal(delivered[0], lost[0])
    assert np.array_equal(delivered[1], lost[1])
    assert not np.array_equal(delivered[2], lost[2])


def test_bilateral_and_unilateral_commitments_have_distinct_safe_consequences() -> None:
    bilateral = EpistemicCommitmentUAVShadowEnv(True, 17).execute(
        CommitmentChoice(COMMIT, COMMIT)
    )
    unilateral = EpistemicCommitmentUAVShadowEnv(False, 17).execute(
        CommitmentChoice(COMMIT, FALLBACK)
    )
    assert bilateral["outcome"] == "bilateral_commitment"
    assert unilateral["outcome"] == "unilateral_commitment"
    assert bilateral["task_value"] > unilateral["task_value"]
    assert not bilateral["collision"] and not unilateral["collision"]
    assert not bilateral["constraint_violation"] and not unilateral["constraint_violation"]


def test_p1c_gate_passes_with_explicit_evidence_boundary() -> None:
    report = run_p1c_gate()
    assert report["verdict"] == "P1C_UAV_COMMITMENT_SEMANTIC_PASS"
    assert all(report["checks"].values())
    assert report["training_started"] is False
    assert report["ppo_updates"] == 0
