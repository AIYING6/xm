"""Artifact/stability gate for the method-blind D2-R2 calibration."""
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

PROTOCOL = "V1_9_D2_R2_BUDGET_STABILITY_CALIBRATION"
UPDATES = [1, *range(20, 301, 20)]
RUNS = tuple(
    (f"{method}_seed{seed}", method, seed, encoder, hidden)
    for method, encoder, hidden in (("pcrf_r2", "pcrf_r2", 128), ("single_r2", "single_r2", 147), ("matched_nongraph_r2", "matched_nongraph_r2", 152))
    for seed in (9501, 9502)
)
REQUIRED_SUMMARY = {"eval_rmte80", "eval_establishment_probability80", "eval_terminal_failure_incidence80", "eval_active_not_established_probability80", "eval_rmte220"}
REQUIRED_RECORDS = {"episode_seed", "failure_onset_step", "event_observed", "event_time", "termination_reason", "terminal_failure_observed", "terminal_failure_time"}


def fail(message: str) -> None:
    raise RuntimeError(f"D2_R2_ARTIFACT_GATE_FAILED: {message}")


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def check_run(root: Path, directory: str, method: str, seed: int, encoder: str, hidden: int, commit: str) -> dict:
    import torch
    run = root / directory
    rows = list(csv.DictReader((run / "train_log.csv").open(encoding="utf-8", newline="")))
    if [int(row["update"]) for row in rows] != list(range(1, 301)):
        fail(f"{directory}: training updates are not contiguous 1..300")
    for row in rows:
        for field in ("loss", "policy_loss", "value_loss", "entropy", "grad_norm"):
            if not math.isfinite(float(row[field])):
                fail(f"{directory}: non-finite {field} at {row['update']}")
    stderr = run / "train.stderr.log"
    if not stderr.exists() or stderr.read_text(encoding="utf-8").strip():
        fail(f"{directory}: stderr is missing or nonempty")
    for update in UPDATES:
        snapshot = run / f"actor_critic_update_{update:04d}.pt"
        metadata_path = run / f"actor_critic_update_{update:04d}.metadata.json"
        point = run / "validation" / f"update_{update:04d}"
        if not snapshot.exists() or not metadata_path.exists() or not point.exists():
            fail(f"{directory}: missing immutable validation artifact at {update}")
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if metadata.get("protocol_version") != PROTOCOL or metadata.get("git_commit") != commit or metadata.get("sha256") != digest(snapshot):
            fail(f"{directory}: bad snapshot provenance at {update}")
        summary = json.loads((point / "summary.json").read_text(encoding="utf-8"))
        if not REQUIRED_SUMMARY.issubset(summary):
            fail(f"{directory}: selector fields absent at {update}")
        with (point / "episode_event_records.csv").open(encoding="utf-8", newline="") as f:
            if not REQUIRED_RECORDS.issubset(set(next(csv.reader(f)))):
                fail(f"{directory}: event fields absent at {update}")
        keys = set(torch.load(snapshot, map_location="cpu", weights_only=False)["model_state"])
        prefix = "actor.pcrf_r2_graph." if encoder == "pcrf_r2" else "actor.r2_unified_graph."
        if not any(key.startswith(prefix) for key in keys):
            fail(f"{directory}: R2 encoder missing at {update}")
    return {"run": directory, "method": method, "seed": seed, "encoder": encoder, "hidden_dim": hidden, "train_log_sha256": digest(run / "train_log.csv"), "validated_updates": UPDATES}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--expected-source-commit", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    runtime = json.loads((args.root / "runtime_manifest.json").read_text(encoding="utf-8"))
    if runtime.get("protocol_version") != PROTOCOL or not runtime.get("cuda_available") or runtime.get("git_commit") != args.expected_source_commit:
        fail("invalid CUDA runtime/source attestation")
    result = {"status": "D2_R2_ARTIFACT_AND_STABILITY_GATE_PASS", "protocol_version": PROTOCOL, "performance_use_prohibited": True, "source_commit": args.expected_source_commit, "runs": [check_run(args.root, *run, args.expected_source_commit) for run in RUNS]}
    if args.output.exists():
        fail(f"refusing to overwrite {args.output}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
        raise SystemExit(2)
