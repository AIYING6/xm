from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_b1_lite_is_explicitly_zero_environment() -> None:
    source = (ROOT / "scripts" / "aggregate_drtp_b1_update_sensitivity_lite.py").read_text(encoding="utf-8")
    assert "environment_episodes_run_by_this_analysis\": 0" in source
    assert "run_drtp_sg_development_evaluation" not in source
    assert "evaluate_cell" not in source


def test_b1_lite_cannot_authorize_an_algorithm() -> None:
    source = (ROOT / "scripts" / "aggregate_drtp_b1_update_sensitivity_lite.py").read_text(encoding="utf-8")
    assert '"mechanism_declared": False' in source
    assert '"algorithm_modification_authorized": False' in source
