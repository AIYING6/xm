"""Build a cloud package for P2-R zero-training preflight only."""
from __future__ import annotations

import hashlib
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
FILES = (
    "algorithms/redundant_topology_sg_mappo.py",
    "algorithms/redundant_topology_role_sg_mappo.py",
    "envs/redundant_topology_uav_env.py",
    "scripts/verify_redundant_topology_uav_p2r_preflight.py",
    "docs/redundant_topology_uav_p2r_20260903/P2_R_REQUALIFICATION_CONTRACT.md",
)


def main() -> None:
    target = ROOT / "REDUNDANT_TOPOLOGY_UAV_P2R_PREFLIGHT.zip"
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("algorithms/__init__.py", '"""P2-R isolated algorithms."""\n')
        archive.writestr("envs/__init__.py", '"""P2-R isolated environment."""\n')
        for rel in FILES:
            archive.write(ROOT / rel, rel)
    checksum = hashlib.sha256(target.read_bytes()).hexdigest()
    (ROOT / f"{target.name}.sha256").write_text(f"{checksum}  {target.name}\n", encoding="utf-8")
    print(target)
    print(checksum)


if __name__ == "__main__":
    main()
