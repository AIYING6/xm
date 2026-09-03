"""Record the pre-training scheduling amendment without changing any gate."""
from __future__ import annotations
import argparse,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument("--output-root",type=Path,required=True);p.add_argument("--execute",action="store_true");a=p.parse_args()
 if not a.execute:raise SystemExit("--execute required")
 p0=a.output_root/"diagnostics"/"egtr_double_cohort_preregistration"/"EGTR_PREREGISTRATION_AUDIT.json"
 if not p0.exists():raise FileNotFoundError("run P0 preregistration audit first")
 old=json.loads(p0.read_text())
 if old.get("verdict")!="EGTR_DOUBLE_COHORT_PREREGISTRATION_READY":raise RuntimeError("P0 not ready")
 out=a.output_root/"diagnostics"/"egtr_double_cohort_simultaneous_amendment";out.mkdir(parents=True,exist_ok=False)
 d={"protocol":"EGTR-DOUBLE-COHORT-SIMULTANEOUS-AMENDMENT-V1","verdict":"EGTR_DOUBLE_COHORT_SIMULTANEOUS_AMENDMENT_READY","change":"scheduling_only","cohort_A":[71011,71012,71013,71014,71015],"cohort_B":[71021,71022,71023,71024,71025],"both_start_before_results":True,"all_numeric_gates_unchanged":True,"separate_cohort_decisions_required":True,"pooled_n10_confirmatory_forbidden":True,"automatic_continuation":False,"training_started":False,"evaluation_started":False}
 (out/"EGTR_SIMULTANEOUS_AMENDMENT.json").write_text(json.dumps(d,indent=2)+"\n");(out/"EGTR_SIMULTANEOUS_AMENDMENT_VERDICT.md").write_text("# EGTR simultaneous amendment\n\n`EGTR_DOUBLE_COHORT_SIMULTANEOUS_AMENDMENT_READY`\n\nOnly scheduling changed; no criterion changed.\n");print(json.dumps(d,indent=2))
if __name__=="__main__":main()
