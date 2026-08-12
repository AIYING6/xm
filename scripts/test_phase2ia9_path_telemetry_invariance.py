"""P0-style noninterference tests for Phase2IA9 path telemetry."""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from envs.uav_intercept_3d_env import UAVIntercept3DConfig,UAVIntercept3DEnv
FIELDS=('attacker_direct_target_information_t','attacker_fresh_cache_information_t','attacker_cache_source_ids_t','attacker_cache_paths_t','attacker_cache_path_includes_relay1_t','attacker_support_path_relay1_required_t')
def roll():
 e=UAVIntercept3DEnv(UAVIntercept3DConfig(seed=919,target_policy='straight',communication_dropout_prob=.30,message_delay_steps=2,strict_target_sensing=True,agent_target_info_bottleneck=True));e.reset();out=[]
 while not e.done:
  _,_,_,r,d,i=e.step(np.asarray([13,13,13]));
  for f in FIELDS:assert f in i
  assert float(i['attacker_support_path_relay1_required_t'])<=float(i['chain_support_t'])
  out.append((float(np.sum(r)),float(d[0,0]),*(i[f] for f in FIELDS)))
 return out
def main():assert roll()==roll();print('PHASE2IA9_PATH_TELEMETRY_TEST=PASS')
if __name__=='__main__':main()
