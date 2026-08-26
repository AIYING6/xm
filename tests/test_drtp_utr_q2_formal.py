from __future__ import annotations

import csv
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from create_drtp_utr_q2_formal_tape import CONDITIONS, SEEDS, frozen_manifest  # noqa: E402
from run_drtp_utr_q2_formal_single import ARMS, training_config  # noqa: E402


def test_formal_config_diff_is_sampler_only(tmp_path: Path) -> None:
    utr = training_config("utr_sg", SEEDS[0], tmp_path / "utr")
    drtp = training_config("drtp_sg", SEEDS[0], tmp_path / "drtp")
    ignored = {"drtp_sampler_mode", "seed", "drtp_sampler_seed", "out_dir"}
    utr_values = {key: value for key, value in utr.__dict__.items() if key not in ignored}
    drtp_values = {key: value for key, value in drtp.__dict__.items() if key not in ignored}
    assert utr_values == drtp_values
    assert utr.drtp_sampler_mode == "utr"
    assert drtp.drtp_sampler_mode == "drtp"


def test_frozen_formal_tape() -> None:
    tape = frozen_manifest()
    assert tape["episode_ids"] == list(range(490000, 490100))
    assert len(tape["conditions"]) == 12
    assert tape["canonical"] is False
    assert tape["paired_training_seeds"] == list(SEEDS)


def test_aggregation_contract_with_complete_synthetic_evidence(tmp_path: Path) -> None:
    result_root = tmp_path / "formal"
    eval_root = result_root / "evaluations" / "final_10m"
    eval_root.mkdir(parents=True)
    tape = frozen_manifest()
    (result_root / "formal_tape_manifest.json").write_text(
        json.dumps(tape, indent=2) + "\n", encoding="utf-8")
    (eval_root / "evaluation_manifest.json").write_text(json.dumps({
        "status": "completed", "tape_hash": tape["tape_hash"], "raw_rows": 12000,
    }) + "\n", encoding="utf-8")
    rows = []
    for arm in ARMS:
        for seed in SEEDS:
            for index, condition in enumerate(CONDITIONS):
                nominal = condition == "nominal"
                baseline = 100.0 if nominal else (80.0 if index == 1 else 70.0 + index)
                gain = 2.0 if nominal else 10.0
                rows.append({
                    "arm": arm, "seed": seed, "checkpoint_label": "10m",
                    "condition": condition, "J": baseline + (gain if arm == "drtp_sg" else 0.0),
                    "collision": .01, "timeout": .2, "constraint_violation": 0.0,
                    "failure_exposure": "nan" if nominal else 1.0,
                    "failure_exposure_all_scheduled": "nan" if nominal else 1.0,
                    "episode_length": 260, "risk_set_size": 0 if nominal else 100,
                    "survival_to_onset_fraction": "nan" if nominal else 1.0,
                    "failure_trigger_success_rate_risk_set": "nan" if nominal else 1.0,
                    "pretrigger_collision_count": 0,
                    "pretrigger_collision_rate": "nan" if nominal else 0.0,
                    "path_switch_count": 1.0, "direct_path_fraction": .5,
                    "relay_path_fraction": .1, "task_support_fraction": .5,
                    "legal_information_fraction": .8, "mean_cache_age": 10.0,
                    "traveled_distance": 1000.0, "control_effort": 20.0,
                })
    summary = eval_root / "per_seed_condition_summary.csv"
    with summary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    report = tmp_path / "report.md"
    subprocess.run([
        sys.executable, str(ROOT / "scripts" / "aggregate_drtp_utr_q2_formal.py"),
        "--results-root", str(result_root), "--report-path", str(report),
    ], cwd=ROOT, check=True, capture_output=True, text=True)
    decision = json.loads((eval_root / "DRTP_UTR_Q2_FORMAL_DECISION.json").read_text(encoding="utf-8"))
    assert decision["verdict"] == "FORMAL_CONFIRMATION_PASS_SEED_SENSITIVE"
    assert decision["gates"]["complete_12000_records"] is True
    assert decision["gates"]["risk_set_trigger_validity"] is True
    assert report.exists()
