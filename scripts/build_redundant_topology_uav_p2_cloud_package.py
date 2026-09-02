"""Build the minimal, reproducible cloud package for the frozen P2 gate."""
from __future__ import annotations

import hashlib
from pathlib import Path
import zipfile


ROOT = Path(__file__).resolve().parents[1]
FILES = (
    "algorithms/__init__.py",
    "algorithms/redundant_topology_sg_mappo.py",
    "envs/__init__.py",
    "envs/redundant_topology_uav_env.py",
    "scripts/run_redundant_topology_uav_p2.py",
    "scripts/launch_redundant_topology_uav_p2_autodl.sh",
    "docs/redundant_topology_uav_p2_20260902/P2_FROZEN_CONTRACT.md",
)


def main() -> None:
    name = ROOT / "REDUNDANT_TOPOLOGY_UAV_P2_CLOUD_EXECUTION.zip"
    with zipfile.ZipFile(name, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for relative in FILES:
            path = ROOT / relative
            if not path.exists():
                raise FileNotFoundError(path)
            archive.write(path, relative)
    digest = hashlib.sha256(name.read_bytes()).hexdigest()
    (ROOT / f"{name.name}.sha256").write_text(f"{digest}  {name.name}\n", encoding="utf-8")
    print(name); print(digest)


if __name__ == "__main__":
    main()
