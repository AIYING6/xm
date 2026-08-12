"""Static Phase2IA6 executor audit; performs no feasibility episodes."""
from __future__ import annotations
import ast, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results'/'development'/'phase2ia6_prelaunch'

def main()->None:
    source=(ROOT/'scripts'/'run_phase2ia6_task_feasibility.py').read_text(encoding='utf8')
    tree=ast.parse(source)
    legal=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='legal_observation_actions')
    banned={'red_pos','red_speed','red_heading','red_gamma'}
    no_oracle=not any(isinstance(n,ast.Attribute) and n.attr in banned for n in ast.walk(legal))
    checks=[
      ('no_training_or_checkpoint_loader', 'torch' not in source and 'optimizer' not in source and 'checkpoint' not in source),
      ('legal_controller_no_simulator_target_access',no_oracle),
      ('frozen_seed_set', 'SEEDS = (601, 602, 603)' in source),
      ('frozen_controller_pair', 'CONTROLLERS = ("structural_oracle", "legal_observation")' in source),
      ('fail_closed_execute_flag','requires --execute' in source),
      ('overwrite_guard','Refusing to overwrite' in source),
      ('raw_trace_outputs','raw_timestep_chain' in source and 'raw_episode_metrics.csv' in source),
    ]
    rows=[{'gate':name,'status':'PASS' if ok else 'FAIL'} for name,ok in checks]
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'executor_audit.json').write_text(json.dumps({'status':'PASS' if all(x[1] for x in checks) else 'NO-GO','training_started':False,'canonical_data_used':False,'checks':rows},indent=2)+'\n')
    print((OUT/'executor_audit.json').read_text())
if __name__=='__main__':main()
