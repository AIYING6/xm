"""Build a source-only AutoDL package for Development V1 train/evaluate/assess."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "DRTP_STABILIZATION_DEVELOPMENT_V1_CLOUD_TRAINING.zip"
SOURCE_PATHS = ("algorithms", "envs", "scripts", "configs", "requirements.txt", "README.md")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="drtp_stab_v1_bundle_") as temporary:
        temp = Path(temporary)
        source = temp / "source.zip"
        subprocess.run(
            ["git", "archive", "--format=zip", f"--output={source}", commit, "--", *SOURCE_PATHS],
            cwd=ROOT,
            check=True,
        )
        stage = temp / "DRTP_STABILIZATION_DEVELOPMENT_V1"
        stage.mkdir()
        with zipfile.ZipFile(source) as archive:
            archive.extractall(stage)
        provenance = {
            "protocol": "DRTP-STABILIZATION-DEVELOPMENT-V1-CLOUD-PACKAGE",
            "commit": commit,
            "scope": "18 development trajectories plus frozen fixed-endpoint evaluation and integrated development assessment",
            "training_only": False,
            "endpoint_evaluation": "fixed final checkpoint only; 18 cells x 5 conditions x 100 episodes",
            "integrated_assessment": ["upside", "lower_tail", "mean", "median", "seed_spread", "nominal", "safety", "adaptivity"],
            "automatic_v2_or_confirmation": False,
            "development_seeds": [76011, 76012, 76013],
            "anchor_alphas": [0.35, 0.55, 0.75],
        }
        (stage / "DRTP_STABILIZATION_DEVELOPMENT_V1_PROVENANCE.json").write_text(
            json.dumps(provenance, indent=2) + "\n", encoding="utf-8"
        )
        (stage / "README_AUTODL.txt").write_text(
            "Run scripts/launch_drtp_stabilization_development_v1_autodl.sh only. "
            "It trains the frozen V1 cells, runs fixed endpoint evaluation, then writes an integrated development assessment. "
            "It never starts V2 or confirmation automatically.\n",
            encoding="utf-8",
        )
        if OUT.exists():
            OUT.unlink()
        shutil.make_archive(str(OUT.with_suffix("")), "zip", temp, stage.name)
    OUT.with_suffix(OUT.suffix + ".sha256").write_text(f"{sha256(OUT)}  {OUT.name}\n", encoding="utf-8")
    print(json.dumps({"package": str(OUT), "sha256": sha256(OUT), "commit": commit}, indent=2))


if __name__ == "__main__":
    main()
