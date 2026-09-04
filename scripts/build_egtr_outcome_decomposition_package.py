"""Build the no-training EGTR outcome-decomposition package."""
from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path


FILES = ("scripts/run_egtr_outcome_decomposition.py",)


def checksum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root, output = Path(__file__).resolve().parents[1], args.output.resolve()
    if output.exists():
        raise FileExistsError(output)
    provenance = {"protocol": "EGTR-OUTCOME-DECOMPOSITION-PACKAGE-V1", "scope": "offline post-hoc audit only", "training_started": False, "evaluation_started": False, "automatic_continuation": False}
    with zipfile.ZipFile(output, "x", zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for relative in FILES:
            archive.write(root / relative, relative)
        archive.writestr("EGTR_OUTCOME_DECOMPOSITION_PROVENANCE.json", json.dumps(provenance, indent=2) + "\n")
    digest = checksum(output)
    output.with_suffix(output.suffix + ".sha256").write_text(f"{digest}  {output.name}\n", encoding="utf-8")
    print(json.dumps({"package": str(output), "sha256": digest}, indent=2))


if __name__ == "__main__":
    main()
