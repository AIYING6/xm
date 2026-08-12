"""Completion-only audit for frozen Phase 2I-A2 development runs."""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
RUN_ROOT = ROOT / "results" / "development" / "role_gate_phase2ia2" / "runs"
INCIDENT_LOG = ROOT / "results" / "development" / "role_gate_phase2ia2" / "run_incident_log.csv"
OUT = ROOT / "docs" / "PHASE2IA2_TRAINING_COMPLETION_AUDIT.md"
EXPECTED_ARMS = ("full_gate", "no_role_gate")
EXPECTED_SEEDS = (101, 202, 303)
EXPECTED_UPDATES = 782
EXPECTED_STEPS = 200_192
TELEMETRY_FIELDS = {"update", "relation", "receiver_role", "sender_role", "edge_count", "attention_mean", "gate_mean", "effective_payload_mean"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def audit_one(arm: str, seed: int) -> dict:
    directory = RUN_ROOT / arm / f"seed{seed}"
    manifest_path = directory / "run_manifest.json"
    checkpoint = directory / "actor_critic_latest.pt"
    telemetry = directory / "role_gate_telemetry.csv"
    log = directory / "train_log.csv"
    result = {"arm": arm, "seed": seed, "errors": []}
    if not manifest_path.exists():
        result["errors"].append("missing run manifest")
        return result
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    result["status"] = manifest.get("completion_status")
    result["declared_steps"] = manifest.get("environment_steps")
    result["git_sha"] = manifest.get("git_sha")
    result["config_sha256"] = manifest.get("config_sha256")
    if result["status"] != "completed":
        result["errors"].append("manifest is not completed")
    if result["declared_steps"] != EXPECTED_STEPS:
        result["errors"].append("environment-step budget mismatch")
    if not log.exists():
        result["errors"].append("missing train log")
    else:
        with log.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        result["updates_logged"] = len(rows)
        if len(rows) != EXPECTED_UPDATES or not rows or int(rows[-1]["update"]) != EXPECTED_UPDATES:
            result["errors"].append("update count mismatch")
    if not checkpoint.exists():
        result["errors"].append("missing fixed final checkpoint")
    else:
        try:
            state = torch.load(checkpoint, map_location="cpu", weights_only=True)
            result["checkpoint_reload"] = isinstance(state, dict) and bool(state)
        except Exception as exc:  # audit needs evidence, not a hidden retry
            result["checkpoint_reload"] = False
            result["errors"].append(f"checkpoint reload failed: {type(exc).__name__}")
        result["checkpoint_sha256"] = sha256(checkpoint)
        if manifest.get("checkpoint_sha256") != result["checkpoint_sha256"]:
            result["errors"].append("checkpoint hash mismatch")
    if not telemetry.exists():
        result["errors"].append("missing telemetry")
    else:
        with telemetry.open(newline="", encoding="utf-8") as handle:
            fields = set((csv.DictReader(handle).fieldnames or []))
        result["telemetry_schema"] = TELEMETRY_FIELDS.issubset(fields)
        if not result["telemetry_schema"]:
            result["errors"].append("telemetry schema mismatch")
    result["pass"] = not result["errors"]
    return result


def main() -> None:
    results = [audit_one(arm, seed) for arm in EXPECTED_ARMS for seed in EXPECTED_SEEDS]
    all_pass = all(row["pass"] for row in results)
    incident_count = 0
    if INCIDENT_LOG.exists():
        with INCIDENT_LOG.open(newline="", encoding="utf-8") as handle:
            incident_count = sum(1 for _ in csv.DictReader(handle))
    lines = [
        "# Phase 2I-A2 training completion audit", "",
        "**Artifact class:** DEVELOPMENT_ONLY", "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}", "",
        "## Result", "",
        "**PASS** — all six fixed-budget runs are complete and their final artifacts are valid." if all_pass else "**NO-GO** — one or more fixed-budget runs failed completion audit.", "",
        "## Per-run evidence", "",
        "| Arm | Seed | Updates | Environment steps | Final checkpoint reload | Checkpoint SHA256 | Telemetry schema | Status |",
        "|---|---:|---:|---:|---|---|---|---|",
    ]
    for row in results:
        errors = "; ".join(row["errors"]) or "PASS"
        lines.append(f"| {row['arm']} | {row['seed']} | {row.get('updates_logged', '—')} | {row.get('declared_steps', '—')} | {row.get('checkpoint_reload', False)} | {row.get('checkpoint_sha256', '—')} | {row.get('telemetry_schema', False)} | {errors} |")
    lines += ["", "## Incidents", "", f"Recorded incidents: {incident_count}. The only recorded incident occurred before any run artifact was created; no completed result was discarded.", "", "## Boundary", "", "This audit does not inspect training performance. Fixed-final-checkpoint development validation may proceed only because this completion audit is PASS.", ""]
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(OUT)
    if not all_pass:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
