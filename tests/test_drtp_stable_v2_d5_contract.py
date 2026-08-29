"""Rollout-free contract and frozen-gate tests for the D5 DRTP-KLB pilot."""
from __future__ import annotations

import csv
import json
from pathlib import Path
import subprocess
import sys

from scripts import run_drtp_stable_v2_d5_single as pilot


ROOT = Path(__file__).resolve().parents[1]
ARMS = ("utr_sg", "drtp_sg", "drtp_klb_sg")
SEEDS = (3201, 3202, 3203)
CONDITIONS = ("nominal", "F0_44_80", "T28_28_80", "D120_44_120", "C28_120")


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def fixture(root: Path, original: list[float], candidate: list[float], *, valid_telemetry: bool = True) -> Path:
    gains = {
        "utr_sg": dict(zip(SEEDS, [0.0, 0.0, 0.0])),
        "drtp_sg": dict(zip(SEEDS, original)),
        "drtp_klb_sg": dict(zip(SEEDS, candidate)),
    }
    summary = []
    for arm in ARMS:
        for seed in SEEDS:
            for condition in CONDITIONS:
                summary.append({
                    "method": arm, "train_seed": seed, "condition": condition,
                    "J": 100.0 + gains[arm][seed], "collision": 0.01, "timeout": 0.20,
                    "constraint_violation": 0.0, "failure_exposed": 1.0,
                })
    evaluation = root / "evaluations" / "final_05m"
    write_csv(evaluation / "per_seed_condition_summary.csv", summary)
    write_csv(evaluation / "raw_episode_metrics.csv", [{"row": index} for index in range(4500)])
    tape = json.loads((ROOT / "configs" / "drtp_stable_v2_d5_pilot_tape.json").read_text())
    source_runs = [
        {
            "status": "completed", "updates": 1953, "environment_steps": 499968,
            "parameter_count": 116728, "early_stopping": False, "checkpoint_promotion": False,
            "seed_replacement": False, "tape_hash": tape["tape_hash"],
        }
        for _ in range(9)
    ]
    (evaluation / "evaluation_manifest.json").write_text(json.dumps({
        "status": "completed", "raw_rows": 4500, "source_runs": source_runs,
    }), encoding="utf-8")
    fields = [
        "policy_guard_triggered", "policy_steps_attempted", "policy_steps_accepted",
        "policy_kl_post_step", "policy_kl_attempted_max", "policy_kl_threshold",
        "actor_attempted_update_l2", "actor_accepted_update_l2", "actor_projection_l2",
        "policy_backtrack_alpha", "policy_backtrack_iterations",
        "actor_optimizer_state_restored", "actor_optimizer_state_retained_after_projection",
        "critic_step_retained_after_policy_guard",
    ]
    for seed in SEEDS:
        rows = []
        for update in range(1, 1954):
            trigger = seed == 3201 and update == 100
            values = [
                int(trigger), 1, 1, 0.02 if trigger else 0.001, 0.03 if trigger else 0.001, 0.02,
                1.0, 0.7 if trigger else 1.0, 0.3 if trigger else 0.0,
                0.7 if trigger else 1.0, 24 if trigger else 0,
                0, int(trigger and valid_telemetry), int(trigger),
            ]
            rows.append(dict(zip(fields, values)))
        write_csv(root / "runs" / "drtp_klb_sg" / f"seed{seed}" / "train_log.csv", rows)
    audit = root / "D4_TECHNICAL_AUDIT.json"
    audit.write_text(json.dumps({"status": "D4_TECHNICAL_PASS"}), encoding="utf-8")
    return audit


def run_gate(root: Path, audit: Path) -> dict:
    subprocess.run([
        sys.executable, "scripts/aggregate_drtp_stable_v2_d5_pilot.py",
        "--output-root", str(root), "--technical-audit", str(audit), "--execute",
    ], cwd=ROOT, check=True, capture_output=True, text=True)
    return json.loads((root / "diagnostics" / "stable_v2_d5_pilot_gate" / "D5_PILOT_GATE_DECISION.json").read_text())


def test_d5_configs_are_frozen_without_creating_environment(tmp_path):
    assert pilot.SEEDS == SEEDS
    assert pilot.UPDATES * pilot.NUM_ENVS * pilot.ROLLOUT_STEPS == 499968
    for arm, expected in pilot.ARMS.items():
        cfg = pilot.training_config(arm, 3201, tmp_path / "unused")
        assert cfg.drtp_sampler_mode == expected["sampler"]
        assert cfg.policy_update_guard_mode == expected["guard"]
        assert cfg.target_kl == expected["target_kl"]
        assert cfg.evaluation_enabled is False


def test_d5_gate_accepts_joint_high_return_downside_and_reliability(tmp_path):
    audit = fixture(tmp_path, [30.0, -20.0, 10.0], [28.0, 10.0, 15.0])
    decision = run_gate(tmp_path, audit)
    assert decision["decision"] == "D5_PILOT_GO_SIGNAL"
    assert all(decision["criteria"].values())


def test_d5_gate_rejects_upper_tail_suppression(tmp_path):
    audit = fixture(tmp_path, [30.0, -20.0, 10.0], [10.0, 10.0, 15.0])
    decision = run_gate(tmp_path, audit)
    assert decision["decision"] == "D5_PILOT_NO_GO"
    assert decision["criteria"]["upper_tail_retention"] is False


def test_d5_gate_marks_unassessable_upper_tail_inconclusive(tmp_path):
    audit = fixture(tmp_path, [5.0, -5.0, 0.0], [4.0, 4.0, 4.0])
    decision = run_gate(tmp_path, audit)
    assert decision["decision"] == "D5_PILOT_INCONCLUSIVE_UPPER_TAIL"
    assert decision["criteria"]["upper_tail_assessable"] is False


def test_d5_gate_rejects_invalid_projection_telemetry(tmp_path):
    audit = fixture(tmp_path, [30.0, -20.0, 10.0], [28.0, 10.0, 15.0], valid_telemetry=False)
    decision = run_gate(tmp_path, audit)
    assert decision["decision"] == "D5_PILOT_NO_GO"
    assert decision["criteria"]["mechanism_activity_and_semantics"] is False
