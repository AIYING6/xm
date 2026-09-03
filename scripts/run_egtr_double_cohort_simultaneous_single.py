"""Run one of the 30 prospectively frozen simultaneous EGTR trajectories."""
from __future__ import annotations
import argparse,json
from pathlib import Path
import run_egtr_double_cohort_a_single as base
SEEDS=(71011,71012,71013,71014,71015,71021,71022,71023,71024,71025); ARMS=base.ARMS
base.SEEDS=SEEDS;base.PROTOCOL="EGTR-DOUBLE-COHORT-SIMULTANEOUS-10M-TRAINING-V1";base.TAPE_PROTOCOL="EGTR-DOUBLE-COHORT-SIMULTANEOUS-DEVELOPMENT-TAPE-V1"
def main():
 p=argparse.ArgumentParser();p.add_argument("--arm",choices=ARMS,required=True);p.add_argument("--seed",type=int,choices=SEEDS,required=True);p.add_argument("--output-root",type=Path,required=True);p.add_argument("--execute",action="store_true");a=p.parse_args()
 if not a.execute:raise SystemExit("--execute required")
 base.run(a.arm,a.seed,a.output_root);path=a.output_root/"runs"/a.arm/f"seed{a.seed}"/"run_manifest.json";d=json.loads(path.read_text());d["cohort"]="A" if a.seed<71020 else "B";d["simultaneous_dual_cohort"] = True;path.write_text(json.dumps(d,indent=2,default=str)+"\n")
if __name__=="__main__":main()
