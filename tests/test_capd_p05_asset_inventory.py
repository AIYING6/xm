import json
from pathlib import Path

from scripts.audit_capd_p05_asset_inventory import audit


def make_run(root: Path, arm: str, seed: int) -> None:
    run = root / "results" / "development" / "egtr_double_cohort_simultaneous" / "runs" / arm / f"seed{seed}"
    run.mkdir(parents=True)
    (run / "actor_critic_latest.pt").write_bytes(f"{arm}-{seed}".encode())
    (run / "run_manifest.json").write_text(json.dumps({"arm": arm, "seed": seed}), encoding="utf-8")


def test_missing_assets_are_blocked_not_no_go(tmp_path: Path) -> None:
    result = audit(tmp_path / "empty", tmp_path / "out")
    assert result["verdict"] == "CAPD_P05_BLOCKED_ASSETS_NOT_LOCAL"
    assert result["complete_teacher_runs"] == 0
    assert result["checkpoint_loading_performed"] is False
    assert result["evaluation_started"] is False


def test_all_assets_enable_signal_audit_only(tmp_path: Path) -> None:
    source = tmp_path / "source"
    for arm in ("utr_sg", "egtr_sg"):
        for seed in (71011, 71012, 71013, 71014, 71015, 71021, 71022, 71023, 71024, 71025):
            make_run(source, arm, seed)
    result = audit(source, tmp_path / "out")
    assert result["verdict"] == "CAPD_P05_ASSETS_READY_FOR_SIGNAL_AUDIT"
    assert result["complete_teacher_runs"] == 20
    assert result["student_training_started"] is False
