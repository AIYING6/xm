"""Build the P2.8 deterministic-validation cloud package."""
from __future__ import annotations

import hashlib
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
FILES = (
    "envs/redundant_topology_uav_env.py",
    "scripts/run_redundant_topology_uav_p2_8_assignment_validation.py",
    "docs/redundant_topology_uav_p2_8_20260903/P2_8_ASSIGNMENT_OBSERVATION_CONTRACT.md",
)


def main() -> None:
    target = ROOT / "REDUNDANT_TOPOLOGY_UAV_P2_8_ASSIGNMENT_VALIDATION.zip"
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("envs/__init__.py", '"""P2.8 isolated environment."""\n')
        for rel in FILES:
            archive.write(ROOT / rel, rel)
    checksum = hashlib.sha256(target.read_bytes()).hexdigest()
    (ROOT / f"{target.name}.sha256").write_text(f"{checksum}  {target.name}\n", encoding="utf-8")
    print(target)
    print(checksum)


if __name__ == "__main__":
    main()
