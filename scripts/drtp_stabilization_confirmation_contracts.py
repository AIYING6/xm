"""Frozen cohort-specific contracts for final DRTP confirmation and replication."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARMS = {
    "utr_sg": ("utr", None),
    "drtp_sg": ("drtp", None),
    "egtr_sg": ("egtr", None),
    "global_anchored_egtr_a075_sg": ("anchored_egtr", 0.75),
}

_FILES = {
    "A": ROOT / "configs" / "drtp_stabilization_final_freeze.json",
    "B": ROOT / "configs" / "drtp_stabilization_independent_replication_freeze.json",
}


def cohort_names() -> tuple[str, ...]:
    return tuple(_FILES)


def cohort_spec(cohort: str) -> dict:
    if cohort not in _FILES:
        raise ValueError(f"unknown confirmation cohort: {cohort}")
    freeze_path = _FILES[cohort]
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    training = freeze["frozen_training"]
    evaluation = freeze["evaluation"]
    if freeze["final_method"]["anchor_alpha"] != 0.75:
        raise RuntimeError("confirmation contract changed final alpha")
    if tuple(training["arms"]) != tuple(ARMS):
        raise RuntimeError("confirmation contract changed comparison arms")
    return {
        "cohort": cohort,
        "freeze": freeze,
        "freeze_path": freeze_path,
        "seeds": tuple(training["seeds"]),
        "episode_ids": list(range(int(evaluation["episode_ids"][0]), int(evaluation["episode_ids"][1]) + 1)),
        "tape_protocol": evaluation["tape_protocol"],
        "training_protocol": "DRTP-STABILIZATION-FINAL-CONFIRMATION-10M-V1" if cohort == "A" else "DRTP-STABILIZATION-INDEPENDENT-REPLICATION-10M-V1",
        "evaluation_protocol": "DRTP-STABILIZATION-FINAL-CONFIRMATION-10M-EVALUATION-V1" if cohort == "A" else "DRTP-STABILIZATION-INDEPENDENT-REPLICATION-10M-EVALUATION-V1",
        "report_protocol": "DRTP-STABILIZATION-FINAL-CONFIRMATION-REPORT-V1" if cohort == "A" else "DRTP-STABILIZATION-INDEPENDENT-REPLICATION-REPORT-V1",
        "diagnostic_dir": "confirmation_final" if cohort == "A" else "independent_replication_final",
    }
