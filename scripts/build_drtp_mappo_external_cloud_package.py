"""Build a source-only cloud package for the frozen MAPPO-NoGraph reference."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""): value.update(chunk)
    return value.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--output", type=Path, required=True); args = parser.parse_args()
    root, output = Path(__file__).resolve().parents[1], args.output.resolve()
    if output.exists(): raise FileExistsError(f"refusing to overwrite: {output}")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    with tempfile.TemporaryDirectory(prefix="mappo_external_") as temporary:
        temporary, stage, archive = Path(temporary), Path(temporary) / "EA_RG_MAPPO_MAPPO_EXTERNAL", Path(temporary) / "source.zip"
        preflight = Path(temporary) / "preflight.json"
        subprocess.run([sys.executable, "scripts/verify_drtp_mappo_external_contract.py", "--output", str(preflight)], cwd=root, check=True)
        evidence = json.loads(preflight.read_text(encoding="utf-8"))
        if not evidence.get("pass"): raise RuntimeError("failed MAPPO external preflight")
        stage.mkdir(); subprocess.run(["git", "archive", "--format=zip", f"--output={archive}", commit], cwd=root, check=True)
        with zipfile.ZipFile(archive) as source: source.extractall(stage)
        provenance = {"protocol": "DRTP-MAPPO-NOGRAPH-EXTERNAL-REFERENCE-CLOUD-PACKAGE-V1", "source_commit": commit,
                      "authorized_method": "MAPPO-NoGraph", "seeds": [2301, 2302, 2303, 2304, 2305],
                      "budget": "10000128 environment steps per run", "tape_hash": evidence["tape_hash"],
                      "stop_after_package": True, "historical_drtp_utr_verdict_preserved": True}
        (stage / "MAPPO_EXTERNAL_CLOUD_PROVENANCE.json").write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
        (stage / "MAPPO_EXTERNAL_PREFLIGHT_EVIDENCE.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
        with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as target:
            for path in stage.rglob("*"):
                if path.is_file(): target.write(path, path.relative_to(stage).as_posix())
    print(json.dumps({"package": str(output), "sha256": digest(output), "commit": commit}, indent=2))


if __name__ == "__main__": main()
