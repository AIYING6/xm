"""Frozen cloud-only SR-DRTP P1 official and matched-shadow units."""
from __future__ import annotations
import argparse, csv, hashlib, json, subprocess, sys, time
from dataclasses import asdict, fields, replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]; sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]
from algorithms.ri_gmappo.simple_ri_gmappo import RIGMAPPOConfig, train_ri_gmappo
import run_drtp_sg_strict_10m_single as strict

FREEZE = ROOT / "configs" / "sr_drtp_p1_shadow_preparation_freeze.json"

def sha(path: Path) -> str: return hashlib.sha256(path.read_bytes()).hexdigest()
def head() -> str:
    try: return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception: return "UNAVAILABLE"
def freeze() -> dict: return json.loads(FREEZE.read_text(encoding="utf-8"))
def cohort(seed: int, f: dict) -> str:
    return "A" if seed in f["cohorts"]["A"] else "B" if seed in f["cohorts"]["B"] else (_ for _ in ()).throw(ValueError("unauthorized seed"))
def labels(f: dict) -> dict[int, str]: return {int(u): f"u{int(u):04d}" for u in f["shadow_events"]["source_updates"]}
def mean_reward(path: Path) -> float:
    with path.open(newline="", encoding="utf-8") as h: rows = list(csv.DictReader(h))
    if not rows: raise RuntimeError("shadow emitted no train rows")
    return sum(float(r["train_avg_reward"]) for r in rows) / len(rows)

def official(seed: int, output_root: Path) -> None:
    f = freeze()
    if not f["authorization"]["p1_execution_authorized"]: raise RuntimeError("P1 execution authorization absent")
    out = output_root / "runs" / "drtp_sg" / f"seed{seed}"
    if out.exists(): raise FileExistsError(f"refusing overwrite: {out}")
    out.mkdir(parents=True)
    base = strict.training_config("drtp_sg", seed, out)
    cfg = replace(base, seed=seed, updates=f["official_trajectory"]["updates"], out_dir=str(out),
        drtp_sampler_mode="drtp", drtp_sampler_seed=seed, drtp_sampler_total_updates=f["official_trajectory"]["updates"],
        evaluation_enabled=False, policy_update_guard_mode="none", target_kl=None,
        runtime_state_checkpointing=True, runtime_state_save_interval=1, save_interval=256,
        milestone_updates=labels(f), sr_drtp_telemetry=True, sr_drtp_telemetry_interval=32,
        sr_drtp_p1_pp_signal=True, sr_drtp_p1_pp_probe_count=4,
        sr_drtp_p1_pp_probe_updates=tuple(f["shadow_events"]["source_updates"]))
    (out / "frozen_config.json").write_text(json.dumps(asdict(cfg), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest = {"protocol":f["protocol"],"status":"running","seed":seed,"cohort":cohort(seed,f),"arm":"original_drtp_only","updates":cfg.updates,"evaluation_enabled":False,"shadow_selection":False,"freeze_sha256":sha(FREEZE),"commit":head(),"started_at":time.time()}
    p=out/"run_manifest.json"; p.write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    try:
        train_ri_gmappo(cfg)
        required=[out/"train_log.csv",out/"sr_drtp_p1_signal"/"pp_disagreement.csv"]+[out/f"actor_critic_runtime_state_milestone_{x}.pt" for x in labels(f).values()]
        if not all(x.exists() for x in required): raise RuntimeError("missing frozen official P1 artifacts")
        manifest.update(status="completed",completed_at=time.time())
    except BaseException as e:
        manifest.update(status="failed",error=repr(e)); p.write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8"); raise
    p.write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")

def shadow(seed: int, source_update: int, branch: str, output_root: Path) -> None:
    f=freeze(); cohort(seed,f)
    if branch not in {"A","B","C"}: raise ValueError("branch must be A/B/C")
    if source_update not in labels(f): raise ValueError("unfrozen source update")
    official_dir=output_root/"runs"/"drtp_sg"/f"seed{seed}"
    source=official_dir/f"actor_critic_runtime_state_milestone_{labels(f)[source_update]}.pt"
    raw=json.loads((official_dir/"frozen_config.json").read_text(encoding="utf-8")); allowed={x.name for x in fields(RIGMAPPOConfig)}
    cfg=RIGMAPPOConfig(**{k:v for k,v in raw.items() if k in allowed})
    out=official_dir/"matched_shadows"/f"u{source_update:04d}"/branch
    if out.exists(): raise FileExistsError(f"refusing overwrite: {out}")
    mode={"A":"none","B":"sampler_uniform_anchor","C":"actor_rollback_next_update"}[branch]
    cfg=replace(cfg,updates=f["shadow_events"]["horizon_updates"],update_offset=source_update,out_dir=str(out),runtime_state_resume=str(source),append_log=False,evaluation_enabled=False,diagnostic_rng_branch_mode="exact_replay",diagnostic_rng_branch_seed=None,sr_drtp_p1_pp_signal=False,sr_drtp_telemetry=False,sr_drtp_shadow_branch=mode)
    out.mkdir(parents=True)
    manifest={"protocol":f["protocol"],"status":"running","seed":seed,"cohort":cohort(seed,f),"source_update":source_update,"branch":branch,"branch_semantics":f["branches"][branch],"horizon_updates":cfg.updates,"source_sha256":sha(source),"formal_or_heldout_evaluation_tape_used":False,"official_trajectory_modified":False,"started_at":time.time()}
    p=out/"shadow_manifest.json"; p.write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    try:
        train_ri_gmappo(cfg); manifest.update(status="completed",outcome_mean_training_reward=mean_reward(out/"train_log.csv"),completed_at=time.time())
    except BaseException as e:
        manifest.update(status="failed",error=repr(e)); p.write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8"); raise
    p.write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")

def main() -> None:
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest="cmd",required=True)
    for name in ("official","shadow"):
        q=sub.add_parser(name); q.add_argument("--seed",type=int,required=True); q.add_argument("--output-root",type=Path,required=True); q.add_argument("--execute",action="store_true")
        if name=="shadow": q.add_argument("--source-update",type=int,required=True); q.add_argument("--branch",required=True)
    a=p.parse_args()
    if not a.execute: raise SystemExit("--execute required")
    if a.cmd=="official": official(a.seed,a.output_root)
    else: shadow(a.seed,a.source_update,a.branch,a.output_root)
if __name__=="__main__": main()
