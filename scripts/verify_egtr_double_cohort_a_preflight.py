"""Zero-training mechanical gate for authorized Cohort-A execution only."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from algorithms.ri_gmappo.drtp_topology_sampler import EGTRTopologySampler
SEEDS=[71011,71012,71013,71014,71015]; ARMS={"utr_sg":"utr","drtp_sg":"drtp","egtr_sg":"egtr"}
def main():
 p=argparse.ArgumentParser();p.add_argument("--output-root",type=Path,required=True);p.add_argument("--execute",action="store_true");a=p.parse_args()
 if not a.execute:raise SystemExit("--execute required")
 tape=json.loads((a.output_root/"tape"/"tape_manifest.json").read_text())
 checks={"cohort_a_only":SEEDS==[71011,71012,71013,71014,71015],"exact_15_trajectories":len(SEEDS)*len(ARMS)==15,"fresh_tape":tape.get("episode_ids")==list(range(720000,720100)),"training_tape_access_forbidden":tape.get("training_access")=="forbidden","egtr_frozen":EGTRTopologySampler(9001,39063).manifest()["trust_region_after_projection"] is True,"no_existing_runs":not any((a.output_root/"runs"/arm/f"seed{s}").exists() for arm in ARMS for s in SEEDS)}
 if not all(checks.values()):raise RuntimeError(checks)
 d={"protocol":"EGTR-DOUBLE-COHORT-A-PREFLIGHT-V1","status":"PASS","checks":checks,"seeds":SEEDS,"arms":ARMS,"updates":39063,"environment_steps":10000128,"cohort_b_started":False,"evaluation_started":False,"automatic_continuation":False}
 (a.output_root/"EGTR_COHORT_A_PREFLIGHT.json").write_text(json.dumps(d,indent=2)+"\n");print(json.dumps(d,indent=2))
if __name__=="__main__":main()
