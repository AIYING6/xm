"""Read-only artifact gate for the six-run v1.9 D1-R2 engineering pilot."""
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

from scripts.select_formal_v1_8_repair_checkpoints import verify_and_select  # noqa: E402

PROTOCOL = "V1_9_D1_R2_ENGINEERING_PILOT"
EXPECTED_UPDATES = [1, 10, 20, 30]
RUNS = tuple(
    (f"{method}_seed{seed}", method, seed, encoder, hidden)
    for method, encoder, hidden in (
        ("pcrf_r2", "pcrf_r2", 128),
        ("single_r2", "single_r2", 147),
        ("matched_nongraph_r2", "matched_nongraph_r2", 152),
    )
    for seed in (9201, 9202)
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def fail(message: str) -> None:
    raise RuntimeError(f"D1_R2_ARTIFACT_GATE_FAILED: {message}")


def read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot read {path}: {exc}")


def verify_log(run_dir: Path) -> str:
    log_path = run_dir / "train_log.csv"
    if not log_path.exists():
        fail(f"missing training log: {run_dir}")
    rows = list(csv.DictReader(log_path.open(encoding="utf-8", newline="")))
    updates = [int(row["update"]) for row in rows]
    if updates != list(range(1, 31)):
        fail(f"{run_dir.name}: expected contiguous updates 1..30, got {updates}")
    for row in rows:
        for name in ("loss", "policy_loss", "value_loss", "entropy", "grad_norm"):
            try:
                value = float(row[name])
            except (KeyError, ValueError) as exc:
                fail(f"{run_dir.name}: invalid {name} at update {row.get('update')}: {exc}")
            if not math.isfinite(value):
                fail(f"{run_dir.name}: non-finite {name} at update {row['update']}")
    return sha256(log_path)


def verify_stderr(run_dir: Path) -> None:
    for name in ("segment_01_10.stderr.log", "segment_11_30.stderr.log"):
        path = run_dir / name
        if not path.exists():
            fail(f"{run_dir.name}: missing {name}")
        if path.read_text(encoding="utf-8").strip():
            fail(f"{run_dir.name}: non-empty {name}")


def verify_r2_snapshot_interface(snapshot: Path, encoder: str) -> None:
    try:
        import torch
        payload = torch.load(snapshot, map_location="cpu", weights_only=False)
        keys = set(payload["model_state"])
    except Exception as exc:  # artifact failure, not a model result
        fail(f"cannot load {snapshot}: {exc}")
    if encoder == "pcrf_r2":
        required, prohibited = "actor.pcrf_r2_graph.", ("actor.pcrf_graph.", "actor.multi_relation_graph.")
    else:
        required, prohibited = "actor.r2_unified_graph.", ("actor.pcrf_r2_graph.", "actor.pcrf_graph.", "actor.multi_relation_graph.")
    if not any(key.startswith(required) for key in keys):
        fail(f"{snapshot}: missing expected R2 encoder state {required}")
    if any(key.startswith(prefix) for prefix in prohibited for key in keys):
        fail(f"{snapshot}: contains prohibited historical actor path")


def check_run(root: Path, directory: str, method: str, seed: int, encoder: str, hidden: int, expected_commit: str) -> dict:
    run_dir = root / directory
    winner, candidates = verify_and_select(run_dir, method, seed, PROTOCOL)
    updates = [int(candidate["update"]) for candidate in candidates]
    if updates != EXPECTED_UPDATES:
        fail(f"{directory}: expected validation updates {EXPECTED_UPDATES}, got {updates}")
    for candidate in candidates:
        if candidate.get("git_commit") != expected_commit:
            fail(f"{directory}: source commit mismatch at update {candidate['update']}")
        verify_r2_snapshot_interface(run_dir / candidate["snapshot_path"], encoder)
    verify_stderr(run_dir)
    log_sha = verify_log(run_dir)
    for required in ("segment_01_10.stdout.log", "segment_11_30.stdout.log", "actor_critic_training_state_latest.pt"):
        if not (run_dir / required).exists():
            fail(f"{directory}: missing continuation artifact {required}")
    return {
        "run": directory,
        "method": method,
        "seed": seed,
        "graph_encoder": encoder,
        "hidden_dim": hidden,
        "engineering_only": True,
        "selector_output_for_artifact_check_only": {
            "update": int(winner["update"]),
            "snapshot_sha256": winner["snapshot_sha256"],
        },
        "train_log_sha256": log_sha,
        "validated_updates": updates,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--expected-source-commit", required=True)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    if len(args.expected_source_commit) != 40:
        fail("expected source commit must be a full 40-character Git commit")
    runtime_path = args.root / "runtime_manifest.json"
    runtime = read_json(runtime_path)
    if runtime.get("protocol_version") != PROTOCOL or not runtime.get("cuda_available"):
        fail("runtime manifest does not attest the frozen D1-R2 CUDA protocol")
    if runtime.get("git_commit") != args.expected_source_commit:
        fail("runtime manifest source commit mismatch")
    runs = [check_run(args.root, *run, args.expected_source_commit) for run in RUNS]
    result = {
        "status": "D1_R2_ARTIFACT_GATE_PASS",
        "protocol_version": PROTOCOL,
        "performance_use_prohibited": True,
        "source_commit": args.expected_source_commit,
        "runs": runs,
    }
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        if args.output.exists():
            fail(f"refusing to overwrite output: {args.output}")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    print(encoded, end="")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2)
