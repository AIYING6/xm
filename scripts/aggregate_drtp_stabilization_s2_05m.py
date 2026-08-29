"""Frozen S2 0.5M gate.  It only aggregates existing S1 and S2 data."""
from __future__ import annotations

import argparse, csv, json, math, statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARMS, SEEDS = ("utr_sg", "drtp_sg", "conservative_drtp_sg"), (2901,2902,2903)
CONDITIONS=("nominal","F0_44_80","T28_28_80","D120_44_120","C28_120"); FAILURES=CONDITIONS[1:]

def read(path: Path) -> list[dict[str,str]]:
    with path.open(newline="",encoding="utf-8") as handle: return list(csv.DictReader(handle))
def mean(values: list[float]) -> float: return sum(values)/len(values)
def dispersion(values: list[float]) -> dict[str,float]:
    med=statistics.median(values); return {"mean":mean(values),"median":med,"minimum":min(values),"maximum":max(values),"range":max(values)-min(values),"sample_sd":statistics.stdev(values),"mad":statistics.median(abs(v-med) for v in values)}
def get(summary, arm, seed, condition):
    found=[row for row in summary if row["method"]==arm and int(row["train_seed"])==seed and row["condition"]==condition]
    if len(found)!=1: raise RuntimeError(f"missing {arm}/seed{seed}/{condition}")
    return found[0]
def metrics(summary, arm, seed):
    number=lambda condition,key:float(get(summary,arm,seed,condition)[key])
    return {"J_nominal":number("nominal","J"),"J_F0":number("F0_44_80","J"),"J_T28":number("T28_28_80","J"),"J_D120":number("D120_44_120","J"),"J_C28_120":number("C28_120","J"),"J_pert_mean":mean([number(c,"J") for c in FAILURES]),"J_pert_worst":min(number(c,"J") for c in FAILURES),"collision":mean([number(c,"collision") for c in FAILURES]),"timeout":mean([number(c,"timeout") for c in FAILURES]),"constraint_violation":max(number(c,"constraint_violation") for c in FAILURES)}
def catastrophic(candidate,reference):
    f0=candidate["J_F0"]/reference["J_F0"]; worst=candidate["J_pert_worst"]/reference["J_pert_worst"]
    return (f0<.70 and worst<.85) or (worst<.70 and f0<.85) or (candidate["timeout"]-reference["timeout"]>.20 and (f0<.85 or worst<.85))

def main():
    p=argparse.ArgumentParser();p.add_argument("--output-root",type=Path,required=True);p.add_argument("--s1-root",type=Path,required=True);p.add_argument("--technical-audit",type=Path,required=True);p.add_argument("--execute",action="store_true");a=p.parse_args()
    if not a.execute: raise SystemExit("--execute required")
    audit=json.loads(a.technical_audit.read_text(encoding="utf-8"))
    if audit.get("status")!="PASS": raise RuntimeError("S2_TECHNICAL_NOT_READY")
    freeze=json.loads((ROOT/"configs/drtp_stabilization_s0_freeze.json").read_text(encoding="utf-8")); tape=json.loads((ROOT/"configs/drtp_stabilization_s1_development_tape.json").read_text(encoding="utf-8"))
    evaluation=a.output_root/"evaluations"/"final_05m"; manifest=json.loads((evaluation/"evaluation_manifest.json").read_text(encoding="utf-8")); raw,summary=read(evaluation/"raw_episode_metrics.csv"),read(evaluation/"per_seed_condition_summary.csv")
    expected=len(ARMS)*len(SEEDS)*len(CONDITIONS)*100
    if manifest.get("status")!="completed" or len(raw)!=expected or manifest.get("raw_rows")!=expected or manifest.get("tape_hash")!=tape["tape_hash"]: raise RuntimeError("S2 technical invalid evaluation")
    report=a.output_root/"diagnostics"/"s2_05m_gate"
    # The launcher deliberately writes the zero-training technical audit here
    # before training.  It is the sole admissible pre-existing material; a
    # gate result is never overwritten on a rerun.
    protected={"S2_05M_GATE_REPORT.md","S2_05M_GATE_DECISION.json","S2_SEED_LEVEL_RESULTS.csv","S2_SAMPLER_TELEMETRY_SUMMARY.csv","S2_INTEGRITY_MANIFEST.json"}
    if report.exists() and any(path.name in protected for path in report.iterdir()):
        raise FileExistsError(f"refusing to overwrite existing S2 gate: {report}")
    report.mkdir(parents=True,exist_ok=True)
    cells={arm:{seed:metrics(summary,arm,seed) for seed in SEEDS} for arm in ARMS}; rows=[]
    for seed in SEEDS:
        utr,original,s2=cells["utr_sg"][seed],cells["drtp_sg"][seed],cells["conservative_drtp_sg"][seed]
        rows.append({"seed":seed,**{f"utr_{k}":v for k,v in utr.items()},**{f"drtp_{k}":v for k,v in original.items()},**{f"s2_{k}":v for k,v in s2.items()},"G_drtp":original["J_pert_mean"]-utr["J_pert_mean"],"G_s2":s2["J_pert_mean"]-utr["J_pert_mean"],"s2_minus_drtp":s2["J_pert_mean"]-original["J_pert_mean"],"drtp_catastrophic":catastrophic(original,utr),"s2_catastrophic":catastrophic(s2,utr)})
    epsilon=float(freeze["epsilon_J"]); margin=float(freeze["practical_downside_improvement_margin"]); g0=[row["G_drtp"] for row in rows]; g2=[row["G_s2"] for row in rows]; d0,d2=dispersion(g0),dispersion(g2)
    advantage=mean([cells["conservative_drtp_sg"][s]["J_pert_mean"] for s in SEEDS]) >= mean([cells["drtp_sg"][s]["J_pert_mean"] for s in SEEDS])-epsilon
    downside=min(g2)-min(g0)>margin and sum(row["s2_catastrophic"] for row in rows)<=sum(row["drtp_catastrophic"] for row in rows)
    reliability=all(d2[key]<d0[key] for key in ("range","sample_sd","mad")); upper=[row for row in rows if row["G_drtp"]>epsilon]; upper_ok=bool(upper) and all(row["s2_minus_drtp"]>=-epsilon for row in upper)
    safety_details=[]
    for seed in SEEDS:
        for condition in FAILURES:
            c,r=get(summary,"conservative_drtp_sg",seed,condition),get(summary,"utr_sg",seed,condition); safety_details.append({"seed":seed,"condition":condition,"collision_difference":float(c["collision"])-float(r["collision"]),"timeout_difference":float(c["timeout"])-float(r["timeout"]),"constraint_violation":float(c["constraint_violation"])})
    safety=mean([cells["conservative_drtp_sg"][s]["collision"]-cells["utr_sg"][s]["collision"] for s in SEEDS])<=.05 and mean([cells["conservative_drtp_sg"][s]["timeout"]-cells["utr_sg"][s]["timeout"] for s in SEEDS])<=.05 and all(row["collision_difference"]<=.10 and row["timeout_difference"]<=.10 and row["constraint_violation"]==0 for row in safety_details)
    criteria={"advantage_retention":advantage,"downside_protection":downside,"seed_reliability":reliability,"upper_tail_retention":upper_ok,"upper_tail_assessable":bool(upper),"safety":safety}; failures=[]
    if not advantage: failures.append("advantage_retention_failed")
    if not downside: failures.append("downside_protection_failed")
    if not reliability: failures.append("seed_reliability_failed")
    if not upper_ok: failures.append("upper_tail_retention_failed_or_unassessable")
    if not safety: failures.append("safety_failed")
    decision="S2_EARLY_GO" if not failures else "S2_NO_GO / STABILIZATION_LINE_CLOSED"
    with (report/"S2_SEED_LEVEL_RESULTS.csv").open("w",newline="",encoding="utf-8") as h: w=csv.DictWriter(h,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    with (report/"s2_safety_evidence.csv").open("w",newline="",encoding="utf-8") as h: w=csv.DictWriter(h,fieldnames=list(safety_details[0]));w.writeheader();w.writerows(safety_details)
    # Read-only sampler telemetry summary; no values are reused for tuning.
    sampler=[]
    for seed in SEEDS:
        log=read(a.output_root/"runs"/"conservative_drtp_sg"/f"seed{seed}"/"drtp_topology_sampler_log.csv"); updates=[row for row in log if row["record_type"]=="weight_update" and str(row["adapted"]).lower()=="true"]
        sampler.append({"seed":seed,"adaptation_boundaries":len(updates),"tr_activation_rate":mean([float(str(row["trust_region_active"]).lower()=="true") for row in updates]),"mean_pre_tr_l1":mean([float(row["pre_tr_l1"]) for row in updates]),"mean_final_l1":mean([float(row["q_step_l1"]) for row in updates]),"mean_q_distance_uniform":mean([sum(abs(float(row[f"q_{g}"])-1/6) for g in ("F0","TE","TL","DS","DL","CP")) for row in updates]),"mean_anchor_shift":mean([sum(abs(float(row[f"anchored_target_{g}"])-float(row[f"projected_target_{g}"])) for g in ("F0","TE","TL","DS","DL","CP")) for row in updates])})
    with (report/"S2_SAMPLER_TELEMETRY_SUMMARY.csv").open("w",newline="",encoding="utf-8") as h: w=csv.DictWriter(h,fieldnames=list(sampler[0]));w.writeheader();w.writerows(sampler)
    integrity={"protocol":"DRTP-STABILIZATION-S2-INTEGRITY-V1","s1_gate":"S1_NO_GO","s2_runs":3,"reused_baselines":6,"raw_rows":len(raw),"tape_hash":tape["tape_hash"],"technical_audit":str(a.technical_audit),"no_continuation_started":True,"no_s3_authorized":True}
    (report/"S2_INTEGRITY_MANIFEST.json").write_text(json.dumps(integrity,indent=2)+"\n",encoding="utf-8")
    result={"decision":decision,"criteria":criteria,"failures":failures,"epsilon_J":epsilon,"downside_margin":margin,"seed_results":rows,"original_drtp_dispersion":d0,"s2_dispersion":d2,"automatic_follow_on_started":False,"stabilization_line_closed":bool(failures)}
    (report/"S2_05M_GATE_DECISION.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    lines=["# S2 0.5M frozen gate report","",f"**Decision:** `{decision}`.","",f"Raw records: `{len(raw)}/{expected}`; S0 delta: `{freeze['delta_q_l1']}`; anchor: `0.20`; tape: `{tape['tape_hash']}`.","","| Seed | G original | G S2 | S2−original | Original catastrophic | S2 catastrophic |","|---:|---:|---:|---:|---|---|"]
    lines += [f"| {r['seed']} | {r['G_drtp']:.3f} | {r['G_s2']:.3f} | {r['s2_minus_drtp']:.3f} | {r['drtp_catastrophic']} | {r['s2_catastrophic']} |" for r in rows]
    lines += ["","| Criterion | Result |","|---|---|",*[f"| {k} | `{v}` |" for k,v in criteria.items()],"",f"Original dispersion: `{json.dumps(d0)}`.",f"S2 dispersion: `{json.dumps(d2)}`.",f"NO-GO reasons: `{', '.join(failures) if failures else 'none'}`.","","No S2 continuation, parameter change, or third stabilization candidate was started."]
    (report/"S2_05M_GATE_REPORT.md").write_text("\n".join(lines)+"\n",encoding="utf-8");print(json.dumps({"decision":decision,"report":str(report/"S2_05M_GATE_REPORT.md")},indent=2))
if __name__=="__main__": main()
