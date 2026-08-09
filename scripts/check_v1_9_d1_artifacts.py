"""Read-only artifact gate for the four-run v1.9 D1 engineering pilot."""
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

PROTOCOL = "V1_9_D1_ENGINEERING_PILOT"
RUNS = (
    ("pcrf_seed9101", "pcrf", 9101),
    ("pcrf_seed9102", "pcrf", 9102),
    ("single_seed9101", "wider_single_graph", 9101),
    ("single_seed9102", "wider_single_graph", 9102),
)
EXPECTED_UPDATES = [1, 10, 20]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def check_run(root: Path, directory: str, method: str, seed: int) -> dict:
    run_dir = root / directory
    winner, candidates = verify_and_select(run_dir, method, seed, PROTOCOL)
    updates = [int(candidate["update"]) for candidate in candidates]
    if updates != EXPECTED_UPDATES:
        raise RuntimeError(f"{directory}: expected validation updates {EXPECTED_UPDATES}, got {updates}")
    log_path = run_dir / "train_log.csv"
    rows = list(csv.DictReader(log_path.open(encoding="utf-8", newline="")))
    if not rows or int(rows[-1]["update"]) != 20:
        raise RuntimeError(f"{directory}: training did not reach update 20")
    return {
        "run": directory,
        "method": method,
        "seed": seed,
        "selected_update_for_artifact_check_only": int(winner["update"]),
        "selected_snapshot_sha256": winner["snapshot_sha256"],
        "train_log_sha256": sha256(log_path),
        "validated_updates": updates,
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
    checks = [check_run(args.root, *run) for run in RUNS]
    print(json.dumps({"status": "D1_ARTIFACT_GATE_PASS", "runs": checks}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
