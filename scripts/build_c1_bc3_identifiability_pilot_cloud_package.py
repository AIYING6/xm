"""Build a self-contained cloud package for the frozen C1 BC3 short pilot."""
from __future__ import annotations

import hashlib
import shutil
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = "C1_BC3_IDENTIFIABILITY_PILOT_V1"
FILES = (
    "algorithms/__init__.py",
    "algorithms/c1_bc3_mappo.py",
    "configs/c1_bc3_identifiability_pilot_freeze_20260911.json",
    "envs/__init__.py",
    "envs/c1_lbf_masked_adapter.py",
    "requirements-c1-lbf.txt",
    "scripts/aggregate_c1_bc3_identifiability_pilot.py",
    "scripts/launch_c1_bc3_identifiability_pilot_autodl.sh",
    "scripts/run_c1_bc3_identifiability_pilot.py",
    "scripts/verify_c1_bc3_identifiability_preflight.py",
)

README = """# C1 BC3 identifiability pilot

This package runs exactly 12 short trajectories: four matched arms over three
frozen seeds. It starts with a static/synthetic information-boundary preflight,
then trains all arms, performs a fixed endpoint evaluation and emits a human
review report. A complete run never launches a longer experiment automatically.

Install the isolated optional benchmark dependencies with:

    python -m pip install -r requirements-c1-lbf.txt

Launch with `bash scripts/launch_c1_bc3_identifiability_pilot_autodl.sh` after
setting `OUTPUT_ROOT` to a new path. Results are diagnostic pilot evidence only,
not a paper or formal performance claim.
"""


def main() -> None:
    destination = ROOT / f"{PACKAGE}.zip"
    if destination.exists():
        raise FileExistsError(f"refusing to overwrite {destination}")
    for relative in FILES:
        if not (ROOT / relative).is_file():
            raise FileNotFoundError(relative)
    with tempfile.TemporaryDirectory(prefix="c1_bc3_") as temporary:
        temporary_root = Path(temporary)
        package_root = temporary_root / PACKAGE
        for relative in FILES:
            target = package_root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / relative, target)
        (package_root / "README.md").write_text(README, encoding="utf-8")
        with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for path in sorted(package_root.rglob("*")):
                if path.is_file():
                    archive.write(path, path.relative_to(temporary_root))
    digest = hashlib.sha256(destination.read_bytes()).hexdigest()
    destination.with_suffix(".zip.sha256").write_text(f"{digest}  {destination.name}\n", encoding="ascii")
    print(destination)
    print(digest)


if __name__ == "__main__":
    main()
