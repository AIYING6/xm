"""Read-only artifact gate for D1-R2 P0-A statistical requalification."""
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

PROTOCOL = "V1_9_D1_R2_P0A_REQUALIFICATION"
EXPECTED_UPDATES = [1, 10, 20, 30]
RUNS = tuple(
    (f"{method}_seed{seed}", method, seed, encoder, hidden)
    for method, encoder, hidden in (
        ("pcrf_r2", "pcrf_r2", 128),
        ("single_r2", "single_r2", 147),
        ("matched_nongraph_r2", "matched_nongraph_r2", 152),
    )
    for seed in (9301, 9302)
)


def fail(message: str) -> None:
    raise RuntimeError(f"D1_R2_P0A_REQUALIFICATION_FAILED: {message}")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def check_run(root: Path, directory: str, method: str, seed: int, encoder: str, hidden: int, expected_commit: str) -> dict:
    run_dir = root / directory
    winner, candidates = verify_and_select(run_dir, method, seed, PROTOCOL)
    updates = [int(candidate["update"]) for candidate in candidates]
    if updates != EXPECTED_UPDATES:
        fail(f"{directory}: expected updates {EXPECTED_UPDATES}, got {updates}")
    for candidate in candidates:
        update = int(candidate["update"])
        if candidate.get("git_commit") != expected_commit:
            fail(f"{directory}: source commit mismatch at {update}")
        metadata = json.loads((run_dir / f"actor_critic_update_{update:04d}.metadata.json").read_text(encoding="utf-8"))
        if metadata.get("sha256") != candidate["snapshot_sha256"] or metadata.get("protocol_version") != PROTOCOL:
            fail(f"{directory}: snapshot metadata mismatch at {update}")
        import torch
        keys = set(torch.load(run_dir / candidate["snapshot_path"], map_location="cpu", weights_only=False)["model_state"])
        required = "actor.pcrf_r2_graph." if encoder == "pcrf_r2" else "actor.r2_unified_graph."
        if not any(key.startswith(required) for key in keys):
            fail(f"{directory}: R2 actor encoder not present at {update}")
    log = run_dir / "train_log.csv"
    rows = list(csv.DictReader(log.open(encoding="utf-8", newline="")))
    if [int(row["update"]) for row in rows] != list(range(1, 31)):
        fail(f"{directory}: incomplete or non-contiguous train log")
    for row in rows:
        for field in ("loss", "policy_loss", "value_loss", "entropy", "grad_norm"):
            if not math.isfinite(float(row[field])):
                fail(f"{directory}: non-finite {field} at {row['update']}")
    for name in ("segment_01_10.stderr.log", "segment_11_30.stderr.log"):
        path = run_dir / name
        if not path.exists() or path.read_text(encoding="utf-8").strip():
            fail(f"{directory}: nonempty/missing {name}")
    return {
        "run": directory, "method": method, "seed": seed, "graph_encoder": encoder,
        "hidden_dim": hidden, "engineering_only": True,
        "selected_update_for_artifact_check_only": int(winner["update"]),
        "selected_snapshot_sha256": winner["snapshot_sha256"],
        "train_log_sha256": sha256(log), "validated_updates": updates,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--expected-source-commit", required=True)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    runtime = json.loads((args.root / "runtime_manifest.json").read_text(encoding="utf-8"))
    if runtime.get("protocol_version") != PROTOCOL or not runtime.get("cuda_available"):
        fail("runtime manifest does not attest P0-A requalification CUDA protocol")
    if runtime.get("git_commit") != args.expected_source_commit:
        fail("runtime manifest source commit mismatch")
    runs = [check_run(args.root, *run, args.expected_source_commit) for run in RUNS]
    result = {
        "status": "D1_R2_P0A_REQUALIFICATION_GATE_PASS__P0_R2_RED_TEAM_CONTINUES__D2_NOT_AUTHORIZED",
        "protocol_version": PROTOCOL, "performance_use_prohibited": True,
        "source_commit": args.expected_source_commit, "runs": runs,
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
