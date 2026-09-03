"""Apply the frozen preregistered decision to Cohort A; never starts Cohort B."""
from __future__ import annotations
import argparse,csv,importlib.util,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; RULE=ROOT/"results"/"development"/"egtr_double_cohort_preregistration"/"diagnostics"/"egtr_double_cohort_preregistration"/"EGTR_MACHINE_EXECUTABLE_DECISION_RULE.py"
def load_rule(path):
 s=importlib.util.spec_from_file_location("egtr_rule",path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 p=argparse.ArgumentParser();p.add_argument("--evaluation-root",type=Path,required=True);p.add_argument("--output-root",type=Path,required=True);p.add_argument("--execute",action="store_true");a=p.parse_args()
 if not a.execute:raise SystemExit("--execute required")
 if not RULE.exists():raise FileNotFoundError("P0 machine rule must be included at results/development/egtr_double_cohort_preregistration")
 m=json.loads((a.evaluation_root/"evaluation_manifest.json").read_text()); rows=list(csv.DictReader((a.evaluation_root/"per_seed_condition_summary.csv").open()))
 if not(m.get("status")=="completed" and m.get("raw_rows")==10500 and m.get("cohort")=="A" and m.get("cohort_b_started") is False):raise RuntimeError("invalid Cohort-A evaluation")
 def metric(arm,seed):
  d={r["condition"]:r for r in rows if r["method"]==arm and int(r["train_seed"])==seed};failure=[d[x] for x in ("F0","TE","TL","DS","DL","CP")];return {"J_nominal":float(d["nominal"]["J"]),"J_F0":float(d["F0"]["J"]),"J_pert_mean":statistics.mean(float(x["J"]) for x in failure),"J_pert_worst":min(float(x["J"]) for x in failure),"collision":statistics.mean(float(x["collision"]) for x in failure),"timeout":statistics.mean(float(x["timeout"]) for x in failure)}
 pairs=[{"seed":s,"utr":metric("utr_sg",s),"original":metric("drtp_sg",s),"egtr":metric("egtr_sg",s)} for s in (71011,71012,71013,71014,71015)];rule=load_rule(RULE);d=rule.cohort_decision(pairs);verdict="EGTR_COHORT_A_PASS__COHORT_B_REQUIRES_SEPARATE_AUTHORIZATION" if d["decision"]=="COHORT_PASS" else "EGTR_COHORT_A_FAIL__EGTR_PERMANENTLY_CLOSED";out=a.output_root/"diagnostics"/"egtr_double_cohort_a_gate";out.mkdir(parents=True,exist_ok=False);(out/"EGTR_COHORT_A_GATE_DECISION.json").write_text(json.dumps({"verdict":verdict,"cohort_A":d,"cohort_B_started":False,"automatic_continuation":False},indent=2)+"\n");(out/"EGTR_COHORT_A_FINAL_VERDICT.md").write_text(f"# EGTR Cohort A final verdict\n\n`{verdict}`\n\nCohort B was not started.\n")
if __name__=="__main__":main()
