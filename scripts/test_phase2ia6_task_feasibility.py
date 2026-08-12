"""Static and deterministic checks for Phase2IA6 feasibility probes."""
from __future__ import annotations
import ast
from pathlib import Path
from run_phase2ia6_task_feasibility import CONTROLLERS, SEEDS, episode_id, legal_observation_actions
import numpy as np

def main() -> None:
    assert CONTROLLERS == ('structural_oracle','legal_observation') and SEEDS == (601,602,603)
    assert episode_id(1,2,99)==622099
    assert legal_observation_actions(np.zeros((3,34),dtype=np.float32)).shape == (3,)
    tree=ast.parse(Path(__file__).with_name('run_phase2ia6_task_feasibility.py').read_text(encoding='utf8'))
    fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='legal_observation_actions')
    banned={'red_pos','red_speed','red_heading','red_gamma'}
    assert not any(isinstance(n,ast.Attribute) and n.attr in banned for n in ast.walk(fn))
    print('PHASE2IA6_FEASIBILITY_EXECUTOR_TEST=PASS')
if __name__=='__main__': main()
