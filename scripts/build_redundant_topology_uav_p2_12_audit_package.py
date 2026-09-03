"""Build P2.12 deterministic Scout-assignment audit package."""
from __future__ import annotations

import hashlib
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
FILES = (
    "algorithms/redundant_topology_sg_mappo.py",
    "algorithms/redundant_topology_role_sg_mappo.py",
    "envs/redundant_topology_uav_env.py",
    "scripts/run_redundant_topology_uav_p2_12_scout_assignment_audit.py",
    "docs/redundant_topology_uav_p2_12_20260903/P2_12_SCOUT_ASSIGNMENT_INTERFACE_CONTRACT.md",
)


def main() -> None:
    target = ROOT / "REDUNDANT_TOPOLOGY_UAV_P2_12_SCOUT_ASSIGNMENT_AUDIT.zip"
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        for folder in ("algorithms", "envs", "scripts"):
            archive.writestr(f"{folder}/__init__.py", f'"""P2.12 isolated {folder}."""\n')
        for rel in FILES:
            archive.write(ROOT / rel, rel)
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    (ROOT / f"{target.name}.sha256").write_text(f"{digest}  {target.name}\n", encoding="utf-8")
    print(target)
    print(digest)


if __name__ == "__main__":
    main()
