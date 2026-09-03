"""Apply unchanged machine gates independently to simultaneous A and B."""
from __future__ import annotations
import argparse,csv,importlib.util,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RULE=ROOT/"results"/"development"/"egtr_double_cohort_preregistration"/"diagnostics"/"egtr_double_cohort_preregistration"/"EGTR_MACHINE_EXECUTABLE_DECISION_RULE.py"
def rule():
 s=importlib.util.spec_from_file_location("egtr_rule",RULE);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 p=argparse.ArgumentParser();p.add_argument("--evaluation-root",type=Path,required=True);p.add_argument("--output-root",type=Path,required=True);p.add_argument("--execute",action="store_true");a=p.parse_args()
 if not a.execute:raise SystemExit("--execute required")
 if not RULE.exists():raise FileNotFoundError("missing P0 machine rule")
 manifest=json.loads((a.evaluation_root/"evaluation_manifest.json").read_text());rows=list(csv.DictReader((a.evaluation_root/"per_seed_condition_summary.csv").open()))
 if not(manifest.get("status")=="completed" and manifest.get("raw_rows")==21000 and manifest.get("cells")==30 and manifest.get("cohorts_separate") is True):raise RuntimeError("invalid final evaluation")
 def metric(arm,seed):
  d={r["condition"]:r for r in rows if r["method"]==arm and int(r["train_seed"])==seed};f=[d[x] for x in ("F0","TE","TL","DS","DL","CP")];return {"J_nominal":float(d["nominal"]["J"]),"J_F0":float(d["F0"]["J"]),"J_pert_mean":statistics.mean(float(x["J"]) for x in f),"J_pert_worst":min(float(x["J"]) for x in f),"collision":statistics.mean(float(x["collision"]) for x in f),"timeout":statistics.mean(float(x["timeout"]) for x in f)}
 r=rule();groups={"A":(71011,71012,71013,71014,71015),"B":(71021,71022,71023,71024,71025)};out=a.output_root/"diagnostics"/"egtr_double_cohort_final_gate";out.mkdir(parents=True,exist_ok=False);dec={}
 for name,seeds in groups.items():dec[name]=r.cohort_decision([{"seed":s,"utr":metric("utr_sg",s),"original":metric("drtp_sg",s),"egtr":metric("egtr_sg",s)} for s in seeds])
 verdict=r.final_decision(dec["A"],dec["B"]);d={"verdict":verdict,"cohort_A":dec["A"],"cohort_B":dec["B"],"pooled_n10_descriptive_only":True,"automatic_continuation":False};(out/"EGTR_DOUBLE_COHORT_GATE_DECISION.json").write_text(json.dumps(d,indent=2)+"\n");(out/"EGTR_DOUBLE_COHORT_FINAL_VERDICT.md").write_text(f"# EGTR fresh double-cohort final verdict\n\n`{verdict}`\n\nCohort A: `{dec['A']['decision']}`; Cohort B: `{dec['B']['decision']}`. No pooled n=10 confirmation was used.\n")
if __name__=="__main__":main()
