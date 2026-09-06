from __future__ import annotations

import json
import csv
from pathlib import Path

from scripts.aggregate_drtp_stabilization_confirmation import write_csv
from scripts.create_drtp_stabilization_confirmatory_tape import payload
from scripts.drtp_stabilization_confirmation_contracts import cohort_spec
from scripts.run_drtp_stabilization_confirmatory_single import ARMS, SEEDS, STEPS, UPDATES, training_config


def test_confirmation_freeze_is_a_single_final_method_with_fresh_seeds() -> None:
    freeze = json.loads(open("configs/drtp_stabilization_final_freeze.json", encoding="utf-8").read())
    assert freeze["status"] == "V1_STRONG_FREEZE_CANDIDATE"
    assert freeze["final_method"]["sampler_mode"] == "anchored_egtr"
    assert freeze["final_method"]["anchor_alpha"] == 0.75
    assert freeze["frozen_training"]["seeds"] == list(SEEDS)
    assert set(freeze["frozen_training"]["arms"]) == set(ARMS)
    assert freeze["frozen_training"]["updates"] == UPDATES
    assert freeze["frozen_training"]["environment_steps_per_trajectory"] == STEPS
    assert set(SEEDS).isdisjoint({76011, 76012, 76013, 71011, 71012, 71013, 71014, 71015, 71021, 71022, 71023, 71024, 71025})


def test_confirmation_arms_are_matched_except_sampler() -> None:
    shared = None
    for arm, (mode, alpha) in ARMS.items():
        cfg = training_config(arm, SEEDS[0], "unused-output")
        assert cfg.drtp_sampler_mode == mode
        assert cfg.drtp_sampler_anchor_alpha == (1.0 if alpha is None else alpha)
        assert cfg.evaluation_enabled is False
        current = dict(cfg.__dict__)
        for key in ("drtp_sampler_mode", "drtp_sampler_anchor_alpha", "seed", "drtp_sampler_seed", "out_dir", "device"):
            current.pop(key)
        if shared is None:
            shared = current
        else:
            assert current == shared


def test_confirmation_tape_is_fresh_and_training_inaccessible() -> None:
    tape = payload()
    assert tape["protocol"] == "DRTP-STABILIZATION-CONFIRMATORY-TAPE-V1"
    assert tape["training_access"] == "forbidden"
    assert tape["confirmatory"] is True
    assert tape["episode_ids"] == list(range(780000, 780100))
    assert [row["name"] for row in tape["conditions"]] == ["nominal", "F0", "TE", "TL", "DS", "DL", "CP"]


def test_confirmation_launcher_has_no_algorithm_revision_path() -> None:
    launcher = open("scripts/launch_drtp_stabilization_confirmation_autodl.sh", encoding="utf-8").read()
    assert "run_drtp_stabilization_confirmatory_evaluation.py" in launcher
    assert "aggregate_drtp_stabilization_confirmation.py" in launcher
    assert "automatic_algorithm_revision\":false" in launcher
    assert "launch_6uav" not in launcher.lower()


def test_independent_replication_is_frozen_before_cohort_a_results() -> None:
    a, b = cohort_spec("A"), cohort_spec("B")
    assert a["freeze"]["final_method"] == b["freeze"]["final_method"]
    assert set(a["seeds"]).isdisjoint(b["seeds"])
    assert b["seeds"] == (78021, 78022, 78023, 78024, 78025)
    tape = payload("B")
    assert tape["protocol"] == "DRTP-STABILIZATION-INDEPENDENT-REPLICATION-TAPE-V1"
    assert tape["episode_ids"] == list(range(781000, 781100))
    assert tape["training_access"] == "forbidden"


def test_confirmation_csv_accepts_final_sampler_telemetry_columns(tmp_path: Path) -> None:
    target = tmp_path / "endpoints.csv"
    write_csv(target, [{"method": "utr_sg", "J_perturbed": 1.0}, {"method": "final", "J_perturbed": 2.0, "sampler_adapted_updates": 10}])
    with target.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[1]["sampler_adapted_updates"] == "10"
