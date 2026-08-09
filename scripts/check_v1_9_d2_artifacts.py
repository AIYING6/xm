"""Read-only artifact gate for the PCRF-only v1.9 D2 budget calibration."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.select_formal_v1_8_repair_checkpoints import verify_and_select  # noqa: E402

PROTOCOL = "V1_9_D2_BUDGET_CALIBRATION_R1"
RUNS = tuple((f"pcrf_seed{seed}", "pcrf", seed) for seed in (9201, 9202, 9203))
EXPECTED_UPDATES = [1, 20, 40, 60, 80, 100]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def check_run(root: Path, directory: str, method: str, seed: int) -> dict:
    run_dir = root / directory
    _, candidates = verify_and_select(run_dir, method, seed, PROTOCOL)
    updates = [int(candidate["update"]) for candidate in candidates]
    if updates != EXPECTED_UPDATES:
        raise RuntimeError(f"{directory}: expected validation updates {EXPECTED_UPDATES}, got {updates}")
    log_path = run_dir / "train_log.csv"
    rows = list(csv.DictReader(log_path.open(encoding="utf-8", newline="")))
    if not rows or int(rows[-1]["update"]) != 100:
        raise RuntimeError(f"{directory}: training did not reach update 100")
    runtime_path = run_dir / "runtime_timing.json"
    if not runtime_path.exists():
        raise RuntimeError(f"{directory}: missing portable timing record")
    timing = json.loads(runtime_path.read_text(encoding="utf-8"))
    if timing.get("return_code") != 0 or float(timing.get("wall_seconds", -1.0)) < 0.0:
        raise RuntimeError(f"{directory}: invalid portable timing record")
    return {
        "run": directory,
        "method": method,
        "seed": seed,
        "train_log_sha256": sha256(log_path),
        "validated_updates": updates,
        "runtime_record_sha256": sha256(runtime_path),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    args = parser.parse_args()
    runtime = args.root / "runtime_manifest.json"
    if not runtime.exists():
        raise RuntimeError("missing pre-training CUDA runtime manifest")
    manifest = json.loads(runtime.read_text(encoding="utf-8"))
    if not manifest.get("cuda_available"):
        raise RuntimeError("runtime manifest does not attest CUDA availability")
    if manifest.get("protocol_version") != PROTOCOL:
        raise RuntimeError("runtime manifest protocol provenance mismatch")
    source = manifest.get("source_archive_provenance", {})
    if not source.get("commit") or not source.get("archive_sha256"):
        raise RuntimeError("runtime manifest lacks immutable source-archive provenance")
    telemetry = args.root / "gpu_telemetry.csv"
    if not telemetry.exists() or not telemetry.read_text(encoding="utf-8").strip():
        raise RuntimeError("missing GPU telemetry")
    checks = [check_run(args.root, *run) for run in RUNS]
    print(json.dumps({"status": "D2_ARTIFACT_GATE_PASS", "runs": checks}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
