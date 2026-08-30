from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs" / "drtp_b5_cross_cohort_atlas_freeze.json"
SCRIPT = ROOT / "scripts" / "build_drtp_b5_cross_cohort_atlas.py"


def load_module():
    spec = importlib.util.spec_from_file_location("drtp_b5_atlas", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_b5_freeze_closes_patch_search_and_protects_mainline_a() -> None:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    assert config["decision"] == "B5_INSTRUMENTATION_ONLY_GO"
    assert config["algorithm_modification_authorized"] is False
    assert config["training_authorized"] is False
    assert config["mainline_a_modified"] is False
    assert config["independent_unit"] == "training_seed"


def test_observational_contract_has_falsifiable_controls() -> None:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    cohort = config["observational_cohort"]
    assert cohort["arms"] == ["utr_sg", "drtp_sg"]
    assert len(cohort["provisional_seeds"]) == 5
    assert cohort["ceiling_env_steps"] == 1000192
    assert cohort["milestones_env_steps"][-1] == cohort["ceiling_env_steps"]
    assert len(cohort["mechanism_go"]) >= 6
    assert "close B-line" in cohort["mechanism_no_go"]


def test_credit_assignment_is_unobserved_not_claimed() -> None:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    top = min(config["candidate_hypotheses"], key=lambda row: row["rank"])
    assert top["name"] == "failure_group_conditioned_credit_assignment"
    assert top["status"] == "UNOBSERVED_ACTIONABLE_HYPOTHESIS"
    for experiment in config["experiments"]:
        assert experiment["decision"]
        assert len(experiment["sha256"]) == 64


def test_dispersion_uses_seed_level_values() -> None:
    module = load_module()
    stats = module.dispersion([1.0, 2.0, 5.0])
    assert stats["mean"] == 8.0 / 3.0
    assert stats["minimum"] == 1.0
    assert stats["maximum"] == 5.0
    assert stats["range"] == 4.0
    assert stats["sample_sd"] > 0
