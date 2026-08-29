"""Build a compact, source-hashed AutoDL package for the frozen Stable-v2 pilot."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile


ROOT = Path(__file__).resolve().parents[1]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def files() -> list[Path]:
    selected = []
    for directory in ("algorithms", "envs"):
        selected.extend((ROOT / directory).rglob("*.py"))
    selected.extend((ROOT / "scripts").glob("*.py"))
    selected.append(ROOT / "scripts" / "launch_drtp_stable_v2_pilot_autodl.sh")
    selected.extend([
        ROOT / "configs" / "drtp_stable_v2_pilot_tape.json",
        ROOT / "configs" / "drtp_stable_v2_pilot_freeze.json",
        ROOT / "tests" / "__init__.py",
        ROOT / "tests" / "test_drtp_stable_v2_kl_guard.py",
        ROOT / "tests" / "test_drtp_stable_v2_pilot_contract.py",
        ROOT / "tests" / "test_tc_sam.py",
        ROOT / "tests" / "test_drtp_utr_q2_formal.py",
    ])
    selected.extend((ROOT / "docs" / "drtp_stable_v2_d1_20260829").glob("*"))
    selected.extend((ROOT / "docs" / "drtp_stable_v2_d2_20260829").glob("*"))
    return sorted({path.resolve() for path in selected if path.is_file()})


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    source_commit = commit()
    output = args.output or ROOT / f"DRTP_STABLE_V2_PILOT_05M_{source_commit[:8]}.zip"
    output = output.resolve()
    if output.exists():
        raise FileExistsError(f"refusing package overwrite: {output}")
    payloads = {}
    for path in files():
        relative = str(path.relative_to(ROOT)).replace("\\", "/")
        payloads[relative] = path.read_bytes()
    payloads["SOURCE_COMMIT.txt"] = (source_commit + "\n").encode("utf-8")
    manifest = {
        "protocol": "DRTP-STABLE-V2-PILOT-CLOUD-PACKAGE-V1",
        "source_commit": source_commit,
        "algorithm_freeze_commit": "3c17bf62",
        "training_authorized_by_package": False,
        "expected_trajectories": 9,
        "max_parallel": 9,
        "environment_steps_per_trajectory": 499968,
        "tape_hash": "25ff4eb5764cd2d590fba719a9c6c43b290ee3466a63075fd7e7184b049c4859",
        "files": {name: sha256_bytes(data) for name, data in sorted(payloads.items())},
    }
    payloads["PACKAGE_MANIFEST.json"] = (json.dumps(manifest, indent=2) + "\n").encode("utf-8")
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(payloads.items()):
            archive.writestr(name, data)
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    checksum = output.with_suffix(output.suffix + ".sha256")
    with checksum.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(f"{digest}  {output.name}\n")
    print(json.dumps({
        "package": str(output),
        "sha256_file": str(checksum),
        "sha256": digest,
        "files": len(payloads),
        "bytes": output.stat().st_size,
        "source_commit": source_commit,
    }, indent=2))


if __name__ == "__main__":
    main()
