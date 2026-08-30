"""Apply the frozen KLR P3 gate separately to Cohort A and Cohort B."""
from __future__ import annotations
import argparse,csv,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];FREEZE=ROOT/"configs"/"drtp_klr_final_replication_freeze.json";TAPE=ROOT/"configs"/"drtp_klr_final_replication_tape.json"
ARMS=("utr_sg","drtp_sg","drtp_klr_sg");CONDS=("nominal","F0_44_80","T28_28_80","D120_44_120","C28_120");FAIL=CONDS[1:]
def read(p):
 with p.open(newline="",encoding="utf-8") as h:return list(csv.DictReader(h))
def mean(x):x=list(x);return sum(x)/len(x)
def disp(x):return {"range":max(x)-min(x),"sample_sd":statistics.stdev(x),"mean":mean(x)}
def cell(rows,arm,seed):
 d={r["condition"]:r for r in rows if r["method"]==arm and int(r["train_seed"])==seed}
 if set(d)!=set(CONDS):raise RuntimeError(f"missing cell {arm}/{seed}")
 f=lambda c,k:float(d[c][k]);return {"J_nominal":f("nominal","J"),"J_F0":f("F0_44_80","J"),"J_pert_mean":mean(f(c,"J") for c in FAIL),"J_pert_worst":min(f(c,"J") for c in FAIL),"collision":mean(f(c,"collision") for c in FAIL),"timeout":mean(f(c,"timeout") for c in FAIL),"constraint_violation":max(f(c,"constraint_violation") for c in FAIL)}
def ratio(x,u,e):return x/u if u>0 else 1+(x-u)/max(abs(u),e)
def catastrophic(x,u,e):
 a,b=ratio(x["J_F0"],u["J_F0"],e),ratio(x["J_pert_worst"],u["J_pert_worst"],e);return (a<.7 and b<.85) or (b<.7 and a<.85) or (x["timeout"]-u["timeout"]>.2 and (a<.85 or b<.85))
def guard(root,seeds):
 z=[]
 for s in seeds:
  r=read(root/"runs"/"drtp_klr_sg"/f"seed{s}"/"train_log.csv");
  if len(r)!=1953:raise RuntimeError("incomplete KLR telemetry")
  t=sum(int(float(x["policy_guard_triggered"])) for x in r);a=sum(int(float(x["policy_steps_attempted"])) for x in r)
  if t!=sum(int(float(x["actor_optimizer_state_restored"])) for x in r):raise RuntimeError("rollback telemetry mismatch")
  z.append({"seed":s,"triggers":t,"attempts":a,"rate":t/a if a else 0})
 return z
def cohort(rows,root,seeds,f):
 e,m=float(f["gate"]["epsilon_J"]),float(f["gate"]["downside_improvement_margin"]);r=[]
 for s in seeds:
  u,o,k=(cell(rows,a,s) for a in ARMS);r.append({"seed":s,"G_original":o["J_pert_mean"]-u["J_pert_mean"],"G_klr":k["J_pert_mean"]-u["J_pert_mean"],"klr_minus_original":k["J_pert_mean"]-o["J_pert_mean"],"original_catastrophic":catastrophic(o,u,e),"klr_catastrophic":catastrophic(k,u,e),"original":o,"klr":k,"utr":u})
 og=[x["G_original"] for x in r];kg=[x["G_klr"] for x in r]; od,kd=disp(og),disp(kg);top=[x for x in r if x["G_original"]>e]
 crit={"mean_retention":mean(x["klr"]["J_pert_mean"] for x in r)>=mean(x["original"]["J_pert_mean"] for x in r)-e,"worst_seed_improvement":min(kg)-min(og)>m,"catastrophic_not_increased":sum(x["klr_catastrophic"] for x in r)<=sum(x["original_catastrophic"] for x in r),"range_reduced":kd["range"]<od["range"],"sample_sd_reduced":kd["sample_sd"]<od["sample_sd"],"majority_not_worse":sum(x["klr_minus_original"]>=-e for x in r)>=3,"upper_tail_retained":bool(top) and all(x["klr_minus_original"]>=-e for x in top),"safety":all(x["klr"]["collision"]-x["utr"]["collision"]<=.1 and x["klr"]["timeout"]-x["utr"]["timeout"]<=.1 and x["klr"]["constraint_violation"]<=x["utr"]["constraint_violation"] for x in r)}
 g=guard(root,seeds);crit["intervention_activity"]=sum(x["triggers"] for x in g)>=1 and mean(x["rate"] for x in g)<=.1
 return {"decision":"COHORT_PASS" if all(crit.values()) else "COHORT_FAIL","criteria":crit,"original_dispersion":od,"klr_dispersion":kd,"seed_results":r,"guard":g}
def main():
 p=argparse.ArgumentParser();p.add_argument("--output-root",type=Path,required=True);p.add_argument("--execute",action="store_true");a=p.parse_args()
 if not a.execute:raise SystemExit("--execute required")
 f=json.loads(FREEZE.read_text());t=json.loads(TAPE.read_text());ev=a.output_root/"evaluations"/"final_05m";man=json.loads((ev/"evaluation_manifest.json").read_text()); rows=read(ev/"per_seed_condition_summary.csv")
 if man.get("status")!="completed" or man.get("raw_rows")!=15000 or man.get("tape_hash")!=t["tape_hash"]:raise RuntimeError("invalid P3 evaluation")
 out=a.output_root/"diagnostics"/"klr_final_replication_gate";out.mkdir(parents=True,exist_ok=False);A=cohort(rows,a.output_root,f["cohorts"]["A"],f);B=cohort(rows,a.output_root,f["cohorts"]["B"],f);decision="KLR_FINAL_REPLICATION_GO" if A["decision"]==B["decision"]=="COHORT_PASS" else "KLR_FINAL_REPLICATION_NO_GO_PERMANENTLY_CLOSED";d={"decision":decision,"cohort_A":A,"cohort_B":B,"pooled_n10_descriptive_only":True,"automatic_continuation_started":False,"mainline_a_modified":False}
 (out/"KLR_FINAL_GATE_DECISION.json").write_text(json.dumps(d,indent=2)+"\n")
 for label,x in (("A",A),("B",B)):
  with (out/f"cohort_{label}_seed_results.csv").open("w",newline="",encoding="utf-8") as h:w=csv.DictWriter(h,fieldnames=["seed","G_original","G_klr","klr_minus_original","original_catastrophic","klr_catastrophic"]);w.writeheader();w.writerows([{k:v for k,v in z.items() if k in w.fieldnames} for z in x["seed_results"]])
 text="# KLR Final Replication P3 gate\n\n**Decision:** `"+decision+"`. Cohort A: `"+A["decision"]+"`; Cohort B: `"+B["decision"]+"`.\n\n"+"\n\n".join("## Cohort "+q+"\n```json\n"+json.dumps(x["criteria"],indent=2)+"\n```" for q,x in (("A",A),("B",B)))+"\n\nNo continuation, tuning, rerun, or KLR-v2 was started.\n";(out/"KLR_FINAL_GATE_REPORT.md").write_text(text)
 print(json.dumps({"decision":decision,"report":str(out/"KLR_FINAL_GATE_REPORT.md")},indent=2))
if __name__=="__main__":main()
