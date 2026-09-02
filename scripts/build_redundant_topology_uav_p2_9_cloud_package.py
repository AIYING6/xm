"""Build the frozen P2.9 assigned-observation cloud execution package."""
from __future__ import annotations
import hashlib
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
FILES = (
    "algorithms/redundant_topology_sg_mappo.py", "algorithms/redundant_topology_role_sg_mappo.py",
    "envs/redundant_topology_uav_env.py", "scripts/run_redundant_topology_uav_p2.py",
    "scripts/run_redundant_topology_uav_p2r.py", "scripts/run_redundant_topology_uav_p2_9.py",
    "scripts/verify_redundant_topology_uav_p2_9_preflight.py", "scripts/launch_redundant_topology_uav_p2_9_autodl.sh",
    "docs/redundant_topology_uav_p2_9_20260903/P2_9_ASSIGNED_BASELINE_QUALIFICATION_CONTRACT.md",
)
def main() -> None:
    target = ROOT / "REDUNDANT_TOPOLOGY_UAV_P2_9_CLOUD_EXECUTION.zip"
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        for folder in ("algorithms", "envs", "scripts"): archive.writestr(f"{folder}/__init__.py", f'"""P2.9 isolated {folder}."""\n')
        for rel in FILES: archive.write(ROOT / rel, rel)
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    (ROOT / f"{target.name}.sha256").write_text(f"{digest}  {target.name}\n", encoding="utf-8")
    print(target); print(digest)
if __name__ == "__main__": main()
