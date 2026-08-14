"""Build a self-contained zero-training OGS evaluation package."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile


ROOT = Path(__file__).resolve().parents[1]
MSR = ROOT / "archival/results/phase_msr_cloud_20260814/results/development/phase_msr_mature_shared_policy"
MATURITY = ROOT / "archival/results/phase_fl_maturity_cloud_20260814/results/development/phase_fl_maturity"
CHECKPOINTS = [
    ("msr", "mixed50_sg", 1801, MSR / "runs/mixed50_sg/seed1801/actor_critic_latest.pt"),
    ("msr", "mixed50_sg", 1802, MSR / "runs/mixed50_sg/seed1802/actor_critic_latest.pt"),
    ("maturity", "fl_nominal_expert", 1801, MATURITY / "runs/fl_nominal_expert/seed1801/actor_critic_latest.pt"),
    ("maturity", "fl_nominal_expert", 1802, MATURITY / "runs/fl_nominal_expert/seed1802/actor_critic_latest.pt"),
    ("maturity", "fl_f0_expert", 1801, MATURITY / "runs/fl_f0_expert/seed1801/actor_critic_latest.pt"),
    ("maturity", "fl_f0_expert", 1802, MATURITY / "runs/fl_f0_expert/seed1802/actor_critic_latest.pt"),
]


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
    if args.output.exists():
        raise FileExistsError(args.output)
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    branch = subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip()
    with tempfile.TemporaryDirectory(prefix="post_msr_ogs_") as temporary:
        stage = Path(temporary) / "EA_RG_MAPPO_POST_MSR_OGS"
        stage.mkdir()
        source_zip = Path(temporary) / "source.zip"
        subprocess.run(["git", "archive", "--format=zip", f"--output={source_zip}", commit], cwd=ROOT, check=True)
        with zipfile.ZipFile(source_zip) as bundle:
            bundle.extractall(stage)
        records = []
        for kind, group, seed, source in CHECKPOINTS:
            if not source.exists():
                raise FileNotFoundError(source)
            relative = ("archival/results/phase_msr_cloud_20260814/results/development/phase_msr_mature_shared_policy/"
                        f"runs/{group}/seed{seed}/actor_critic_latest.pt" if kind == "msr" else
                        "archival/results/phase_fl_maturity_cloud_20260814/results/development/phase_fl_maturity/"
                        f"runs/{group}/seed{seed}/actor_critic_latest.pt")
            target = stage / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            records.append({"kind": kind, "group": group, "seed": seed,
                            "sha256": sha256(source), "relative_path": relative})
        provenance = {"protocol": "POST-MSR-OGS-CLOUD-V1", "commit": commit, "branch": branch,
                      "training_started": False, "checkpoints": records}
        (stage / "OGS_CLOUD_PROVENANCE.json").write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
        with zipfile.ZipFile(args.output, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as bundle:
            for path in stage.rglob("*"):
                if path.is_file():
                    bundle.write(path, path.relative_to(stage).as_posix())
    print(json.dumps({"output": str(args.output), "sha256": sha256(args.output), "commit": commit, "branch": branch}, indent=2))


if __name__ == "__main__":
    main()
