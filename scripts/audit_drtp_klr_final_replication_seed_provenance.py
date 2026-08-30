"""Record an exact identifier audit for the two pre-training KLR cohorts."""
from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SEEDS=tuple(range(3701,3711))
SKIP={".git","results","tmp","artifacts","archival","output","__pycache__"}
def sha(p:Path)->str: return hashlib.sha256(p.read_bytes()).hexdigest()
def main()->None:
    ap=argparse.ArgumentParser(); ap.add_argument("--output",type=Path,required=True); a=ap.parse_args()
    if a.output.exists(): raise FileExistsError(f"refusing overwrite: {a.output}")
    pattern=re.compile(r"(?i)(?:seed[_-]?|\"seed\"\s*:\s*)("+"|".join(map(str,SEEDS))+r")\b")
    hits=[]; scanned=0
    for p in ROOT.rglob("*"):
        if not p.is_file() or any(part in SKIP for part in p.relative_to(ROOT).parts): continue
        if p.suffix.lower() not in {".py",".json",".md",".sh",".toml",".yaml",".yml",".csv"}: continue
        scanned+=1
        try: text=p.read_text(encoding="utf-8",errors="ignore")
        except OSError: continue
        if pattern.search(text): hits.append(str(p.relative_to(ROOT)).replace("\\","/"))
    payload={"status":"CLEAN" if not hits else "CONTAMINATED","candidate_cohorts":{"A":list(range(3701,3706)),"B":list(range(3706,3711))},"match_rule":pattern.pattern,"files_scanned":scanned,"identifier_hits":hits,"excluded_directories":sorted(SKIP),"zero_training":True}
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); print(json.dumps(payload,ensure_ascii=False,indent=2)); raise SystemExit(0 if not hits else 1)
if __name__=="__main__": main()
