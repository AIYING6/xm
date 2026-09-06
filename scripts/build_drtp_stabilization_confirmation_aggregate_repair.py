"""Build a read-only repair package for a completed A-cohort evaluation."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import zipfile


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "DRTP_STABILIZATION_FINAL_CONFIRMATION_AGGREGATE_REPAIR_V1.zip"
FILES = (
    "scripts/aggregate_drtp_stabilization_confirmation.py",
    "scripts/drtp_stabilization_confirmation_contracts.py",
    "configs/drtp_stabilization_final_freeze.json",
)


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="drtp_aggregate_repair_") as temporary:
        stage = Path(temporary) / "DRTP_STABILIZATION_FINAL_CONFIRMATION_AGGREGATE_REPAIR"
        stage.mkdir()
        for rel in FILES:
            source, target = ROOT / rel, stage / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.read_bytes())
        (stage / "README_REPAIR.txt").write_text(
            "This package only repairs final aggregation after a completed A-cohort endpoint evaluation. "
            "It must not train, evaluate, alter checkpoints, or overwrite a non-empty diagnostics directory.\n",
            encoding="utf-8",
        )
        (stage / "REPAIR_PROVENANCE.json").write_text(json.dumps({
            "protocol": "DRTP-STABILIZATION-FINAL-CONFIRMATION-AGGREGATE-REPAIR-V1",
            "commit": commit,
            "allowed_input": "completed evaluations/final_10m only",
            "training_started": False,
            "evaluation_started": False,
            "checkpoint_selection": False,
            "algorithm_revision": False,
        }, indent=2) + "\n", encoding="utf-8")
        if OUT.exists():
            OUT.unlink()
        with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as archive:
            for path in stage.rglob("*"):
                if path.is_file():
                    archive.write(path, path.relative_to(stage.parent))
    OUT.with_suffix(OUT.suffix + ".sha256").write_text(f"{digest(OUT)}  {OUT.name}\n", encoding="utf-8")
    print(json.dumps({"package": str(OUT), "sha256": digest(OUT), "commit": commit}, indent=2))


if __name__ == "__main__":
    main()
