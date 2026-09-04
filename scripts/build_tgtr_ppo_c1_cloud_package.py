"""Build the authorized TGTR C1 source package and frozen source assets."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import shutil
import zipfile


ROOT = Path(__file__).resolve().parents[1]
INCLUDE = ("algorithms", "envs", "scripts", "configs", "requirements.txt")


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--assets-output", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, default=ROOT / "results/development/t1_telemetry_native_reference_1m_run1/runs/utr_sg")
    args = parser.parse_args()
    for path in (args.output, args.assets_output):
        if path.exists():
            raise FileExistsError(f"refusing to overwrite {path}")
    required = ("run_manifest.json", "actor_critic_runtime_state_latest.pt")
    for seed in range(2201, 2206):
        if not all((args.source_root / f"seed{seed}" / name).is_file() for name in required):
            raise FileNotFoundError(f"missing source asset seed{seed}")
    with zipfile.ZipFile(args.output, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for item in INCLUDE:
            source = ROOT / item
            if source.is_file():
                archive.write(source, source.relative_to(ROOT).as_posix())
            elif source.is_dir():
                for path in source.rglob("*"):
                    if path.is_file() and "__pycache__" not in path.parts:
                        archive.write(path, path.relative_to(ROOT).as_posix())
    staging = ROOT / ".tgtr_c1_assets_staging"
    if staging.exists():
        raise FileExistsError(f"staging directory exists: {staging}")
    try:
        target = staging / "results/development/t1_telemetry_native_reference_1m_run1/runs/utr_sg"
        for seed in range(2201, 2206):
            destination = target / f"seed{seed}"
            destination.mkdir(parents=True)
            for name in required:
                shutil.copy2(args.source_root / f"seed{seed}" / name, destination / name)
        base = args.assets_output.with_suffix("").with_suffix("")
        shutil.make_archive(str(base), "gztar", staging)
    finally:
        shutil.rmtree(staging, ignore_errors=True)
    for path in (args.output, args.assets_output):
        path.with_suffix(path.suffix + ".sha256").write_text(f"{digest(path)}  {path.name}\n", encoding="utf-8")
    print(args.output)
    print(args.assets_output)


if __name__ == "__main__":
    main()
