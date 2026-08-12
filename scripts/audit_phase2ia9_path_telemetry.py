"""Static noninterference audit for Phase2IA9 telemetry."""
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results'/'development'/'phase2ia9_p0_audit'
def main():
 s=(ROOT/'envs'/'uav_intercept_3d_env.py').read_text(encoding='utf8');names=['attacker_direct_target_information_t','attacker_fresh_cache_information_t','attacker_cache_source_ids_t','attacker_cache_paths_t','attacker_cache_path_includes_relay1_t','attacker_support_path_relay1_required_t'];checks=[{'field':n,'status':'PASS' if s.count(n)==1 else 'FAIL'} for n in names];result={'status':'PASS' if all(x['status']=='PASS' for x in checks) else 'FAIL','checks':checks,'training_started':False};OUT.mkdir(parents=True,exist_ok=True);(OUT/'PATH_TELEMETRY_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
