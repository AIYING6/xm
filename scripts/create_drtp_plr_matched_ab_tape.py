from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.drtp_plr_matched_ab_contracts import tape
p=argparse.ArgumentParser();p.add_argument('--cohort',choices=('A','B'),required=True);p.add_argument('--output-root',type=Path,required=True);a=p.parse_args();a.output_root.mkdir(parents=True,exist_ok=True);x=tape(a.cohort);q=a.output_root/'tape_manifest.json'
if q.exists() and json.loads(q.read_text(encoding='utf-8'))!=x:raise RuntimeError('existing tape differs')
q.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8');print(json.dumps({'status':'created','cohort':a.cohort,'tape_hash':x['tape_hash']},indent=2))
