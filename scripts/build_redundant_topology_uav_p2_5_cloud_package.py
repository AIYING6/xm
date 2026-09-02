"""Build a read-only P2.5 package; it contains no learner training launcher."""
from __future__ import annotations
import hashlib
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parents[1]
FILES=("scripts/run_redundant_topology_uav_p2_5_forensic.py", "algorithms/redundant_topology_sg_mappo.py", "envs/redundant_topology_uav_env.py")
def main():
    target=ROOT/"REDUNDANT_TOPOLOGY_UAV_P2_5_FORENSIC.zip"
    with zipfile.ZipFile(target,"w",zipfile.ZIP_DEFLATED) as z:
        z.writestr("envs/__init__.py", '"""P2.5 isolated environment package."""\n')
        z.writestr("algorithms/__init__.py", '"""P2.5 isolated algorithm package."""\n')
        for relative in FILES: z.write(ROOT/relative,relative)
    digest=hashlib.sha256(target.read_bytes()).hexdigest()
    (ROOT/f"{target.name}.sha256").write_text(f"{digest}  {target.name}\n",encoding="utf-8")
    print(target); print(digest)
if __name__=="__main__": main()
