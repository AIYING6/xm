"""Create a self-contained AutoDL package for the authorized Stage-MSR run."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile


ARMS = ("fl_nominal_expert", "fl_f0_expert")
SEEDS = (1801, 1802)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--specialist-root", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = args.output.resolve()
    if output.exists():
        raise FileExistsError(f"refusing to overwrite existing package: {output}")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    branch = subprocess.check_output(["git", "branch", "--show-current"], cwd=root, text=True).strip()
    with tempfile.TemporaryDirectory(prefix="phase_msr_cloud_") as temporary:
        stage = Path(temporary) / "EA_RG_MAPPO_MSR"
        stage.mkdir()
        archive = Path(temporary) / "source.zip"
        subprocess.run(["git", "archive", "--format=zip", f"--output={archive}", commit], cwd=root, check=True)
        with zipfile.ZipFile(archive) as bundle:
            bundle.extractall(stage)
        copied = []
        for arm in ARMS:
            for seed in SEEDS:
                source = args.specialist_root / arm / f"seed{seed}"
                checkpoint = source / "actor_critic_latest.pt"
                manifest = source / "run_manifest.json"
                if not checkpoint.exists() or not manifest.exists():
                    raise FileNotFoundError(f"missing mature specialist source: {source}")
                destination = stage / "inputs" / "mature_specialists" / arm / f"seed{seed}"
                destination.mkdir(parents=True)
                shutil.copy2(checkpoint, destination / checkpoint.name)
                shutil.copy2(manifest, destination / manifest.name)
                copied.append({
                    "arm": arm, "seed": seed, "source": str(source),
                    "checkpoint_sha256": sha256(checkpoint),
                })
        provenance = {
            "protocol": "PHASE-MSR-CLOUD-PACKAGE-V1", "commit": commit, "branch": branch,
            "specialist_checkpoints": copied,
            "authorized_scope": "Stage MSR only; mixed50_sg seeds1801/1802; no ENMM/OOD/ablation/formal",
        }
        (stage / "MSR_CLOUD_PROVENANCE.json").write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
        with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as bundle:
            for path in stage.rglob("*"):
                if path.is_file():
                    bundle.write(path, path.relative_to(stage).as_posix())
    print(json.dumps({"package": str(output), "sha256": sha256(output), "commit": commit, "branch": branch}, indent=2))


if __name__ == "__main__":
    main()
