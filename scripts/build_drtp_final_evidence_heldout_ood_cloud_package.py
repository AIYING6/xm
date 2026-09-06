"""Build a source-only cloud package for frozen final DRTP held-out/OOD evaluation."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATHS = (
    "algorithms", "envs", "scripts", "configs/drtp_final_evidence_p0_heldout_ood_freeze_20260906.json",
    "docs/drtp_stabilization_final_freeze_20260905/DRTP_FINAL_EVIDENCE_P0_HELDOUT_OOD_CONTRACT_20260906.md",
    "requirements.txt",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    output = ROOT / "output" / "DRTP_FINAL_EVIDENCE_HELDOUT_OOD_EVALUATION_V1.zip"
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="drtp_final_evidence_ood_") as temporary:
        temporary_root = Path(temporary)
        source = temporary_root / "source.zip"
        subprocess.run(["git", "archive", "--format=zip", f"--output={source}", commit, "--", *SOURCE_PATHS], cwd=ROOT, check=True)
        stage = temporary_root / "DRTP_FINAL_EVIDENCE_HELDOUT_OOD_EVALUATION"
        stage.mkdir()
        shutil.unpack_archive(source, stage)
        (stage / "README_AUTODL.txt").write_text(
            "This package performs only final-checkpoint held-out/OOD evaluation of uploaded A/B archives and a descriptive report. "
            "It extracts exactly UTR/DRTP endpoint checkpoints into its output directory; it never trains, selects checkpoints, changes a sampler, or starts external/6-UAV work.\n",
            encoding="utf-8",
        )
        (stage / "CLOUD_PROVENANCE.json").write_text(json.dumps({
            "protocol": "DRTP-FINAL-EVIDENCE-HELDOUT-OOD-CLOUD-PACKAGE-V1", "commit": commit,
            "cells": 20, "episodes": 14000, "default_workers": 20,
            "training_started": False, "checkpoint_selection": False, "automatic_algorithm_revision": False,
        }, indent=2) + "\n", encoding="utf-8")
        if output.exists():
            output.unlink()
        shutil.make_archive(str(output.with_suffix("")), "zip", temporary_root, stage.name)
    output.with_suffix(output.suffix + ".sha256").write_text(f"{sha256(output)}  {output.name}\n", encoding="utf-8")
    print(json.dumps({"package": str(output), "sha256": sha256(output), "commit": commit}, indent=2))


if __name__ == "__main__":
    main()
