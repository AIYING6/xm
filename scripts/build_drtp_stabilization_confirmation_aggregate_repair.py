"""Build a read-only aggregation repair package for a completed cohort."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import zipfile


ROOT = Path(__file__).resolve().parents[1]
COMMON_FILES = (
    "scripts/aggregate_drtp_stabilization_confirmation.py",
    "scripts/drtp_stabilization_confirmation_contracts.py",
)

COHORT_FILES = {
    "A": "configs/drtp_stabilization_final_freeze.json",
    "B": "configs/drtp_stabilization_independent_replication_freeze.json",
}


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cohort", choices=tuple(COHORT_FILES), default="A")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    default_name = (
        "DRTP_STABILIZATION_FINAL_CONFIRMATION_AGGREGATE_REPAIR_V1.zip"
        if args.cohort == "A"
        else "DRTP_STABILIZATION_INDEPENDENT_REPLICATION_AGGREGATE_REPAIR_V1.zip"
    )
    output = args.output or ROOT / "output" / default_name
    stage_name = (
        "DRTP_STABILIZATION_FINAL_CONFIRMATION_AGGREGATE_REPAIR"
        if args.cohort == "A"
        else "DRTP_STABILIZATION_INDEPENDENT_REPLICATION_AGGREGATE_REPAIR"
    )
    files = (*COMMON_FILES, COHORT_FILES[args.cohort])
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="drtp_aggregate_repair_") as temporary:
        stage = Path(temporary) / stage_name
        stage.mkdir()
        for rel in files:
            source, target = ROOT / rel, stage / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.read_bytes())
        (stage / "README_REPAIR.txt").write_text(
            f"This package only repairs final aggregation after a completed {args.cohort}-cohort endpoint evaluation. "
            "It must not train, evaluate, alter checkpoints, or overwrite a non-empty diagnostics directory.\n",
            encoding="utf-8",
        )
        (stage / "REPAIR_PROVENANCE.json").write_text(json.dumps({
            "protocol": "DRTP-STABILIZATION-CONFIRMATION-AGGREGATE-REPAIR-V1",
            "cohort": args.cohort,
            "commit": commit,
            "allowed_input": "completed evaluations/final_10m only",
            "training_started": False,
            "evaluation_started": False,
            "checkpoint_selection": False,
            "algorithm_revision": False,
        }, indent=2) + "\n", encoding="utf-8")
        if output.exists():
            output.unlink()
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
            for path in stage.rglob("*"):
                if path.is_file():
                    archive.write(path, path.relative_to(stage.parent))
    output.with_suffix(output.suffix + ".sha256").write_text(f"{digest(output)}  {output.name}\n", encoding="utf-8")
    print(json.dumps({"cohort": args.cohort, "package": str(output), "sha256": digest(output), "commit": commit}, indent=2))


if __name__ == "__main__":
    main()
