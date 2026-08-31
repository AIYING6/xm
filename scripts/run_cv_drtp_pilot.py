"""Frozen two-cohort CV-DRTP 0.5M pilot: train, evaluate, then gate."""
from __future__ import annotations
import argparse, csv, hashlib, json, multiprocessing as mp, statistics, subprocess, sys, time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import replace
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]; sys.path[:0]=[str(ROOT),str(ROOT/"scripts")]
from algorithms.ri_gmappo.simple_ri_gmappo import train_ri_gmappo
import run_drtp_sg_development_evaluation as evaluation
import run_drtp_sg_strict_10m_single as strict
FREEZE=ROOT/"configs"/"cv_drtp_pilot_freeze.json"; TAPE=ROOT/"configs"/"cv_drtp_pilot_tape.json"
ARMS={"utr_sg":("utr",False),"drtp_sg":("drtp",False),"cv_drtp_sg":("drtp",True)}; SEEDS=tuple(range(4301,4311)); CONDS=("nominal","F0_44_80","T28_28_80","D120_44_120","C28_120"); FAIL=CONDS[1:]
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def tape_hash(): return hashlib.sha256(json.dumps(json.loads(TAPE.read_text()),sort_keys=True,separators=(",",":")).encode()).hexdigest()
def cohort(seed): return "A" if seed<=4305 else "B"
def config(arm,seed,out):
    sampler,enabled=ARMS[arm]; base=strict.training_config("utr_sg",strict.SEEDS[0],out)
    return replace(base,seed=seed,updates=1953,save_interval=976,milestone_updates={976:"250k",1953:"500k"},out_dir=str(out),drtp_sampler_mode=sampler,drtp_sampler_seed=seed,drtp_sampler_total_updates=1953,counterfactual_critic_enabled=enabled,runtime_state_checkpointing=True,runtime_state_save_interval=976,evaluation_enabled=False)
def train(a):
    out=a.output_root/"runs"/a.arm/f"seed{a.seed}"; f=json.loads(FREEZE.read_text())
    if not a.execute or not f["authorization"]["training_authorized"]: raise RuntimeError("explicit frozen authorization required")
    if out.exists(): raise FileExistsError(f"refusing rerun/overwrite: {out}")
    out.mkdir(parents=True); c=config(a.arm,a.seed,out); manifest={"protocol":"CV-DRTP-PILOT-P2-V1","status":"running","arm":a.arm,"seed":a.seed,"cohort":cohort(a.seed),"environment_steps":499968,"updates":1953,"counterfactual_critic_enabled":c.counterfactual_critic_enabled,"sampler":c.drtp_sampler_mode,"freeze_sha256":sha(FREEZE),"tape_sha256":sha(TAPE),"tape_hash":tape_hash(),"checkpoint_promotion":False,"early_stopping":False,"automatic_continuation":False,"started_at":time.time()}; (out/"run_manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    try:
        train_ri_gmappo(c); required=[out/"actor_critic_milestone_250k.pt",out/"actor_critic_milestone_500k.pt",out/"actor_critic_runtime_state_milestone_500k.pt",out/"train_log.csv",out/"drtp_topology_sampler_log.csv"]
        if not all(p.exists() for p in required): raise RuntimeError("missing frozen trajectory artifact")
        manifest["status"]="completed";manifest["completed_at"]=time.time()
    except BaseException as e:
        manifest["status"]="failed";manifest["error"]=repr(e);(out/"run_manifest.json").write_text(json.dumps(manifest,indent=2)+"\n");raise
    (out/"run_manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
def avg(rows,key): return sum(float(r[key]) for r in rows)/len(rows)
def evaluate(a):
    tape=json.loads(TAPE.read_text()); out=a.output_root/"evaluations"/"final_05m"
    if not a.execute or out.exists(): raise RuntimeError("evaluation requires --execute and new output")
    out.mkdir(parents=True); tasks=[]
    for arm in ARMS:
      for seed in SEEDS:
       run=a.output_root/"runs"/arm/f"seed{seed}"; m=json.loads((run/"run_manifest.json").read_text())
       if m.get("status")!="completed" or m.get("tape_hash")!=tape_hash(): raise RuntimeError(f"invalid run {run}")
       for condition in tape["conditions"]: tasks.append((arm,seed,str(run/"actor_critic_milestone_500k.pt"),"500k",tape["episode_ids"],[condition],tape_hash()))
    rows=[]; done=0; total=len(tasks)*100; print(f"CV-DRTP pilot evaluation: workers={a.workers}, cells={len(tasks)}, episodes={total}",flush=True)
    with ProcessPoolExecutor(max_workers=a.workers,mp_context=mp.get_context("spawn")) as executor:
      futures=[executor.submit(evaluation.evaluate_cell,t) for t in tasks]
      for future in as_completed(futures): rows+=future.result();done=len(rows);print(f"CV-DRTP pilot evaluation progress {done}/{total} ({100*done/total:.2f}%)",flush=True)
    if len(rows)!=total: raise RuntimeError("incomplete evaluation")
    rows.sort(key=lambda r:(r["method"],int(r["train_seed"]),r["topology_condition"],int(r["development_episode_id"])))
    with (out/"raw_episode_metrics.csv").open("w",newline="",encoding="utf-8") as h: w=csv.DictWriter(h,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    summaries=[]
    for arm in ARMS:
      for seed in SEEDS:
       for cond in tape["conditions"]:
        group=[r for r in rows if r["method"]==arm and int(r["train_seed"])==seed and r["topology_condition"]==cond["name"]]
        summaries.append({"method":arm,"train_seed":seed,"condition":cond["name"],**{k:avg(group,k) for k in ("J","collision","timeout","constraint_violation")}})
    with (out/"per_seed_condition_summary.csv").open("w",newline="",encoding="utf-8") as h:w=csv.DictWriter(h,fieldnames=list(summaries[0]));w.writeheader();w.writerows(summaries)
    (out/"evaluation_manifest.json").write_text(json.dumps({"status":"completed","raw_rows":len(rows),"workers":a.workers,"tape_hash":tape_hash(),"checkpoint_promotion":False},indent=2)+"\n")
def metrics(rows,arm,seed):
 d={r["condition"]:r for r in rows if r["method"]==arm and int(r["train_seed"])==seed}
 if set(d)!=set(CONDS): raise RuntimeError("missing condition")
 j=lambda c:float(d[c]["J"]); return {"J_pert_mean":sum(j(c) for c in FAIL)/4,"J_F0":j("F0_44_80"),"J_pert_worst":min(j(c) for c in FAIL),"collision":sum(float(d[c]["collision"]) for c in FAIL)/4,"timeout":sum(float(d[c]["timeout"]) for c in FAIL)/4,"constraint":max(float(d[c]["constraint_violation"]) for c in FAIL)}
def catastrophic(x,u): return x["J_pert_worst"]<.7*u["J_pert_worst"] and x["J_F0"]<.7*u["J_F0"]
def aggregate(a):
    if not a.execute: raise RuntimeError("--execute required")
    out=a.output_root/"diagnostics"/"cv_drtp_pilot_gate"; ev=a.output_root/"evaluations"/"final_05m"; f=json.loads(FREEZE.read_text()); m=json.loads((ev/"evaluation_manifest.json").read_text())
    if out.exists() or m.get("status")!="completed" or m.get("raw_rows")!=15000 or m.get("tape_hash")!=tape_hash(): raise RuntimeError("invalid or non-new aggregate")
    with (ev/"per_seed_condition_summary.csv").open() as h: rows=list(csv.DictReader(h))
    def one(seeds):
      z=[]
      for seed in seeds:
       u,o,c=(metrics(rows,arm,seed) for arm in ARMS); z.append({"seed":seed,"gain_original":o["J_pert_mean"]-u["J_pert_mean"],"gain_cv":c["J_pert_mean"]-u["J_pert_mean"],"cv_minus_original":c["J_pert_mean"]-o["J_pert_mean"],"original_catastrophic":catastrophic(o,u),"cv_catastrophic":catastrophic(c,u),"utr":u,"original":o,"cv":c})
      og=[x["gain_original"] for x in z];cg=[x["gain_cv"] for x in z]; eps=f["gate"]["epsilon_J"]; mean=lambda x:sum(x)/len(x); sd=lambda x:statistics.stdev(x)
      criteria={"positive_mean_gain_vs_utr":mean(cg)>0,"at_least_four_nonnegative":sum(x>=0 for x in cg)>=4,"no_new_catastrophic":sum(x["cv_catastrophic"] for x in z)<=sum(x["original_catastrophic"] for x in z),"range_reduced":max(cg)-min(cg)<max(og)-min(og),"sample_sd_reduced":sd(cg)<sd(og),"mean_retained_vs_original":mean(x["cv_minus_original"] for x in z)>=-eps,"upper_tail_retained":all(x["cv_minus_original"]>=-eps for x in z if x["gain_original"]>eps),"safety":all(x["cv"]["collision"]-x["utr"]["collision"]<=.1 and x["cv"]["timeout"]-x["utr"]["timeout"]<=.1 and x["cv"]["constraint"]<=x["utr"]["constraint"] for x in z)}
      return {"decision":"COHORT_PASS" if all(criteria.values()) else "COHORT_FAIL","criteria":criteria,"original_dispersion":{"range":max(og)-min(og),"sample_sd":sd(og)},"cv_dispersion":{"range":max(cg)-min(cg),"sample_sd":sd(cg)},"seed_results":z}
    A,B=one(f["cohorts"]["A"]),one(f["cohorts"]["B"]); decision="CV_DRTP_PILOT_EARLY_GO" if A["decision"]==B["decision"]=="COHORT_PASS" else "CV_DRTP_PILOT_NO_GO_PERMANENTLY_CLOSED";out.mkdir(parents=True);payload={"decision":decision,"cohort_A":A,"cohort_B":B,"pooled_n10_descriptive_only":True,"automatic_continuation_started":False,"mainline_a_modified":False};(out/"CV_DRTP_PILOT_GATE_DECISION.json").write_text(json.dumps(payload,indent=2)+"\n");(out/"CV_DRTP_PILOT_GATE_REPORT.md").write_text(f"# CV-DRTP two-cohort 0.5M gate\n\n**Decision:** `{decision}`. Cohort A: `{A['decision']}`; Cohort B: `{B['decision']}`.\n\nNo continuation, tuning, rerun, or CV-DRTP-v2 was started.\n")
def main():
 p=argparse.ArgumentParser();p.add_argument("mode",choices=("train","evaluate","aggregate"));p.add_argument("--arm",choices=ARMS);p.add_argument("--seed",type=int,choices=SEEDS);p.add_argument("--output-root",type=Path,required=True);p.add_argument("--workers",type=int,default=9);p.add_argument("--execute",action="store_true");a=p.parse_args()
 if a.mode=="train":
  if a.arm is None or a.seed is None: p.error("train requires --arm and --seed")
  train(a)
 elif a.mode=="evaluate": evaluate(a)
 else: aggregate(a)
if __name__=="__main__": main()
