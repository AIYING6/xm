"""Build the source-only fixed endpoint TATG evaluation cloud package."""

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INCLUDED_TREES = ("algorithms", "envs")
INCLUDED_FILES = (
    "requirements.txt", "environment.yml",
    "configs/tatg_mappo_pilot_freeze.json",
    "configs/tatg_mappo_pilot_development_tape.json",
    "configs/tatg_mappo_pilot_p4_evaluation_freeze.json",
    "scripts/run_tatg_mappo_pilot_single.py",
    "scripts/run_tatg_mappo_pilot_evaluation.py",
    "scripts/launch_tatg_mappo_pilot_evaluation_autodl.sh",
    "scripts/audit_tatg_mappo_pilot_p4_evaluation.py",
)


def sources() -> list[Path]:
    paths = [ROOT / entry for entry in INCLUDED_FILES]
    for tree in INCLUDED_TREES:
        paths.extend(sorted((ROOT / tree).rglob("*.py")))
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(missing)
    return sorted(set(paths))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("refusing to build endpoint-evaluation bundle without --execute")
    output = Path(args.output).resolve()
    if output.exists():
        raise FileExistsError(output)
    files = sources()
    manifest = {
        "protocol": "TATG-MAPPO-FRESH-SEED-PILOT-P4-FIXED-ENDPOINT-EVALUATION-BUNDLE-V1",
        "purpose": "fixed endpoint development-only evaluation; no training, resume, aggregation or gate",
        "files": {path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in files},
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, path.relative_to(ROOT).as_posix())
        archive.writestr("TATG_PILOT_ENDPOINT_EVALUATION_BUNDLE_MANIFEST.json", json.dumps(manifest, indent=2) + "\n")
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_suffix(output.suffix + ".sha256").write_text(f"{digest}  {output.name}\n", encoding="utf-8")
    print(json.dumps({"bundle": str(output), "sha256": digest, "source_files": len(files), "training_started": False, "evaluation_started": False}, indent=2))


if __name__ == "__main__":
    main()
