"""Build the P2.11 read-only role-credit forensic cloud package."""
from __future__ import annotations

import hashlib
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
FILES = (
    "algorithms/redundant_topology_sg_mappo.py",
    "algorithms/redundant_topology_role_sg_mappo.py",
    "envs/redundant_topology_uav_env.py",
    "scripts/run_redundant_topology_uav_p2.py",
    "scripts/run_redundant_topology_uav_p2r.py",
    "scripts/run_redundant_topology_uav_p2_9.py",
    "scripts/run_redundant_topology_uav_p2_11_role_credit_forensic.py",
    "docs/redundant_topology_uav_p2_11_20260903/P2_11_ROLE_CREDIT_ACTION_TIMING_CONTRACT.md",
)


def main() -> None:
    target = ROOT / "REDUNDANT_TOPOLOGY_UAV_P2_11_ROLE_CREDIT_FORENSIC.zip"
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        for folder in ("algorithms", "envs", "scripts"):
            archive.writestr(f"{folder}/__init__.py", f'"""P2.11 isolated {folder}."""\n')
        for rel in FILES:
            archive.write(ROOT / rel, rel)
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    (ROOT / f"{target.name}.sha256").write_text(f"{digest}  {target.name}\n", encoding="utf-8")
    print(target)
    print(digest)


if __name__ == "__main__":
    main()
