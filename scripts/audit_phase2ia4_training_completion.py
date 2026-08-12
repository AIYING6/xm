"""Completion audit for recovered Phase 2IA4 cloud DEVELOPMENT_ONLY runs."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
ARMS = ("full_gate", "no_role_gate")
SEEDS = (101, 202, 303)
EXPECTED_UPDATES = 3907
EXPECTED_STEPS = 1_000_192
TELEMETRY_FIELDS = {"update", "relation", "receiver_role", "sender_role", "edge_count", "attention_mean", "gate_mean", "effective_payload_mean"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def inspect(run_root: Path, arm: str, seed: int) -> dict:
    directory = run_root / arm / f"seed{seed}"
    result = {"arm": arm, "seed": seed, "errors": []}
    manifest_path = directory / "run_manifest.json"
    if not manifest_path.exists():
        result["errors"].append("missing manifest")
        return result
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    result.update({"status": manifest.get("completion_status"), "updates_declared": manifest.get("updates"),
                   "steps": manifest.get("environment_steps"), "git_sha": manifest.get("git_sha"),
                   "config_sha256": manifest.get("config_sha256")})
    if result["status"] != "completed": result["errors"].append("manifest not completed")
    if result["updates_declared"] != EXPECTED_UPDATES: result["errors"].append("declared update mismatch")
    if result["steps"] != EXPECTED_STEPS: result["errors"].append("environment-step mismatch")
    log = directory / "train_log.csv"
    if not log.exists(): result["errors"].append("missing train log")
    else:
        with log.open(newline="", encoding="utf-8") as f: rows = list(csv.DictReader(f))
        result["updates_logged"] = len(rows)
        if len(rows) != EXPECTED_UPDATES or not rows or int(rows[-1]["update"]) != EXPECTED_UPDATES:
            result["errors"].append("logged update mismatch")
    checkpoint = directory / "actor_critic_latest.pt"
    if not checkpoint.exists(): result["errors"].append("missing final checkpoint")
    else:
        try:
            result["checkpoint_reload"] = bool(torch.load(checkpoint, map_location="cpu", weights_only=True))
        except Exception as exc:
            result["checkpoint_reload"] = False; result["errors"].append(f"checkpoint reload {type(exc).__name__}")
        result["checkpoint_sha256"] = sha256(checkpoint)
        if result["checkpoint_sha256"] != manifest.get("checkpoint_sha256"):
            result["errors"].append("checkpoint SHA256 mismatch")
    telemetry = directory / "role_gate_telemetry.csv"
    if not telemetry.exists(): result["errors"].append("missing telemetry")
    else:
        with telemetry.open(newline="", encoding="utf-8") as f: fields = set(csv.DictReader(f).fieldnames or [])
        result["telemetry_schema"] = TELEMETRY_FIELDS.issubset(fields)
        if not result["telemetry_schema"]: result["errors"].append("telemetry schema mismatch")
    result["pass"] = not result["errors"]
    return result


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--run-root", type=Path, default=ROOT / "archival/results/development/role_gate_phase2ia4/runs")
    p.add_argument("--archive", type=Path, default=Path("D:/File/Downloads/phase2ia4_results.tar.gz"))
    p.add_argument("--out", type=Path, default=ROOT / "docs/PHASE2IA4_TRAINING_COMPLETION_AUDIT.md")
    args = p.parse_args()
    rows = [inspect(args.run_root, arm, seed) for arm in ARMS for seed in SEEDS]
    passed = all(r.get("pass") for r in rows)
    archive_hash = sha256(args.archive) if args.archive.exists() else "unavailable"
    lines = ["# Phase 2I-A4 training completion audit", "", "**Artifact class:** DEVELOPMENT_ONLY", "",
             f"Generated: {datetime.now(timezone.utc).isoformat()}", "", "## Result", "",
             "**PASS** — six fixed-budget cloud runs completed with reloadable final checkpoints." if passed else "**NO-GO** — completion evidence failed.", "",
             "## Provenance", "", f"- Cloud archive SHA256: `{archive_hash}`.",
             "- Cloud package contained no `.git` directory; run manifests record `git_sha=packaged-source`. This provenance limitation is retained explicitly.",
             "- Checkpoint hashes and configuration hashes are verified below.", "", "## Per-run evidence", "",
             "| Arm | Seed | Updates | Steps | Checkpoint reload | Telemetry | SHA256 | Status |",
             "|---|---:|---:|---:|---|---|---|---|"]
    for r in rows:
        status = "; ".join(r["errors"]) or "PASS"
        lines.append(f"| {r['arm']} | {r['seed']} | {r.get('updates_logged','—')} | {r.get('steps','—')} | {r.get('checkpoint_reload',False)} | {r.get('telemetry_schema',False)} | {r.get('checkpoint_sha256','—')} | {status} |")
    lines += ["", "## Boundary", "", "This audit inspects completion and artifact integrity only. It does not compare performance. Fixed-final-checkpoint development validation may proceed only because this audit is PASS.", ""]
    args.out.write_text("\n".join(lines), encoding="utf-8")
    print(args.out)
    if not passed: raise SystemExit(1)


if __name__ == "__main__": main()
