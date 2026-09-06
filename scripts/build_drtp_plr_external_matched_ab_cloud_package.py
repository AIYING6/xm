from __future__ import annotations
import hashlib,json,shutil,subprocess,tempfile,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output'/'DRTP_PLR_EXTERNAL_MATCHED_AB_10M_V2_REPAIR1.zip'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def main():
 commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();OUT.parent.mkdir(exist_ok=True)
 with tempfile.TemporaryDirectory() as x:
  x=Path(x);src=x/'s.zip';stage=x/'DRTP_PLR_EXTERNAL_MATCHED_AB_10M_V2_REPAIR1';subprocess.run(['git','archive','--format=zip',f'--output={src}',commit,'--','algorithms','envs','configs/drtp_plr_external_matched_ab_freeze_20260906.json','configs/drtp_stabilization_final_freeze.json','configs/drtp_stabilization_independent_replication_freeze.json','scripts','requirements.txt','README.md'],cwd=ROOT,check=True);stage.mkdir()
  with zipfile.ZipFile(src) as z:z.extractall(stage)
  (stage/'CLOUD_PROVENANCE.json').write_text(json.dumps({'commit':commit,'protocol':'DRTP-PLR-EXTERNAL-MATCHED-AB-10M-V2','new_training':'PLR-style x 10 A/B seeds only','UTR_retraining':False,'DRTP_retraining':False,'A_B_separate':True,'formal_training_started':False},indent=2)+'\n',encoding='utf-8');(stage/'README_AUTODL.txt').write_text('Requires ARCHIVE_A and ARCHIVE_B frozen complete-results archives. It trains PLR only, never UTR/DRTP; it reports A/B separately. Explicit launch authorization remains required.\n',encoding='utf-8');OUT.unlink(missing_ok=True);shutil.make_archive(str(OUT.with_suffix('')),'zip',x,stage.name)
 OUT.with_suffix('.zip.sha256').write_text(f'{sha(OUT)}  {OUT.name}\n',encoding='utf-8');print(json.dumps({'package':str(OUT),'sha256':sha(OUT),'commit':commit},indent=2))
if __name__=='__main__':main()
