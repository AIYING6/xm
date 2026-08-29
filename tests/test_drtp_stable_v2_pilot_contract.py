"""Rollout-free contract and aggregate-gate tests for the Stable-v2 pilot."""
from __future__ import annotations

import csv
import json
from pathlib import Path
import subprocess
import sys

from scripts import run_drtp_stable_v2_pilot_single as pilot
from scripts.aggregate_drtp_stable_v2_pilot import catastrophic, retention_ratio


ROOT = Path(__file__).resolve().parents[1]
ARMS = ("utr_sg", "drtp_sg", "drtp_klr_sg")
SEEDS = (3101, 3102, 3103)
CONDITIONS = ("nominal", "F0_44_80", "T28_28_80", "D120_44_120", "C28_120")


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def fixture(root: Path, *, active_guard: bool) -> Path:
    gains = {
        "utr_sg": {3101: 0.0, 3102: 0.0, 3103: 0.0},
        "drtp_sg": {3101: 30.0, 3102: -20.0, 3103: 10.0},
        "drtp_klr_sg": {3101: 25.0, 3102: 0.0, 3103: 15.0},
    }
    summary = []
    for arm in ARMS:
        for seed in SEEDS:
            for condition in CONDITIONS:
                summary.append({
                    "method": arm,
                    "train_seed": seed,
                    "condition": condition,
                    "J": 100.0 + gains[arm][seed],
                    "collision": 0.01,
                    "timeout": 0.20,
                    "constraint_violation": 0.0,
                    "failure_exposed": 1.0,
                })
    evaluation = root / "evaluations" / "final_05m"
    write_csv(evaluation / "per_seed_condition_summary.csv", summary)
    write_csv(evaluation / "raw_episode_metrics.csv", [{"row": index} for index in range(4500)])
    source_runs = [
        {
            "status": "completed", "updates": 1953, "environment_steps": 499968,
            "parameter_count": 116728, "early_stopping": False,
            "checkpoint_promotion": False, "seed_replacement": False,
            "tape_hash": "25ff4eb5764cd2d590fba719a9c6c43b290ee3466a63075fd7e7184b049c4859",
        }
        for _ in range(9)
    ]
    (evaluation / "evaluation_manifest.json").write_text(json.dumps({
        "status": "completed", "raw_rows": 4500,
        "source_runs": source_runs,
    }), encoding="utf-8")
    telemetry_fields = [
        "policy_guard_triggered", "policy_steps_attempted", "policy_steps_accepted",
        "policy_kl_attempted_max", "policy_kl_threshold",
        "actor_optimizer_state_restored", "critic_step_retained_after_actor_rollback",
    ]
    for seed in SEEDS:
        rows = []
        for update in range(1, 1954):
            trigger = int(active_guard and seed == 3101 and update == 100)
            rows.append(dict(zip(telemetry_fields, [
                trigger, 1, 1 - trigger, 0.03 if trigger else 0.001, 0.02, trigger, trigger,
            ])))
        write_csv(root / "runs" / "drtp_klr_sg" / f"seed{seed}" / "train_log.csv", rows)
    audit = root / "D1_TECHNICAL_AUDIT.json"
    audit.write_text(json.dumps({"status": "D1_TECHNICAL_PASS"}), encoding="utf-8")
    return audit


def run_gate(root: Path, audit: Path) -> dict:
    completed = subprocess.run(
        [
            sys.executable, "scripts/aggregate_drtp_stable_v2_pilot.py",
            "--output-root", str(root), "--technical-audit", str(audit), "--execute",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "PILOT_" in completed.stdout
    return json.loads((root / "diagnostics" / "stable_v2_pilot_gate" / "PILOT_GATE_DECISION.json").read_text())


def test_pilot_configs_are_frozen_without_creating_environment(tmp_path):
    assert pilot.SEEDS == SEEDS
    assert pilot.UPDATES * pilot.NUM_ENVS * pilot.ROLLOUT_STEPS == 499968
    for arm, expected in pilot.ARMS.items():
        cfg = pilot.training_config(arm, 3101, tmp_path / "unused")
        assert cfg.drtp_sampler_mode == expected["sampler"]
        assert cfg.policy_update_guard_mode == expected["guard"]
        assert cfg.target_kl == expected["target_kl"]
        assert cfg.evaluation_enabled is False


def test_gate_accepts_joint_return_downside_reliability_and_active_guard(tmp_path):
    audit = fixture(tmp_path, active_guard=True)
    decision = run_gate(tmp_path, audit)
    assert decision["decision"] == "PILOT_GO_SIGNAL"
    assert all(decision["criteria"].values())


def test_gate_rejects_inactive_guard_even_when_scores_look_stable(tmp_path):
    audit = fixture(tmp_path, active_guard=False)
    decision = run_gate(tmp_path, audit)
    assert decision["decision"] == "PILOT_NO_GO"
    assert decision["criteria"]["mechanism_activity"] is False
    assert "mechanism_activity" in decision["no_go_reasons"]


def test_catastrophic_retention_preserves_positive_reference_definition():
    assert retention_ratio(70.0, 100.0, 7.0) == 0.70
    assert retention_ratio(85.0, 100.0, 7.0) == 0.85


def test_catastrophic_retention_is_signed_safe_for_nonpositive_utr():
    assert retention_ratio(-20.0, -20.0, 7.0) == 1.0
    assert retention_ratio(-10.0, -20.0, 7.0) == 1.5
    assert retention_ratio(-30.0, -20.0, 7.0) == 0.5
    assert retention_ratio(-7.0, 0.0, 7.0) == 0.0
    utr = {"J_F0": -20.0, "J_pert_worst": -20.0, "timeout": 0.2}
    candidate = {"J_F0": -30.0, "J_pert_worst": -30.0, "timeout": 0.2}
    assert catastrophic(candidate, utr, 7.0)
