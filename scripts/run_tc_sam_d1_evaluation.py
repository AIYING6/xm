"""Final-checkpoint TC-SAM-D1 evaluation on the frozen T1 development tape."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from scripts.create_t1_telemetry_native_tape import EPISODES, TAPE_START  # noqa
from scripts.run_t1_telemetry_native_single import ENVIRONMENT_STEPS, SEEDS  # noqa
from scripts.telemetry_native_t0 import FailureScenario  # noqa
from scripts.telemetry_native_t1 import write_checkpoint_evidence_bundle  # noqa
T1_HASH="3de6e4fabf07bb76fe7c9271b3f3e70a5910262581ac14b3de162533ef83e6c3"
def sha256(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for x in iter(lambda:f.read(1048576),b''): h.update(x)
 return h.hexdigest()
def main():
 p=argparse.ArgumentParser(); p.add_argument('--output-root',type=Path,required=True);p.add_argument('--t1-root',type=Path,required=True);p.add_argument('--device',choices=('cpu','cuda'),default='cpu');p.add_argument('--execute',action='store_true');a=p.parse_args()
 if not a.execute: raise SystemExit('explicit --execute required')
 tape=json.loads((a.t1_root/'tape_manifest.json').read_text())
 if tape.get('tape_hash')!=T1_HASH or tape.get('episode_ids')!=list(range(TAPE_START,TAPE_START+EPISODES)): raise RuntimeError('invalid frozen T1 tape')
 root=a.output_root/'evaluations'/'final_1m'
 if root.exists() and any(root.iterdir()): raise FileExistsError(f'refusing overwrite: {root}')
 plans=[]
 for c in tape['conditions']:
  scenario=FailureScenario(str(c['name']),int(c['failed_blue_agent']),int(c['start_step']),int(c['duration_steps']))
  plans += [(int(i),scenario) for i in tape['episode_ids']]
 entries=[]
 for done,seed in enumerate(SEEDS,1):
  run=a.output_root/'runs'/'tc_sam_utr'/f'seed{seed}'; m=json.loads((run/'run_manifest.json').read_text()); ckpt=run/'actor_critic_latest.pt'
  required={'status':'completed','method':'TC-SAM-UTR','parameter_count':116728,'graph_encoder':'single','actor_gradient_mode':'utr','sam_enabled':True,'sam_rho':.05,'sam_epsilon':1e-12,'environment_steps':ENVIRONMENT_STEPS,'from_scratch':True,'strict_continuous':True,'final_checkpoint_only':True}
  if any(m.get(k)!=v for k,v in required.items()) or not ckpt.exists() or sha256(ckpt)!=m.get('final_checkpoint_sha256'): raise RuntimeError(f'contract violation seed{seed}')
  bundle=write_checkpoint_evidence_bundle(root/'tc_sam_utr'/f'seed{seed}',ckpt,construction_seed=seed,plans=plans,graph_encoder='single',device=a.device)
  entries.append({'seed':seed,'checkpoint_sha256':m['final_checkpoint_sha256'],'bundle_manifest':bundle}); print(f'TC-SAM D1 evaluation progress {done}/{len(SEEDS)} ({100*done/len(SEEDS):.2f}%)',flush=True)
 root.mkdir(parents=True,exist_ok=True); (root/'evaluation_manifest.json').write_text(json.dumps({'protocol':'TC-SAM-D1-FINAL-EVALUATION-V1','status':'completed','tape_hash':T1_HASH,'entries':entries},indent=2)+'\n')
if __name__=='__main__': main()
