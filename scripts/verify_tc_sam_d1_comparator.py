"""Verify frozen T1 UTR provenance before TC-SAM-D1 creates any trajectory."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.run_t1_telemetry_native_single import ENVIRONMENT_STEPS, SEEDS  # noqa: E402

T1_HASH = "3de6e4fabf07bb76fe7c9271b3f3e70a5910262581ac14b3de162533ef83e6c3"


def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for part in iter(lambda: f.read(1024 * 1024), b""):
            h.update(part)
    return h.hexdigest()


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--t1-root", type=Path, required=True)
    p.add_argument("--output-root", type=Path, required=True)
    p.add_argument("--execute", action="store_true")
    a = p.parse_args()
    if not a.execute:
        raise SystemExit("explicit --execute required")
    if a.output_root.exists() and any(a.output_root.iterdir()):
        raise FileExistsError(f"refusing nonempty D1 root: {a.output_root}")
    tape = json.loads((a.t1_root / "tape_manifest.json").read_text(encoding="utf-8"))
    checks = {"tape_hash": tape.get("tape_hash") == T1_HASH, "seeds": list(SEEDS), "cells": {}}
    for seed in SEEDS:
        path = a.t1_root / "runs" / "utr_sg" / f"seed{seed}"
        manifest = json.loads((path / "run_manifest.json").read_text(encoding="utf-8"))
        checkpoint = path / "actor_critic_latest.pt"
        ok = (manifest.get("status") == "completed" and manifest.get("method") == "UTR-SG-MAPPO"
              and manifest.get("parameter_count") == 116728 and manifest.get("graph_encoder") == "single"
              and manifest.get("actor_gradient_mode") == "utr" and manifest.get("environment_steps") == ENVIRONMENT_STEPS
              and manifest.get("from_scratch") is True and manifest.get("strict_continuous") is True
              and manifest.get("final_checkpoint_only") is True and manifest.get("tape_hash") == T1_HASH
              and checkpoint.exists() and file_hash(checkpoint) == manifest.get("final_checkpoint_sha256"))
        checks["cells"][str(seed)] = {"pass": ok, "checkpoint_sha256": manifest.get("final_checkpoint_sha256")}
    checks["status"] = "PASS" if checks["tape_hash"] and all(x["pass"] for x in checks["cells"].values()) else "FAIL"
    a.output_root.mkdir(parents=True, exist_ok=False)
    (a.output_root / "comparator_provenance.json").write_text(json.dumps(checks, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(checks, indent=2))
    if checks["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
