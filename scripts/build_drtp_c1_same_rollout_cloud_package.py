"""Build a source-only cloud package for the frozen C1 audit.

Frozen runtime checkpoints are deliberately packaged separately as result
assets, so maintained source and large training artifacts never get conflated.
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import shutil
import zipfile


ROOT = Path(__file__).resolve().parents[1]
INCLUDE = (
    "algorithms",
    "envs",
    "scripts",
    "configs",
    "requirements.txt",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--assets-output", type=Path, required=True)
    parser.add_argument(
        "--source-root",
        type=Path,
        default=ROOT / "results" / "development" / "t1_telemetry_native_reference_1m_run1" / "runs" / "utr_sg",
    )
    args = parser.parse_args()
    if args.output.exists() or args.assets_output.exists():
        raise FileExistsError("refusing to overwrite a C1 cloud package or asset archive")
    required = ("actor_critic_runtime_state_latest.pt", "run_manifest.json")
    for seed in range(2201, 2206):
        root = args.source_root / f"seed{seed}"
        if not all((root / name).is_file() for name in required):
            raise FileNotFoundError(f"missing frozen C1 source assets: {root}")

    with zipfile.ZipFile(args.output, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for item in INCLUDE:
            source = ROOT / item
            if source.is_file():
                archive.write(source, source.relative_to(ROOT).as_posix())
            elif source.is_dir():
                for path in source.rglob("*"):
                    if path.is_file() and "__pycache__" not in path.parts:
                        archive.write(path, path.relative_to(ROOT).as_posix())
        archive.writestr("C1_SOURCE_PACKAGE.txt", "Source-only package; extract matching frozen runtime assets separately.\n")

    staging = ROOT / ".c1_cloud_assets_staging"
    if staging.exists():
        raise FileExistsError(f"staging path exists: {staging}")
    try:
        target = staging / "t1_telemetry_native_reference_1m_run1" / "runs" / "utr_sg"
        for seed in range(2201, 2206):
            destination = target / f"seed{seed}"
            destination.mkdir(parents=True, exist_ok=False)
            for name in required:
                shutil.copy2(args.source_root / f"seed{seed}" / name, destination / name)
        if args.assets_output.suffixes[-2:] != [".tar", ".gz"]:
            raise ValueError("assets output must end in .tar.gz")
        asset_base = args.assets_output.with_suffix("").with_suffix("")
        shutil.make_archive(str(asset_base), "gztar", staging)
    finally:
        shutil.rmtree(staging, ignore_errors=True)
    for path in (args.output, args.assets_output):
        path.with_suffix(path.suffix + ".sha256").write_text(
            f"{sha256(path)}  {path.name}\n", encoding="utf-8"
        )
    print(f"source_package={args.output}")
    print(f"assets_package={args.assets_output}")


if __name__ == "__main__":
    main()
