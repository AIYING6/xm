"""Zero-result deterministic tests for the v1.9 F2-R2 implementation.

The test creates only temporary byte fixtures. It does not import the simulator,
load a policy, instantiate a confirmatory episode, or read project results.
"""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import csv
import subprocess
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.simple_ri_gmappo import summarize_validation_event_records
from analyze_v1_9_f2_r2 import event_metric_vectors, hierarchical_paired_bootstrap, load_vectors
from check_v1_9_f2_r2_artifacts import validate
from f2_r2_common import (
    F1_PROTOCOL,
    F1_READY_STATUS,
    F2_EPISODE_IDS,
    METHOD_SPECS,
    build_f2_plan,
    sha256_file,
)


FAKE_F1_COMMIT = "1" * 40
FAKE_EVALUATOR_COMMIT = "2" * 40


def build_temporary_f1_root(root: Path) -> None:
    selections = []
    for method, _, _ in METHOD_SPECS:
        for seed in range(8):
            run_dir = root / f"{method}_seed{seed}"
            run_dir.mkdir(parents=True)
            checkpoint = run_dir / "actor_critic_update_0010.pt"
            checkpoint.write_bytes(f"fixture:{method}:{seed}".encode("utf-8"))
            selections.append({
                "method": method,
                "seed": seed,
                "selected_update": 10,
                "selected_checkpoint_path": checkpoint.name,
                "selected_checkpoint_sha256": sha256_file(checkpoint),
            })
    selection = {
        "status": F1_READY_STATUS,
        "protocol_version": F1_PROTOCOL,
        "source_commit": FAKE_F1_COMMIT,
        "confirmatory_heldout_accessed": False,
        "selections": selections,
    }
    artifact = {
        "status": "F1_R2_TRAINING_ARTIFACT_GATE_PASS",
        "source_commit": FAKE_F1_COMMIT,
        "confirmatory_heldout_accessed": False,
    }
    (root / "F1_R2_SELECTED_CHECKPOINTS_MANIFEST.json").write_text(json.dumps(selection), encoding="utf-8")
    (root / "F1_R2_TRAINING_ARTIFACT_GATE_MANIFEST.json").write_text(json.dumps(artifact), encoding="utf-8")


def test_plan_is_exact_24_by_300_paired_matrix() -> None:
    with tempfile.TemporaryDirectory(prefix="v1_9_f2_static_") as directory:
        root = Path(directory)
        build_temporary_f1_root(root)
        plan = build_f2_plan(root, FAKE_F1_COMMIT, FAKE_EVALUATOR_COMMIT)
    assert plan["confirmatory_heldout_accessed"] is False
    assert len(plan["checkpoint_plans"]) == 24
    assert all(row["paired_episode_ids"] == list(F2_EPISODE_IDS) for row in plan["checkpoint_plans"])
    assert len({row["checkpoint_sha256"] for row in plan["checkpoint_plans"]}) == 24


def test_hierarchical_paired_bootstrap_preserves_pairing() -> None:
    left = np.full((8, 300), 8.0)
    right = np.full((8, 300), 12.0)
    samples = hierarchical_paired_bootstrap(left, right, np.random.default_rng(7))
    assert samples.shape == (10_000,)
    assert np.all(samples == -4.0)


def test_terminal_outcome_contributes_restriction_horizon() -> None:
    vectors = event_metric_vectors([
        {
            "event_observed": 0, "event_time": -1, "terminal_failure_observed": 1,
            "terminal_failure_time": 20, "physical_event_observed": 0, "physical_event_time": -1,
        },
        {
            "event_observed": 1, "event_time": 50, "terminal_failure_observed": 0,
            "terminal_failure_time": -1, "physical_event_observed": 1, "physical_event_time": 30,
        },
    ])
    assert np.allclose(vectors["rmte80"], [80.0, 50.0])
    assert np.allclose(vectors["terminal_failure_incidence80"], [1.0, 0.0])
    assert np.allclose(vectors["active_not_established_probability80"], [0.0, 0.0])


def test_artifact_gate_recomputes_summary_from_raw_records() -> None:
    with tempfile.TemporaryDirectory(prefix="v1_9_f2_artifact_static_") as directory:
        root = Path(directory)
        f1_root = root / "f1"
        f1_root.mkdir()
        build_temporary_f1_root(f1_root)
        plan = build_f2_plan(f1_root, FAKE_F1_COMMIT, FAKE_EVALUATOR_COMMIT)
        plan["evaluation_workers"] = 4
        f2_root = root / "f2"
        f2_root.mkdir()
        preflight_path = f2_root / "F2_R2_LAUNCH_PREFLIGHT_MANIFEST.json"
        preflight_path.write_text(json.dumps(plan), encoding="utf-8")
        for item in plan["checkpoint_plans"]:
            run_dir = f2_root / f"{item['method']}_seed{item['training_seed']}"
            run_dir.mkdir()
            records = []
            for index, episode_seed in enumerate(F2_EPISODE_IDS):
                state = index % 3
                records.append({
                    "episode_seed": episode_seed,
                    "failure_onset_step": 40,
                    "event_observed": int(state == 0),
                    "first_stable_establishment_step": 60 if state == 0 else -1,
                    "event_time": 20 if state == 0 else -1,
                    "termination_reason": "success" if state == 0 else ("collision" if state == 1 else "timeout"),
                    "terminal_failure_observed": int(state == 1),
                    "terminal_failure_time": 30 if state == 1 else -1,
                    "terminal_step": 70,
                    "physical_event_observed": int(index % 2 == 0),
                    "first_stable_physical_engagement_step": 55 if index % 2 == 0 else -1,
                    "physical_event_time": 15 if index % 2 == 0 else -1,
                })
            records_path = run_dir / "episode_event_records.csv"
            with records_path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(records[0]))
                writer.writeheader()
                writer.writerows(records)
            summary = {
                "protocol_version": "V1_9_F2_R2_CONFIRMATORY",
                "f1_source_commit": FAKE_F1_COMMIT,
                "f2_evaluator_source_commit": FAKE_EVALUATOR_COMMIT,
                "method": item["method"],
                "training_seed": item["training_seed"],
                "selected_update": item["selected_update"],
                "checkpoint_sha256": item["checkpoint_sha256"],
                "episodes": 300,
                "episode_records_sha256": sha256_file(records_path),
                **{key[5:] if key.startswith("eval_") else key: value for key, value in summarize_validation_event_records(records).items()},
            }
            summary_path = run_dir / "summary.json"
            summary_path.write_text(json.dumps(summary), encoding="utf-8")
        subprocess.run([
            sys.executable, str(ROOT / "scripts" / "finalize_v1_9_f2_r2_execution.py"),
            "--out-root", str(f2_root),
            "--expected-f1-source-commit", FAKE_F1_COMMIT,
            "--expected-evaluator-source-commit", FAKE_EVALUATOR_COMMIT,
            "--f2-workers", "4",
        ], check=True)
        artifact = validate(f2_root, FAKE_F1_COMMIT, FAKE_EVALUATOR_COMMIT)
        assert artifact["status"] == "F2_R2_CONFIRMATORY_ARTIFACT_GATE_PASS"
        matrices = load_vectors(f2_root)
        assert matrices["pcrf_r2:rmte80"].shape == (8, 300)


def main() -> None:
    tests = [
        test_plan_is_exact_24_by_300_paired_matrix,
        test_hierarchical_paired_bootstrap_preserves_pairing,
        test_terminal_outcome_contributes_restriction_horizon,
        test_artifact_gate_recomputes_summary_from_raw_records,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("F2_R2_STATIC_TEST_REPORT: PASS (4 tests; no confirmatory access)")


if __name__ == "__main__":
    main()
