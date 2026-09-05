"""Build a source-only package for the frozen DRTP final confirmation."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "DRTP_STABILIZATION_FINAL_CONFIRMATION_10M.zip"
SOURCE_PATHS = ("algorithms", "envs", "scripts", "configs", "docs/drtp_stabilization_final_freeze_20260905", "requirements.txt", "README.md")


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="drtp_confirmation_") as temporary:
        temp = Path(temporary)
        source = temp / "source.zip"
        subprocess.run(["git", "archive", "--format=zip", f"--output={source}", commit, "--", *SOURCE_PATHS], cwd=ROOT, check=True)
        stage = temp / "DRTP_STABILIZATION_FINAL_CONFIRMATION"
        stage.mkdir()
        with zipfile.ZipFile(source) as archive:
            archive.extractall(stage)
        provenance = {
            "protocol": "DRTP-STABILIZATION-FINAL-CONFIRMATION-CLOUD-PACKAGE-V1",
            "commit": commit,
            "authorized_scope": "4 frozen arms x 5 fresh seeds x 10,000,128 steps, fixed final endpoint evaluation and report",
            "training_seeds": [78011, 78012, 78013, 78014, 78015],
            "arms": ["utr_sg", "drtp_sg", "egtr_sg", "global_anchored_egtr_a075_sg"],
            "final_alpha": 0.75,
            "automatic_training": False,
            "automatic_algorithm_revision": False,
            "automatic_6uav": False,
        }
        (stage / "CONFIRMATORY_CLOUD_PROVENANCE.json").write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
        (stage / "README_AUTODL.txt").write_text(
            "First run scripts/verify_drtp_stabilization_confirmation_preflight.py only. "
            "Training requires a separate user authorization. The supplied launcher performs only the frozen confirmation and its fixed endpoint evaluation/report.\n",
            encoding="utf-8",
        )
        if OUT.exists():
            OUT.unlink()
        shutil.make_archive(str(OUT.with_suffix("")), "zip", temp, stage.name)
    OUT.with_suffix(OUT.suffix + ".sha256").write_text(f"{digest(OUT)}  {OUT.name}\n", encoding="utf-8")
    print(json.dumps({"package": str(OUT), "sha256": digest(OUT), "commit": commit}, indent=2))


if __name__ == "__main__":
    main()
