"""Build the posthoc-only P4-P0 C-attribution cloud package."""
from __future__ import annotations

import hashlib
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
FILES = (
    "algorithms/redundant_topology_sg_mappo.py", "algorithms/redundant_topology_role_sg_mappo.py", "algorithms/redundant_topology_staged_schedule.py",
    "envs/redundant_topology_uav_env.py", "scripts/run_redundant_topology_uav_p2.py", "scripts/run_redundant_topology_uav_p2r.py",
    "scripts/run_redundant_topology_uav_p3_p2.py", "scripts/run_redundant_topology_uav_p4_p0_c_attribution.py",
    "docs/redundant_topology_uav_p3_20260903/P3_P2_FRESH_PILOT_CONTRACT.md",
    "docs/redundant_topology_uav_p3_20260903/P3_P2_TRAINING_AUTHORIZATION.md",
    "docs/redundant_topology_uav_p3_20260903/P4_P0_C_GROUP_ATTRIBUTION_CONTRACT.md",
)

def main() -> None:
    target = ROOT / "REDUNDANT_TOPOLOGY_UAV_P4_P0_C_ATTRIBUTION_FIX1.zip"
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        for folder in ("algorithms", "envs", "scripts"):
            archive.writestr(f"{folder}/__init__.py", f'"""P4-P0 isolated {folder}."""\n')
        for rel in FILES:
            archive.write(ROOT / rel, rel)
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    (ROOT / f"{target.name}.sha256").write_text(f"{digest}  {target.name}\n", encoding="utf-8")
    print(target); print(digest)

if __name__ == "__main__":
    main()
