from __future__ import annotations

import json
from pathlib import Path

from scripts.audit_active_diagnosis_identifiability_p1 import run_audit


ROOT = Path(__file__).resolve().parents[1]


def test_balanced_prior_has_nontrivial_probe_value() -> None:
    config = json.loads(
        (ROOT / "configs" / "active_diagnosis_p1_counterexample.json").read_text(
            encoding="utf-8"
        )
    )
    report = run_audit(config)
    assert report["verdict"] == "P1_IDENTIFIABILITY_COUNTEREXAMPLE_PASS"
    assert report["balanced_prior"]["probe_gain"] > 0.0
    assert report["balanced_prior"]["action_after_ack"] == "recover_link"
    assert report["balanced_prior"]["action_after_silence"] == "degrade_task"


def test_probe_is_not_a_dominant_action() -> None:
    config = json.loads(
        (ROOT / "configs" / "active_diagnosis_p1_counterexample.json").read_text(
            encoding="utf-8"
        )
    )
    report = run_audit(config)
    assert any(item["probe_gain"] < 0.0 for item in report["extreme_priors"])
