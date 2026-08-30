from __future__ import annotations

import hashlib
import json
from pathlib import Path

from scripts.pr_drtp_b4_common import select_seed


ROOT = Path(__file__).resolve().parents[1]
FREEZE_PATH = ROOT / "configs" / "pr_drtp_b4_feasibility_freeze.json"
SELECTOR_PATH = ROOT / "configs" / "pr_drtp_b4_selector_tape.json"
OUTCOME_PATH = ROOT / "configs" / "pr_drtp_b4_outcome_tape.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_tapes_are_frozen_disjoint_and_match_hashes() -> None:
    freeze = json.loads(FREEZE_PATH.read_text())
    selector = json.loads(SELECTOR_PATH.read_text())
    outcome = json.loads(OUTCOME_PATH.read_text())
    assert digest(SELECTOR_PATH) == freeze["selector_tape_sha256"]
    assert digest(OUTCOME_PATH) == freeze["outcome_tape_sha256"]
    assert len(selector["episode_ids"]) == len(set(selector["episode_ids"])) == 50
    assert len(outcome["episode_ids"]) == len(set(outcome["episode_ids"])) == 100
    assert not set(selector["episode_ids"]) & set(outcome["episode_ids"])
    assert len(selector["conditions"]) == 7
    assert len(outcome["conditions"]) == 5


def test_populations_partition_fifteen_seeds_without_outcome_filtering() -> None:
    freeze = json.loads(FREEZE_PATH.read_text())
    expected = {row["seed"] for row in freeze["checkpoints"]}
    members = [seed for population in freeze["populations"] for seed in population["members"]]
    assert len(members) == 15
    assert len(set(members)) == 15
    assert set(members) == expected
    assert freeze["excluded_known_eligible_seeds"] == [3504, 3505]
    cohort_by_seed = {row["seed"]: row["cohort"] for row in freeze["checkpoints"]}
    for population in freeze["populations"]:
        assert len(population["members"]) == 3
        assert len({cohort_by_seed[seed] for seed in population["members"]}) == 3
        assert population["baseline_seed"] in population["members"]
    assert len({cohort_by_seed[p["baseline_seed"]] for p in freeze["populations"]}) == 5


def test_inventory_contains_exact_paired_checkpoint_hashes() -> None:
    freeze = json.loads(FREEZE_PATH.read_text())
    assert freeze["training_authorized"] is False
    assert len(freeze["source_archives"]) == 5
    assert len(freeze["checkpoints"]) == 15
    for row in freeze["checkpoints"]:
        assert len(row["utr_sha256"]) == 64
        assert len(row["drtp_sha256"]) == 64
        assert row["utr_sha256"] != row["drtp_sha256"]


def test_selector_is_fixed_maximin_then_mean_then_lowest_seed() -> None:
    scores = {
        1: {"eligible": True, "minimum_condition_J": 10.0, "mean_condition_J": 20.0},
        2: {"eligible": True, "minimum_condition_J": 11.0, "mean_condition_J": 12.0},
        3: {"eligible": True, "minimum_condition_J": 9.0, "mean_condition_J": 99.0},
    }
    assert select_seed([1, 2, 3], scores) == 2
    scores[1] = {"eligible": True, "minimum_condition_J": 11.0, "mean_condition_J": 13.0}
    assert select_seed([1, 2, 3], scores) == 1
    scores[2] = {"eligible": True, "minimum_condition_J": 11.0, "mean_condition_J": 13.0}
    assert select_seed([1, 2, 3], scores) == 1
    scores[1]["eligible"] = False
    assert select_seed([1, 2, 3], scores) == 2


def test_execution_path_contains_no_training_entrypoint() -> None:
    evaluation = (ROOT / "scripts" / "run_pr_drtp_b4_evaluation.py").read_text()
    launcher = (ROOT / "scripts" / "launch_pr_drtp_b4_autodl.sh").read_text()
    assert "train_ri_gmappo" not in evaluation
    assert "run_pr_drtp_b4_single" not in launcher
    assert "run_pr_drtp_b4_evaluation.py" in launcher
