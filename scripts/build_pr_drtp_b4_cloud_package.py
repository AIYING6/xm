"""Build a compact source-hashed AutoDL package for PR-DRTP B4 evaluation."""
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


def selected_files() -> list[Path]:
    selected: list[Path] = []
    for directory in ("algorithms", "envs"):
        selected.extend((ROOT / directory).rglob("*.py"))
    selected.extend((ROOT / "scripts").glob("*.py"))
    selected.extend([
        ROOT / "scripts" / "launch_pr_drtp_b4_autodl.sh",
        ROOT / "configs" / "pr_drtp_b4_feasibility_freeze.json",
        ROOT / "configs" / "pr_drtp_b4_selector_tape.json",
        ROOT / "configs" / "pr_drtp_b4_outcome_tape.json",
        ROOT / "docs" / "drtp_stable_v2_d11_20260830" / "PR_DRTP_B4_FEASIBILITY_CONTRACT.md",
        ROOT / "tests" / "__init__.py",
        ROOT / "tests" / "test_pr_drtp_b4_contract.py",
    ])
    return sorted({path.resolve() for path in selected if path.is_file()})


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists() or output.with_suffix(output.suffix + ".sha256").exists():
        raise FileExistsError(f"refusing package overwrite: {output}")
    source_commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    payloads: dict[str, bytes] = {}
    for path in selected_files():
        payloads[str(path.relative_to(ROOT)).replace("\\", "/")] = path.read_bytes()
    payloads["SOURCE_COMMIT.txt"] = (source_commit + "\n").encode("utf-8")
    freeze = json.loads(
        (ROOT / "configs" / "pr_drtp_b4_feasibility_freeze.json").read_text(encoding="utf-8")
    )
    manifest = {
        "protocol": "PR-DRTP-B4-CLOUD-PACKAGE-V1",
        "source_commit": source_commit,
        "training_authorized": False,
        "expected_checkpoint_assets": 30,
        "expected_selector_episodes": 15 * 7 * 50,
        "expected_outcome_episodes": 30 * 5 * 100,
        "max_workers": 20,
        "selector_tape_sha256": freeze["selector_tape_sha256"],
        "outcome_tape_sha256": freeze["outcome_tape_sha256"],
        "files": {name: sha256_bytes(data) for name, data in sorted(payloads.items())},
    }
    payloads["PACKAGE_MANIFEST.json"] = (
        json.dumps(manifest, indent=2) + "\n"
    ).encode("utf-8")
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, payload in sorted(payloads.items()):
            archive.writestr(name, payload)
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    checksum = output.with_suffix(output.suffix + ".sha256")
    with checksum.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(f"{digest}  {output.name}\n")
    print(json.dumps({
        "package": str(output), "sha256_file": str(checksum), "sha256": digest,
        "files": len(payloads), "bytes": output.stat().st_size,
        "source_commit": source_commit,
    }, indent=2))


if __name__ == "__main__":
    main()
