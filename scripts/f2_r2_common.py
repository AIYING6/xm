"""Frozen, environment-free constants and manifest checks for v1.9 F2-R2.

This module intentionally does not import the simulator, policy, or trainer.
It can therefore be used to prepare and verify an F2 launch plan without
opening the untouched confirmatory episode population.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


F1_PROTOCOL = "V1_9_F1_R2_FORMAL_TRAINING"
F2_PROTOCOL = "V1_9_F2_R2_CONFIRMATORY"
F1_READY_STATUS = "F1_R2_FORMAL_TRAINING_COMPLETE__CHECKPOINTS_FROZEN__READY_FOR_F2_AUTHORIZATION"
F2_EPISODE_BASE_SEED = 510_000
F2_EPISODES = 300
F2_EPISODE_IDS = tuple(range(F2_EPISODE_BASE_SEED, F2_EPISODE_BASE_SEED + F2_EPISODES))
FORMAL_SEEDS = tuple(range(8))
METHOD_SPECS = (
    ("pcrf_r2", "pcrf_r2", 128),
    ("single_r2", "single_r2", 147),
    ("matched_nongraph_r2", "matched_nongraph_r2", 152),
)
PRIMARY_COMPARATOR = "single_r2"
SECONDARY_COMPARATOR = "matched_nongraph_r2"
PRIMARY_SESOI_DELTA_RMTE80 = -4.0
BOOTSTRAP_RESAMPLES = 10_000
BOOTSTRAP_SEED = 190_802


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def stable_json_sha256(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def write_new_json(path: Path, value: dict) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite immutable output: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")


def fail(message: str) -> None:
    raise RuntimeError(f"F2_R2_PREFLIGHT_FAILED: {message}")


def _read_json(path: Path) -> dict:
    if not path.exists():
        fail(f"missing required manifest: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON manifest {path}: {exc}")
    raise AssertionError("unreachable")


def build_f2_plan(f1_root: Path, expected_f1_source_commit: str, evaluator_source_commit: str) -> dict:
    """Verify F1-selected checkpoint identity without opening F2 episodes."""
    f1_root = f1_root.resolve()
    selection_path = f1_root / "F1_R2_SELECTED_CHECKPOINTS_MANIFEST.json"
    artifact_path = f1_root / "F1_R2_TRAINING_ARTIFACT_GATE_MANIFEST.json"
    selection = _read_json(selection_path)
    artifact = _read_json(artifact_path)
    if selection.get("status") != F1_READY_STATUS:
        fail("F1 selection manifest is not frozen/ready for F2")
    if selection.get("protocol_version") != F1_PROTOCOL:
        fail("F1 selection manifest protocol mismatch")
    if selection.get("source_commit") != expected_f1_source_commit:
        fail("F1 selection manifest source commit mismatch")
    if selection.get("confirmatory_heldout_accessed") is not False:
        fail("F1 manifest does not attest that F2 was untouched")
    if artifact.get("status") != "F1_R2_TRAINING_ARTIFACT_GATE_PASS":
        fail("F1 training artifact gate did not pass")
    if artifact.get("source_commit") != expected_f1_source_commit:
        fail("F1 artifact-gate source commit mismatch")
    if artifact.get("confirmatory_heldout_accessed") is not False:
        fail("F1 artifact gate does not attest that F2 was untouched")

    expected = {(method, seed) for method, _, _ in METHOD_SPECS for seed in FORMAL_SEEDS}
    selections = selection.get("selections", [])
    observed = {(str(row.get("method")), int(row.get("seed", -1))) for row in selections}
    if len(selections) != len(expected) or observed != expected:
        fail("F1 selection matrix is not exactly 3 methods x 8 formal seeds")

    specs = {method: (encoder, hidden_dim) for method, encoder, hidden_dim in METHOD_SPECS}
    plans = []
    for method, _, _ in METHOD_SPECS:
        for seed in FORMAL_SEEDS:
            row = next(item for item in selections if item["method"] == method and int(item["seed"]) == seed)
            checkpoint_relative = Path(f"{method}_seed{seed}") / str(row["selected_checkpoint_path"])
            checkpoint = f1_root / checkpoint_relative
            if not checkpoint.exists():
                fail(f"missing selected checkpoint for {method}/seed{seed}: {checkpoint}")
            actual_hash = sha256_file(checkpoint)
            if actual_hash != row.get("selected_checkpoint_sha256"):
                fail(f"selected checkpoint SHA256 mismatch for {method}/seed{seed}")
            encoder, hidden_dim = specs[method]
            plans.append({
                "method": method,
                "training_seed": seed,
                "encoder": encoder,
                "hidden_dim": hidden_dim,
                "selected_update": int(row["selected_update"]),
                "checkpoint_relative_path": checkpoint_relative.as_posix(),
                "checkpoint_sha256": actual_hash,
                "paired_episode_ids": list(F2_EPISODE_IDS),
            })

    return {
        "status": "F2_R2_LAUNCH_PREFLIGHT_PASS__CONFIRMATORY_NOT_YET_ACCESSED",
        "protocol_version": F2_PROTOCOL,
        "f1_protocol_version": F1_PROTOCOL,
        "f1_source_commit": expected_f1_source_commit,
        "f2_evaluator_source_commit": evaluator_source_commit,
        "f1_selection_manifest_sha256": sha256_file(selection_path),
        "f1_artifact_gate_manifest_sha256": sha256_file(artifact_path),
        "confirmatory_heldout_accessed": False,
        "episodes_per_checkpoint": F2_EPISODES,
        "episode_seed_base": F2_EPISODE_BASE_SEED,
        "episode_seed_list_sha256": stable_json_sha256(list(F2_EPISODE_IDS)),
        "primary_comparator": PRIMARY_COMPARATOR,
        "primary_endpoint": "delta_rmte80_pcrf_minus_single",
        "primary_sesoi_delta_rmte80": PRIMARY_SESOI_DELTA_RMTE80,
        "bootstrap": {
            "hierarchy": "paired_training_seed_then_matched_episode",
            "resamples": BOOTSTRAP_RESAMPLES,
            "seed": BOOTSTRAP_SEED,
        },
        "checkpoint_plans": plans,
    }
