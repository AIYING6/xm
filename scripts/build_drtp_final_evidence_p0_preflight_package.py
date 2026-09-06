"""Build the zero-training cloud preflight for final DRTP held-out/OOD evidence."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile


ROOT = Path(__file__).resolve().parents[1]
FILES = (
    "configs/drtp_final_evidence_p0_heldout_ood_freeze_20260906.json",
    "docs/drtp_stabilization_final_freeze_20260905/DRTP_FINAL_EVIDENCE_P0_HELDOUT_OOD_CONTRACT_20260906.md",
    "scripts/verify_drtp_final_evidence_p0_preflight.py",
    "envs/__init__.py",
    "envs/uav_intercept_3d_env.py",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    output = ROOT / "output" / "DRTP_FINAL_EVIDENCE_P0_HELDOUT_OOD_PREFLIGHT.zip"
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="drtp_final_evidence_p0_") as temporary:
        stage = Path(temporary) / "DRTP_FINAL_EVIDENCE_P0_HELDOUT_OOD_PREFLIGHT"
        stage.mkdir()
        for rel in FILES:
            target = stage / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((ROOT / rel).read_bytes())
        (stage / "README_AUTODL.txt").write_text(
            "Upload this zip together with the already downloaded A/B complete-results archives. "
            "This package only verifies archive integrity and frozen environment semantics. It does not extract checkpoints, train, evaluate a policy, select a checkpoint, or start another study.\n",
            encoding="utf-8",
        )
        (stage / "P0_PROVENANCE.json").write_text(json.dumps({
            "protocol": "DRTP-FINAL-EVIDENCE-P0-HELDOUT-OOD-PREFLIGHT-PACKAGE-V1", "commit": commit,
            "training_started": False, "evaluation_started": False, "checkpoint_selection": False,
        }, indent=2) + "\n", encoding="utf-8")
        if output.exists():
            output.unlink()
        shutil.make_archive(str(output.with_suffix("")), "zip", Path(temporary), stage.name)
    output.with_suffix(output.suffix + ".sha256").write_text(f"{sha256(output)}  {output.name}\n", encoding="utf-8")
    print(json.dumps({"package": str(output), "sha256": sha256(output), "commit": commit}, indent=2))


if __name__ == "__main__":
    main()
