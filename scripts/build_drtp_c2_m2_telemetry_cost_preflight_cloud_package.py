from __future__ import annotations
import argparse, hashlib, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 if a.output.exists(): raise FileExistsError(a.output)
 with zipfile.ZipFile(a.output,'x',zipfile.ZIP_DEFLATED) as z:
  for name in ('algorithms','envs','scripts','configs','requirements.txt'):
   source=ROOT/name
   if source.is_file(): z.write(source,source.relative_to(ROOT).as_posix())
   elif source.is_dir():
    for item in source.rglob('*'):
     if item.is_file() and '__pycache__' not in item.parts: z.write(item,item.relative_to(ROOT).as_posix())
 digest=hashlib.sha256(a.output.read_bytes()).hexdigest();a.output.with_suffix(a.output.suffix+'.sha256').write_text(f'{digest}  {a.output.name}\n',encoding='utf-8');print(a.output)
if __name__=='__main__': main()
