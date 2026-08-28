"""Check a generated anonymous DRTP reproducibility-package staging directory."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import re


REQUIRED = ("README.md", "CITATION.cff", "RELEASE_BLOCKERS.md", "LICENSE-REQUIRED-BEFORE-PUBLIC-RELEASE.md", "checkpoints/README.md", "source_data/DATA_DICTIONARY.md", "manifests/FILE_MANIFEST_SHA256.csv", "manifests/PACKAGE_PROVENANCE.json")
STRATA = ("formal_2301_2305", "mappo_nograph_2301_2305", "independent_2401_2405")
CROSS_TAPE_FILES = (
    "source_data/cross_tape_reliability/raw_episode_metrics.csv",
    "source_data/cross_tape_reliability/evaluation_manifest.json",
    "source_data/cross_tape_reliability/DRTP_CROSS_TAPE_RELIABILITY_DECISION.json",
)
TEXT_SUFFIXES = {".md", ".txt", ".json", ".csv", ".py", ".yml", ".yaml", ".cff"}
IDENTITY_PATTERN = re.compile(r"AIYING6|C:\\Users\\|D:\\Code\\|github\.com/AIYING6", re.IGNORECASE)


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("--package-root", type=Path, required=True)
    root = parser.parse_args().package_root.resolve(); missing = [item for item in REQUIRED if not (root / item).is_file()]
    for stratum in STRATA:
        for item in ("evaluations/final_10m/raw_episode_metrics.csv", "evaluations/final_10m/evaluation_manifest.json"):
            if not (root / "source_data" / stratum / item).is_file(): missing.append(f"source_data/{stratum}/{item}")
    for item in CROSS_TAPE_FILES:
        if not (root / item).is_file(): missing.append(item)
    if missing: raise SystemExit(f"FAIL: missing package assets: {missing}")
    mismatch = []
    with (root / "manifests" / "FILE_MANIFEST_SHA256.csv").open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            path = root / row["relative_path"]
            if not path.is_file() or digest(path) != row["sha256"]: mismatch.append(row["relative_path"])
    provenance = json.loads((root / "manifests" / "PACKAGE_PROVENANCE.json").read_text(encoding="utf-8"))
    if provenance.get("package_status") != "PREPARED_FOR_AUTHOR_HOSTING" or len(provenance.get("archives", [])) != 3: mismatch.append("package provenance")
    identity_hits = []
    for path in root.rglob("*"):
        if path.name == "check_drtp_anonymous_reproducibility_package.py":
            continue
        if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES:
            text = path.read_text(encoding="utf-8", errors="ignore")
            if IDENTITY_PATTERN.search(text): identity_hits.append(path.relative_to(root).as_posix())
    if identity_hits: mismatch.append("identity markers: " + ", ".join(identity_hits))
    if mismatch: raise SystemExit(f"FAIL: checksum/provenance mismatch: {mismatch}")
    print("PASS: anonymous staging package contains three training evidence strata plus the cross-tape diagnostic and verified manifests.")


if __name__ == "__main__": main()
