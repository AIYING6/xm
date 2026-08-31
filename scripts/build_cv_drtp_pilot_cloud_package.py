"""Build the authorized frozen CV-DRTP pilot package for AutoDL."""
from __future__ import annotations
import hashlib,json,subprocess,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(x): return hashlib.sha256(x).hexdigest()
def main():
 commit=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(); output=ROOT/f"CV_DRTP_PILOT_05M_{commit[:8]}.zip"
 if output.exists(): raise FileExistsError(output)
 paths=[]
 for directory in ("algorithms","envs","scripts"):
  paths.extend((ROOT/directory).rglob("*.py"))
 paths += [ROOT/"scripts/launch_cv_drtp_pilot_autodl.sh",ROOT/"configs/cv_drtp_pilot_freeze.json",ROOT/"configs/cv_drtp_pilot_tape.json",ROOT/"configs/cv_drtp_d0_design_freeze.json",ROOT/"tests/__init__.py",ROOT/"tests/test_cv_drtp_d1.py",ROOT/"tests/test_tc_sam.py",ROOT/"docs/drtp_cv_drtp_d0_20260831/CV_DRTP_D1_LOCAL_TECHNICAL_REPORT.md"]
 payload={str(p.relative_to(ROOT)).replace("\\","/"):p.read_bytes() for p in sorted(set(paths)) if p.is_file()};payload["SOURCE_COMMIT.txt"]=(commit+"\n").encode();manifest={"protocol":"CV-DRTP-PILOT-CLOUD-PACKAGE-V1","source_commit":commit,"authorized_trajectories":30,"max_parallel":9,"environment_steps_per_trajectory":499968,"files":{k:sha(v) for k,v in payload.items()}};payload["PACKAGE_MANIFEST.json"]=(json.dumps(manifest,indent=2)+"\n").encode()
 with zipfile.ZipFile(output,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for name,data in sorted(payload.items()):z.writestr(name,data)
 digest=hashlib.sha256(output.read_bytes()).hexdigest();output.with_suffix(".zip.sha256").write_text(f"{digest}  {output.name}\n");print(json.dumps({"package":str(output),"sha256":digest,"files":len(payload)},indent=2))
if __name__=="__main__":main()
