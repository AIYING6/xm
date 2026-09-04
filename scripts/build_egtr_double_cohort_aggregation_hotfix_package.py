"""Build a narrow, no-training repair package for an EGTR final-gate runner bug."""
from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path


FILES = ("scripts/aggregate_egtr_double_cohort_simultaneous.py",)


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            hasher.update(block)
    return hasher.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = args.output.resolve()
    if output.exists():
        raise FileExistsError(output)
    provenance = {
        "protocol": "EGTR-DOUBLE-COHORT-FINAL-GATE-REPAIR-V1",
        "scope": "offline final-gate aggregation only",
        "training_started": False,
        "evaluation_started": False,
        "changes": ["materialize iterable before unchanged frozen arithmetic mean", "reuse empty failed gate directory only"],
        "automatic_continuation": False,
    }
    with zipfile.ZipFile(output, "x", zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for rel in FILES:
            archive.write(root / rel, rel)
        archive.writestr("EGTR_FINAL_GATE_REPAIR_PROVENANCE.json", json.dumps(provenance, indent=2) + "\n")
    checksum = digest(output)
    output.with_suffix(output.suffix + ".sha256").write_text(f"{checksum}  {output.name}\n", encoding="utf-8")
    print(json.dumps({"package": str(output), "sha256": checksum}, indent=2))


if __name__ == "__main__":
    main()
