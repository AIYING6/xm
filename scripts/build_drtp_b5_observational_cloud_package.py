"""Build the compact, source-hashed B5 observational AutoDL package."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile


ROOT = Path(__file__).resolve().parents[1]


def commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def selected_files() -> list[Path]:
    files: list[Path] = []
    for directory in ("algorithms", "envs"):
        files.extend((ROOT / directory).rglob("*.py"))
    files.extend((ROOT / "scripts").glob("*.py"))
    files.append(ROOT / "scripts" / "launch_drtp_b5_observational_autodl.sh")
    files.extend([
        ROOT / "configs" / "drtp_b5_observational_freeze.json",
        ROOT / "configs" / "drtp_b5_observational_tape.json",
        ROOT / "configs" / "drtp_b5_p0_credit_telemetry_freeze.json",
        ROOT / "docs" / "drtp_b5_p0_20260830" / "B5_P0_DECISION.json",
        ROOT / "docs" / "drtp_b5_p0_20260830" / "B5_P0_TECHNICAL_AUDIT.json",
        ROOT / "docs" / "drtp_b5_p0_20260830" / "TELEMETRY_DICTIONARY.md",
        ROOT / "docs" / "drtp_b5_p1_20260830" / "B5_SEED_PROVENANCE_AUDIT.json",
        ROOT / "docs" / "drtp_b5_p1_20260830" / "B5_P1_READINESS.md",
    ])
    return sorted({path.resolve() for path in files if path.is_file()})


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    source_commit = commit()
    output = (args.output or ROOT / f"DRTP_B5_OBSERVATIONAL_1M_{source_commit[:8]}.zip").resolve()
    if output.exists():
        raise FileExistsError(f"refusing package overwrite: {output}")
    payloads = {}
    for path in selected_files():
        payloads[str(path.relative_to(ROOT)).replace("\\", "/")] = path.read_bytes()
    payloads["SOURCE_COMMIT.txt"] = (source_commit + "\n").encode()
    tape = json.loads((ROOT / "configs" / "drtp_b5_observational_tape.json").read_text(encoding="utf-8"))
    manifest = {
        "protocol": "DRTP-B5-OBSERVATIONAL-CLOUD-PACKAGE-V1",
        "source_commit": source_commit,
        "training_authorized_by_package": False,
        "mainline_a_modified": False,
        "trajectories": 10,
        "maximum_training_concurrency": 10,
        "recommended_evaluation_workers": 20,
        "environment_steps_per_trajectory": 1000192,
        "evaluation_episodes": 20000,
        "tape_hash": tape["tape_hash"],
        "files": {name: hashlib.sha256(data).hexdigest() for name, data in sorted(payloads.items())},
    }
    payloads["PACKAGE_MANIFEST.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(payloads.items()):
            archive.writestr(name, data)
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    checksum = output.with_suffix(output.suffix + ".sha256")
    checksum.write_text(f"{digest}  {output.name}\n", encoding="utf-8")
    print(json.dumps({
        "package": str(output), "checksum": str(checksum), "sha256": digest,
        "files": len(payloads), "bytes": output.stat().st_size, "source_commit": source_commit,
    }, indent=2))


if __name__ == "__main__":
    main()
