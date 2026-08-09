"""Artifact gate for the P0-B cache-validity delta requalification."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.select_v1_9_p0a_rmte_checkpoints import verify_and_select  # noqa: E402

PROTOCOL = "V1_9_D1_R2_P0B_DELTA_REQUALIFICATION"
EXPECTED_UPDATES = [1, 5, 10, 15]
RUNS = (
    ("pcrf_r2_seed9401", "pcrf_r2", "pcrf_r2", 128),
    ("single_r2_seed9401", "single_r2", "single_r2", 147),
    ("matched_nongraph_r2_seed9401", "matched_nongraph_r2", "matched_nongraph_r2", 152),
)


def fail(message: str) -> None:
    raise RuntimeError(f"D1_R2_P0B_DELTA_REQUALIFICATION_FAILED: {message}")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def check_run(root: Path, directory: str, method: str, encoder: str, hidden: int, commit: str) -> dict:
    run_dir = root / directory
    winner, candidates = verify_and_select(run_dir, method, 9401, PROTOCOL)
    if [int(row["update"]) for row in candidates] != EXPECTED_UPDATES:
        fail(f"{directory}: expected validation updates {EXPECTED_UPDATES}")
    for row in candidates:
        update = int(row["update"])
        if row.get("git_commit") != commit:
            fail(f"{directory}: source commit mismatch at update {update}")
        metadata_path = run_dir / f"actor_critic_update_{update:04d}.metadata.json"
        if not metadata_path.exists():
            fail(f"{directory}: missing metadata at {update}")
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if metadata.get("protocol_version") != PROTOCOL or metadata.get("sha256") != row["snapshot_sha256"]:
            fail(f"{directory}: snapshot provenance mismatch at {update}")
        import torch
        keys = set(torch.load(run_dir / row["snapshot_path"], map_location="cpu", weights_only=False)["model_state"])
        prefix = "actor.pcrf_r2_graph." if encoder == "pcrf_r2" else "actor.r2_unified_graph."
        if not any(key.startswith(prefix) for key in keys):
            fail(f"{directory}: repaired R2 actor encoder absent at {update}")
    rows = list(csv.DictReader((run_dir / "train_log.csv").open(encoding="utf-8", newline="")))
    if [int(row["update"]) for row in rows] != list(range(1, 16)):
        fail(f"{directory}: incomplete training log")
    for row in rows:
        for field in ("loss", "policy_loss", "value_loss", "entropy", "grad_norm"):
            if not math.isfinite(float(row[field])):
                fail(f"{directory}: non-finite {field} at update {row['update']}")
    stderr = run_dir / "train.stderr.log"
    if not stderr.exists() or stderr.read_text(encoding="utf-8").strip():
        fail(f"{directory}: stderr is missing or nonempty")
    return {
        "run": directory, "method": method, "seed": 9401, "graph_encoder": encoder,
        "hidden_dim": hidden, "engineering_only": True,
        "selected_update_for_artifact_check_only": int(winner["update"]),
        "selected_snapshot_sha256": winner["snapshot_sha256"],
        "train_log_sha256": sha256(run_dir / "train_log.csv"),
        "validated_updates": EXPECTED_UPDATES,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--expected-source-commit", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    runtime = json.loads((args.root / "runtime_manifest.json").read_text(encoding="utf-8"))
    if runtime.get("protocol_version") != PROTOCOL or not runtime.get("cuda_available"):
        fail("runtime manifest does not attest the P0-B delta CUDA protocol")
    if runtime.get("git_commit") != args.expected_source_commit:
        fail("runtime manifest source commit mismatch")
    preflight = args.root / "p0b_runtime_path.log"
    if "P0_B_FEATURE_PROVENANCE_AUDIT_V1_9: PASS (5 tests)" not in preflight.read_text(encoding="utf-8"):
        fail("missing passing P0-B runtime-path regression")
    result = {
        "status": "D1_R2_P0B_DELTA_REQUALIFICATION_GATE_PASS__P0_R2_RED_TEAM_CONTINUES__D2_NOT_AUTHORIZED",
        "protocol_version": PROTOCOL,
        "performance_use_prohibited": True,
        "source_commit": args.expected_source_commit,
        "runs": [check_run(args.root, *run, args.expected_source_commit) for run in RUNS],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.exists():
        fail(f"refusing to overwrite output: {args.output}")
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2)
