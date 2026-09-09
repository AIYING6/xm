from __future__ import annotations

import numpy as np

from envs.epistemic_commitment_trainable_env import (
    ACTION_FALLBACK,
    EpistemicCommitmentEpisodeSpec,
    EpistemicCommitmentTrainableEnv,
    make_balanced_evaluation_tape,
)
from scripts.audit_epistemic_commitment_p1e_trainable_contract import run_p1e_audit


def test_standard_interface_and_private_receipt_boundary() -> None:
    delivered = EpistemicCommitmentTrainableEnv(
        11, EpistemicCommitmentEpisodeSpec(1, "middle", True)
    )
    lost = EpistemicCommitmentTrainableEnv(
        11, EpistemicCommitmentEpisodeSpec(1, "middle", False)
    )
    cue_d = delivered.reset()[0]
    cue_l = lost.reset()[0]
    assert cue_d.shape == (3, 39)
    assert np.array_equal(cue_d, cue_l)
    decision_d = delivered.step([ACTION_FALLBACK] * 3)[0]
    decision_l = lost.step([ACTION_FALLBACK] * 3)[0]
    assert np.array_equal(decision_d[0], decision_l[0])
    assert np.array_equal(decision_d[1], decision_l[1])
    assert not np.array_equal(decision_d[2], decision_l[2])


def test_balanced_tape_has_frozen_context_delivery_counts() -> None:
    tape = make_balanced_evaluation_tape()
    assert len(tape) == 300
    counts = {
        context: sum(spec.delivered for spec in tape if spec.context == context)
        for context in ("low", "middle", "high")
    }
    assert counts == {"low": 15, "middle": 45, "high": 85}


def test_p1e_contract_audit_passes_without_training() -> None:
    report = run_p1e_audit()
    assert report["verdict"] == "P1E_TRAINABLE_CONTRACT_AUDIT_PASS"
    assert all(report["checks"].values())
    assert report["training_started"] is False
