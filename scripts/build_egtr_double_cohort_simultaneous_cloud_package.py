"""Build the user-authorized simultaneous 30-trajectory EGTR package."""
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
  stage=Path(d)/"EGTR_DOUBLE_COHORT_SIMULTANEOUS";stage.mkdir();archive=Path(d)/"src.zip";subprocess.run(["git","archive","--format=zip",f"--output={archive}",commit],cwd=root,check=True)
  with zipfile.ZipFile(archive) as z:z.extractall(stage)
  x={"protocol":"EGTR-DOUBLE-COHORT-SIMULTANEOUS-CLOUD-PACKAGE-V1","commit":commit,"authorized_scope":"UTR/Original DRTP/EGTR x Cohort A 71011-71015 and Cohort B 71021-71025, 10M endpoint","trajectories":30,"separate_cohort_gates":True,"pooled_n10_confirmatory_forbidden":True,"automatic_continuation":False}
  (stage/"EGTR_SIMULTANEOUS_CLOUD_PROVENANCE.json").write_text(json.dumps(x,indent=2)+"\n")
  with zipfile.ZipFile(out,"x",zipfile.ZIP_DEFLATED,compresslevel=6) as z:
   for f in stage.rglob("*"):
    if f.is_file():z.write(f,f.relative_to(stage).as_posix())
 checksum=digest(out);out.with_suffix(out.suffix+".sha256").write_text(f"{checksum}  {out.name}\n");print(json.dumps({"package":str(out),"sha256":checksum,"commit":commit},indent=2))
if __name__=="__main__":main()
