"""Build an isolated V3.1 UTR-only qualification package."""
from __future__ import annotations
import hashlib, zipfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
NAME = "DRTP_6UAV_V31_UTR_LEARNABILITY_PILOT_1M_V1"
FILES = ("algorithms/redundant_topology_sg_mappo.py", "algorithms/sustained_support_role_sg_mappo.py", "envs/redundant_topology_uav_env.py", "envs/sustained_support_topology_uav_env.py", "envs/sustained_support_topology_uav_v31_env.py", "scripts/run_drtp_6uav_v3_q0.py", "scripts/run_drtp_6uav_v3_utr_pilot.py", "scripts/run_drtp_6uav_v31_q0.py", "scripts/run_drtp_6uav_v31_utr_pilot.py", "scripts/verify_drtp_6uav_v31_utr_pilot_preflight.py", "scripts/launch_drtp_6uav_v31_utr_pilot_autodl.sh", "docs/drtp_submission_ready/DRTP_6UAV_V31_UTR_PILOT_CONTRACT.md")
def main() -> None:
    out = ROOT / "artifacts"; out.mkdir(exist_ok=True); archive = out / f"{NAME}.zip"
    if archive.exists(): raise FileExistsError(f"refusing to overwrite {archive}")
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED) as bundle:
        for relative in FILES:
            source = ROOT / relative
            if not source.is_file(): raise FileNotFoundError(source)
            bundle.write(source, Path(NAME) / relative)
    archive.with_suffix(archive.suffix + ".sha256").write_text(f"{hashlib.sha256(archive.read_bytes()).hexdigest()}  {archive.name}\n", encoding="utf-8"); print(archive)
if __name__ == "__main__": main()
