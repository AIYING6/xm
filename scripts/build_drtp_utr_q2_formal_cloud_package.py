"""Build a source-only AutoDL package for the prospective formal confirmation."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
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
    with tempfile.TemporaryDirectory(prefix="drtp_utr_q2_formal_") as temporary:
        temporary_path = Path(temporary)
        stage = temporary_path / "EA_RG_MAPPO_DRTP_UTR_Q2_FORMAL"
        source = temporary_path / "source.zip"
        preflight = temporary_path / "formal_preflight.json"
        subprocess.run(
            [sys.executable, "scripts/verify_drtp_utr_q2_formal_contract.py", "--output", str(preflight)],
            cwd=root, check=True,
        )
        evidence = json.loads(preflight.read_text(encoding="utf-8"))
        if evidence.get("pass") is not True:
            raise RuntimeError("refusing to package a failed formal preflight")
        stage.mkdir()
        subprocess.run(["git", "archive", "--format=zip", f"--output={source}", commit], cwd=root, check=True)
        with zipfile.ZipFile(source) as bundle:
            bundle.extractall(stage)
        provenance = {
            "protocol": "DRTP-UTR-Q2-FORMAL-CLOUD-PACKAGE-V1",
            "commit": commit,
            "branch": branch,
            "authorized_arms": ["utr_sg", "drtp_sg"],
            "paired_training_seeds": [2301, 2302, 2303, 2304, 2305],
            "budget": "39063 updates / 10000128 environment steps per trajectory",
            "formal_tape_generated_on_launch": "490000-490099",
            "independent_inference_unit": "training_seed",
            "multi_gpu_launch": "GPU_IDS is assigned round-robin across training/evaluation workers",
            "strict_stop": "No algorithm change, canonical run, extra ablation, scalability, or follow-on training is authorized.",
        }
        (stage / "DRTP_UTR_Q2_FORMAL_CLOUD_PROVENANCE.json").write_text(
            json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
        evidence["source_commit"] = commit
        (stage / "DRTP_UTR_Q2_FORMAL_PREFLIGHT_EVIDENCE.json").write_text(
            json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
        with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as bundle:
            for path in stage.rglob("*"):
                if path.is_file():
                    bundle.write(path, path.relative_to(stage).as_posix())
    print(json.dumps({"package": str(output), "sha256": sha256(output),
                      "commit": commit, "branch": branch}, indent=2))


if __name__ == "__main__":
    main()
