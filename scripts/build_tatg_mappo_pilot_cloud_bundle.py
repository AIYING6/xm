"""Build a source-only cloud bundle for the frozen TATG pilot runner."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

INCLUDED_TREES = ("algorithms", "envs")
INCLUDED_FILES = (
    "requirements.txt", "environment.yml",
    "configs/tatg_mappo_pilot_freeze.json",
    "configs/tatg_mappo_pilot_development_tape.json",
    "configs/tatg_mappo_pilot_p1_execution_freeze.json",
    "configs/tatg_mappo_pilot_p2_runner_freeze.json",
    "configs/tatg_mappo_pilot_p3_cloud_package_freeze.json",
    "scripts/run_tatg_mappo_pilot_single.py",
    "scripts/launch_tatg_mappo_pilot_autodl.sh",
    "scripts/audit_tatg_mappo_pilot_p2_runner.py",
    "scripts/audit_tatg_mappo_pilot_p3_cloud_package.py",
)


def sources() -> list[Path]:
    files = [ROOT / name for name in INCLUDED_FILES]
    for tree in INCLUDED_TREES:
        files.extend(sorted((ROOT / tree).rglob("*.py")))
    missing = [str(path) for path in files if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"bundle source missing: {missing}")
    return sorted(set(files))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("refusing to build cloud bundle without --execute")
    output = Path(args.output).resolve()
    if output.exists():
        raise SystemExit(f"refusing to overwrite existing bundle: {output}")
    files = sources()
    manifest = {
        "protocol": "TATG-MAPPO-FRESH-SEED-PILOT-CLOUD-BUNDLE-V1",
        "purpose": "training only; endpoint evaluation is a separate later interface",
        "training_started": False,
        "evaluation_started": False,
        "automatic_continuation": False,
        "files": {path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in files},
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, path.relative_to(ROOT).as_posix())
        archive.writestr("TATG_PILOT_CLOUD_BUNDLE_MANIFEST.json", json.dumps(manifest, indent=2) + "\n")
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_suffix(output.suffix + ".sha256").write_text(f"{digest}  {output.name}\n", encoding="utf-8")
    print(json.dumps({"bundle": str(output), "sha256": digest, "source_files": len(files), "training_started": False, "evaluation_started": False}, indent=2))


if __name__ == "__main__":
    main()
