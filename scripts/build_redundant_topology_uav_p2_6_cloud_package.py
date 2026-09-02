"""Build the P2.6 zero/near-zero learning correctness-validation package."""
from __future__ import annotations
import hashlib
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parents[1]
FILES=("algorithms/redundant_topology_sg_mappo.py","algorithms/redundant_topology_role_sg_mappo.py","envs/redundant_topology_uav_env.py","scripts/run_redundant_topology_uav_p2_6_validation.py")
def main():
    target=ROOT/"REDUNDANT_TOPOLOGY_UAV_P2_6_CORRECTNESS_PATCH.zip"
    with zipfile.ZipFile(target,"w",zipfile.ZIP_DEFLATED) as z:
        z.writestr("algorithms/__init__.py",'"""P2.6 isolated algorithms."""\n'); z.writestr("envs/__init__.py",'"""P2.6 isolated env."""\n')
        for rel in FILES: z.write(ROOT/rel,rel)
    digest=hashlib.sha256(target.read_bytes()).hexdigest(); (ROOT/f"{target.name}.sha256").write_text(f"{digest}  {target.name}\n",encoding="utf-8")
    print(target);print(digest)
if __name__=="__main__":main()
