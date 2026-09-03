"""Build source-only AutoDL package for the separately authorized EGTR Cohort A."""
from __future__ import annotations
import argparse,hashlib,json,subprocess,tempfile,zipfile
from pathlib import Path
def digest(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True);a=p.parse_args();root=Path(__file__).resolve().parents[1];out=a.output.resolve()
 if out.exists():raise FileExistsError(out)
 commit=subprocess.check_output(["git","rev-parse","HEAD"],cwd=root,text=True).strip()
 with tempfile.TemporaryDirectory() as d:
  stage=Path(d)/"EGTR_DOUBLE_COHORT_A";stage.mkdir();archive=Path(d)/"source.zip";subprocess.run(["git","archive","--format=zip",f"--output={archive}",commit],cwd=root,check=True)
  with zipfile.ZipFile(archive) as z:z.extractall(stage)
  provenance={"protocol":"EGTR-DOUBLE-COHORT-A-CLOUD-PACKAGE-V1","commit":commit,"authorized_scope":"Cohort A only: UTR/Original DRTP/EGTR x seeds 71011-71015, 10M final endpoint","cohort_B_authorized":False,"automatic_continuation":False,"training_trajectories":15,"environment_steps_per_trajectory":10000128,"evaluation_tape":"720000-720099 development-only"}
  (stage/"EGTR_DOUBLE_COHORT_A_CLOUD_PROVENANCE.json").write_text(json.dumps(provenance,indent=2)+"\n")
  with zipfile.ZipFile(out,"x",zipfile.ZIP_DEFLATED,compresslevel=6) as z:
   for x in stage.rglob("*"):
    if x.is_file():z.write(x,x.relative_to(stage).as_posix())
 checksum = digest(out)
 out.with_suffix(out.suffix + ".sha256").write_text(f"{checksum}  {out.name}\n", encoding="utf-8")
 print(json.dumps({"package":str(out),"sha256":checksum,"commit":commit},indent=2))
if __name__=="__main__":main()
