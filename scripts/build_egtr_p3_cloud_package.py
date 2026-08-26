"""Build a source-only AutoDL package for the frozen EGTR P3 1M stage."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import zipfile


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = args.output.resolve()
    if output.exists():
        raise FileExistsError(f"refusing to overwrite existing package: {output}")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    branch = subprocess.check_output(["git", "branch", "--show-current"], cwd=root, text=True).strip()
    tape = root / "results" / "development" / "egtr_p3" / "tape" / "tape_manifest.json"
    if not tape.exists():
        raise FileNotFoundError(tape)
    with tempfile.TemporaryDirectory(prefix="egtr_p3_cloud_") as temporary:
        stage = Path(temporary) / "EA_RG_MAPPO_EGTR_P3_DEVELOPMENT"
        stage.mkdir()
        archive = Path(temporary) / "source.zip"
        subprocess.run(["git", "archive", "--format=zip", f"--output={archive}", commit], cwd=root, check=True)
        with zipfile.ZipFile(archive) as bundle:
            bundle.extractall(stage)
        target_tape = stage / "results" / "development" / "egtr_p3" / "tape" / "tape_manifest.json"
        target_tape.parent.mkdir(parents=True, exist_ok=True)
        target_tape.write_bytes(tape.read_bytes())
        provenance = {
            "protocol": "EGTR-P3-CLOUD-PACKAGE-V1", "commit": commit, "branch": branch,
            "authorized_scope": "UTR/DRTP/EGTR x seeds2501/2502/2503, 1M only",
            "tape_namespace": "520000-520099", "tape_hash": json.loads(tape.read_text(encoding="utf-8"))["tape_hash"],
            "no_3m_automatic_continuation": True, "no_heldout": True, "no_canonical": True,
        }
        (stage / "EGTR_P3_CLOUD_PROVENANCE.json").write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
        with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as bundle:
            for path in stage.rglob("*"):
                if path.is_file():
                    bundle.write(path, path.relative_to(stage).as_posix())
    print(json.dumps({"package": str(output), "sha256": sha256(output), "commit": commit,
                      "tape_hash": provenance["tape_hash"]}, indent=2))


if __name__ == "__main__":
    main()
