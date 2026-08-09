"""Synthetic artifact test for the F1-R2 gate and frozen selector."""
from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.select_v1_9_f1_r2_checkpoints import (  # noqa: E402
    FORMAL_SEEDS,
    METHODS,
    PROTOCOL,
    REQUIRED_RECORDS,
    REQUIRED_SUMMARY,
    UPDATES,
    VALIDATION_BASE_SEED,
    VALIDATION_EPISODES,
)

COMMIT = "f1-static-pipeline-test"


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def write_run(root: Path, method: str, encoder: str, seed: int) -> None:
    run = root / f"{method}_seed{seed}"
    run.mkdir()
    with (run / "train_log.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["update", "loss", "policy_loss", "value_loss", "entropy", "grad_norm"])
        writer.writeheader()
        for update in range(1, 301):
            writer.writerow({"update": update, "loss": 0.0, "policy_loss": 0.0, "value_loss": 0.0, "entropy": 1.0, "grad_norm": 1.0})
    (run / "train.stderr.log").write_text("", encoding="utf-8")
    manifest = []
    prefix = "actor.pcrf_r2_graph." if encoder == "pcrf_r2" else "actor.r2_unified_graph."
    for update in UPDATES:
        snapshot = run / f"actor_critic_update_{update:04d}.pt"
        torch.save({"model_state": {f"{prefix}weight": torch.zeros(1)}}, snapshot)
        snapshot_hash = digest(snapshot)
        metadata = {
            "protocol_version": PROTOCOL, "git_commit": COMMIT, "method": method,
            "training_seed": seed, "update": update, "sha256": snapshot_hash,
        }
        (run / f"actor_critic_update_{update:04d}.metadata.json").write_text(json.dumps(metadata), encoding="utf-8")
        point = run / "validation" / f"update_{update:04d}"
        point.mkdir(parents=True)
        summary = {
            "protocol_version": PROTOCOL, "method": method, "training_seed": seed, "update": update,
            "validation_base_seed": VALIDATION_BASE_SEED, "episodes": VALIDATION_EPISODES, "snapshot_sha256": snapshot_hash,
            **{field: float(300 - update) for field in REQUIRED_SUMMARY},
        }
        summary_path = point / "summary.json"
        summary_path.write_text(json.dumps(summary), encoding="utf-8")
        records_path = point / "episode_event_records.csv"
        with records_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=sorted(REQUIRED_RECORDS))
            writer.writeheader()
            writer.writerow({field: 0 for field in REQUIRED_RECORDS})
        manifest.append({
            "protocol_version": PROTOCOL, "git_commit": COMMIT, "method": method, "training_seed": seed,
            "update": update, "snapshot_path": snapshot.name, "snapshot_sha256": snapshot_hash,
            "summary_path": str(summary_path.relative_to(run)), "summary_sha256": digest(summary_path),
            "episode_records_path": str(records_path.relative_to(run)), "episode_records_sha256": digest(records_path),
        })
    with (run / "snapshot_manifest.jsonl").open("w", encoding="utf-8") as f:
        for row in manifest:
            f.write(json.dumps(row) + "\n")


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "runtime_manifest.json").write_text(
            json.dumps({"protocol_version": PROTOCOL, "cuda_available": True, "git_commit": COMMIT}), encoding="utf-8"
        )
        for method, encoder, _ in METHODS:
            for seed in FORMAL_SEEDS:
                write_run(root, method, encoder, seed)
        gate = root / "gate.json"
        selected = root / "selected.json"
        subprocess.run([sys.executable, "scripts/check_v1_9_f1_r2_artifacts.py", "--root", str(root), "--expected-source-commit", COMMIT, "--output", str(gate)], cwd=ROOT, check=True, capture_output=True, text=True)
        subprocess.run([sys.executable, "scripts/select_v1_9_f1_r2_checkpoints.py", "--root", str(root), "--expected-source-commit", COMMIT, "--output", str(selected)], cwd=ROOT, check=True, capture_output=True, text=True)
        assert json.loads(gate.read_text(encoding="utf-8"))["status"] == "F1_R2_TRAINING_ARTIFACT_GATE_PASS"
        selection = json.loads(selected.read_text(encoding="utf-8"))
        assert len(selection["selections"]) == 24
        assert {row["selected_update"] for row in selection["selections"]} == {300}
    print("F1_R2_STATIC_PIPELINE_TEST: PASS (24 synthetic formal runs)")


if __name__ == "__main__":
    main()
