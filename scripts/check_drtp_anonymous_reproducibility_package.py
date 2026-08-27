"""Check a generated anonymous DRTP reproducibility-package staging directory."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path


REQUIRED = ("README.md", "CITATION.cff", "RELEASE_BLOCKERS.md", "LICENSE-REQUIRED-BEFORE-PUBLIC-RELEASE.md", "checkpoints/README.md", "source_data/DATA_DICTIONARY.md", "manifests/FILE_MANIFEST_SHA256.csv", "manifests/PACKAGE_PROVENANCE.json")
STRATA = ("formal_2301_2305", "mappo_nograph_2301_2305", "independent_2401_2405")


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
    if missing: raise SystemExit(f"FAIL: missing package assets: {missing}")
    mismatch = []
    with (root / "manifests" / "FILE_MANIFEST_SHA256.csv").open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            path = root / row["relative_path"]
            if not path.is_file() or digest(path) != row["sha256"]: mismatch.append(row["relative_path"])
    provenance = json.loads((root / "manifests" / "PACKAGE_PROVENANCE.json").read_text(encoding="utf-8"))
    if provenance.get("package_status") != "PREPARED_FOR_AUTHOR_HOSTING" or len(provenance.get("archives", [])) != 3: mismatch.append("package provenance")
    if mismatch: raise SystemExit(f"FAIL: checksum/provenance mismatch: {mismatch}")
    print("PASS: anonymous staging package contains all three raw evidence strata and verified manifests.")


if __name__ == "__main__": main()
