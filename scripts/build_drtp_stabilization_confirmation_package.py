"""Build a source-only package for the frozen DRTP final confirmation."""
from __future__ import annotations

import hashlib
import json
import argparse
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile


ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATHS = ("algorithms", "envs", "scripts", "configs", "docs/drtp_stabilization_final_freeze_20260905", "requirements.txt", "README.md")


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cohort", choices=("A", "B"), default="A")
    args = parser.parse_args()
    replication = args.cohort == "B"
    package_name = "DRTP_STABILIZATION_INDEPENDENT_REPLICATION_10M" if replication else "DRTP_STABILIZATION_FINAL_CONFIRMATION_10M"
    stage_name = "DRTP_STABILIZATION_INDEPENDENT_REPLICATION" if replication else "DRTP_STABILIZATION_FINAL_CONFIRMATION"
    output = ROOT / "output" / f"{package_name}.zip"
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="drtp_confirmation_") as temporary:
        temp = Path(temporary)
        source = temp / "source.zip"
        subprocess.run(["git", "archive", "--format=zip", f"--output={source}", commit, "--", *SOURCE_PATHS], cwd=ROOT, check=True)
        stage = temp / stage_name
        stage.mkdir()
        with zipfile.ZipFile(source) as archive:
            archive.extractall(stage)
        provenance = {
            "protocol": "DRTP-STABILIZATION-INDEPENDENT-REPLICATION-CLOUD-PACKAGE-V1" if replication else "DRTP-STABILIZATION-FINAL-CONFIRMATION-CLOUD-PACKAGE-V1",
            "commit": commit,
            "cohort": args.cohort,
            "authorized_scope": "4 frozen arms x 5 disjoint fresh seeds x 10,000,128 steps, fixed final endpoint evaluation and separate report",
            "training_seeds": [78021, 78022, 78023, 78024, 78025] if replication else [78011, 78012, 78013, 78014, 78015],
            "arms": ["utr_sg", "drtp_sg", "egtr_sg", "global_anchored_egtr_a075_sg"],
            "final_alpha": 0.75,
            "automatic_training": False,
            "automatic_algorithm_revision": False,
            "automatic_6uav": False,
        }
        (stage / "CONFIRMATORY_CLOUD_PROVENANCE.json").write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
        (stage / "README_AUTODL.txt").write_text(
            f"Cohort {args.cohort}. First run scripts/verify_drtp_stabilization_confirmation_preflight.py --cohort {args.cohort} only. "
            "Training requires a separate user authorization. The supplied launcher performs only the frozen cohort and its fixed endpoint evaluation/report; it never pools cohorts or changes the algorithm.\n",
            encoding="utf-8",
        )
        if output.exists():
            output.unlink()
        shutil.make_archive(str(output.with_suffix("")), "zip", temp, stage.name)
    output.with_suffix(output.suffix + ".sha256").write_text(f"{digest(output)}  {output.name}\n", encoding="utf-8")
    print(json.dumps({"package": str(output), "sha256": digest(output), "commit": commit, "cohort": args.cohort}, indent=2))


if __name__ == "__main__":
    main()
