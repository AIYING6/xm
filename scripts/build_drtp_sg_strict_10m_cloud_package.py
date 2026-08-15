"""Package the authorized strict-continuous DRTP 0→10M source controller."""
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
    with tempfile.TemporaryDirectory(prefix="drtp_strict_10m_cloud_") as temporary:
        stage = Path(temporary) / "EA_RG_MAPPO_DRTP_STRICT_10M"
        stage.mkdir()
        archive = Path(temporary) / "source.zip"
        subprocess.run(["git", "archive", "--format=zip", f"--output={archive}", commit], cwd=root, check=True)
        with zipfile.ZipFile(archive) as source:
            source.extractall(stage)
        provenance = {
            "protocol": "DRTP-SG-STRICT-CONTINUOUS-10M-CLOUD-PACKAGE-V1",
            "commit": commit, "branch": branch,
            "authorized_scope": "four from-scratch strict-continuous 0→10M development runs only",
            "arms": ["utr_sg", "drtp_sg"], "seeds": [1901, 1902],
            "runtime_persistence": "enabled from update zero", "warm_restart_used": False,
            "development_tape_generated_on_launch": "420000-420099",
            "held_out_and_canonical_prohibited": True,
        }
        (stage / "DRTP_STRICT_10M_CLOUD_PROVENANCE.json").write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
        with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as bundle:
            for path in stage.rglob("*"):
                if path.is_file():
                    bundle.write(path, path.relative_to(stage).as_posix())
    print(json.dumps({"package": str(output), "sha256": sha256(output), "commit": commit, "branch": branch}, indent=2))


if __name__ == "__main__":
    main()
