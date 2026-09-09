from __future__ import annotations

from scripts.audit_epistemic_commitment_p1g_smoke import run_p1g_audit
from scripts.run_epistemic_commitment_p1g_smoke import (
    CommitmentSmokeRunner,
    METHOD_CANDIDATE,
    METHOD_RECURRENT,
)


def test_both_methods_complete_one_finite_local_update() -> None:
    for method in (METHOD_CANDIDATE, METHOD_RECURRENT):
        metrics = CommitmentSmokeRunner(method, 98101, batch_size=3).update()
        assert metrics["episodes"] == 3
        assert metrics["actor_loss"] == metrics["actor_loss"]
        assert metrics["critic_loss"] == metrics["critic_loss"]


def test_p1g_resume_and_logging_audit_passes() -> None:
    report = run_p1g_audit()
    assert report["verdict"] == "P1G_LOCAL_OPTIMIZER_AND_RESUME_SMOKE_PASS"
    assert all(report["checks"].values())
    assert report["scientific_evidence"] is False
