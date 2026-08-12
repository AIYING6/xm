"""Static P1 safeguards; no result-producing episodes."""
from __future__ import annotations
import ast
from pathlib import Path
def main():
 p=Path(__file__).with_name('run_phase2ia8_p1_mechanism_probe.py');s=p.read_text(encoding='utf8');t=ast.parse(s)
 assert "SEEDS=(701,702,703)" in s and "support_hold>=2" in s and "failure=step+1" in s
 assert "node_failure_duration_steps=80" in s and "Refusing to overwrite" in s
 f=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='run_one')
 assert not any(isinstance(n,ast.Attribute) and n.attr in {'checkpoint','optimizer'} for n in ast.walk(f))
 print('PHASE2IA8_P1_EXECUTOR_TEST=PASS')
if __name__=='__main__':main()
