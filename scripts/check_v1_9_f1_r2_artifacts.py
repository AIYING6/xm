"""Integrity gate for the frozen F1-R2 formal-training matrix.

This reads only training-time artifacts.  It never evaluates a checkpoint or
opens the F2 confirmatory population.
"""
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

from scripts.select_v1_9_f1_r2_checkpoints import (  # noqa: E402
    FORMAL_SEEDS,
    METHODS,
    PROTOCOL,
    UPDATES,
    verify_and_select,
)


def fail(message: str) -> None:
    raise RuntimeError(f"F1_R2_ARTIFACT_GATE_FAILED: {message}")


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def check_run(root: Path, method: str, encoder: str, hidden: int, seed: int, commit: str) -> dict:
    import torch

    directory = f"{method}_seed{seed}"
    run = root / directory
    log_path = run / "train_log.csv"
    if not log_path.exists():
        fail(f"{directory}: missing train log")
    with log_path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    if [int(row["update"]) for row in rows] != list(range(1, 301)):
        fail(f"{directory}: training updates are not contiguous 1..300")
    for row in rows:
        for field in ("loss", "policy_loss", "value_loss", "entropy", "grad_norm"):
            if not math.isfinite(float(row[field])):
                fail(f"{directory}: non-finite {field} at update {row['update']}")
    stderr = run / "train.stderr.log"
    if not stderr.exists() or stderr.read_text(encoding="utf-8").strip():
        fail(f"{directory}: stderr is missing or nonempty")
    winner, candidates = verify_and_select(run, method, seed, commit)
    if [int(row["update"]) for row in candidates] != UPDATES:
        fail(f"{directory}: selector candidates differ from frozen updates")
    for update in UPDATES:
        snapshot = run / f"actor_critic_update_{update:04d}.pt"
        payload = torch.load(snapshot, map_location="cpu", weights_only=False)
        keys = set(payload["model_state"])
        prefix = "actor.pcrf_r2_graph." if encoder == "pcrf_r2" else "actor.r2_unified_graph."
        if not any(key.startswith(prefix) for key in keys):
            fail(f"{directory}: wrong R2 encoder at update {update}")
    return {
        "run": directory,
        "method": method,
        "seed": seed,
        "encoder": encoder,
        "hidden_dim": hidden,
        "train_log_sha256": digest(log_path),
        "provisional_selector_winner_update": int(winner["update"]),
        "validated_updates": UPDATES,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--expected-source-commit", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        fail(f"refusing to overwrite frozen output: {args.output}")
    runtime_path = args.root / "runtime_manifest.json"
    if not runtime_path.exists():
        fail("missing CUDA runtime attestation")
    runtime = json.loads(runtime_path.read_text(encoding="utf-8"))
    if (
        runtime.get("protocol_version") != PROTOCOL
        or not runtime.get("cuda_available")
        or runtime.get("git_commit") != args.expected_source_commit
    ):
        fail("invalid CUDA runtime/source attestation")
    runs = [
        check_run(args.root, method, encoder, hidden, seed, args.expected_source_commit)
        for method, encoder, hidden in METHODS
        for seed in FORMAL_SEEDS
    ]
    result = {
        "status": "F1_R2_TRAINING_ARTIFACT_GATE_PASS",
        "protocol_version": PROTOCOL,
        "confirmatory_heldout_accessed": False,
        "source_commit": args.expected_source_commit,
        "runs": runs,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
        raise SystemExit(2)
