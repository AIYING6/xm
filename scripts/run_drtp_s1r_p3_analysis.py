"""P3 final/milestone analysis for the two authorized G/B references.

This script is deliberately post-training only.  It refuses to evaluate until
both from-scratch reference runs have complete milestone/runtime artifacts.
It never promotes a milestone checkpoint and never starts P4.
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
import math
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import run_phase_fl_single as fl  # noqa: E402
import run_phase_rsg1_development_smoke as evaluator  # noqa: E402
from envs.uav_intercept_3d_env import UAVIntercept3DConfig, UAVIntercept3DEnv  # noqa: E402


OUT = ROOT / "results" / "development" / "drtp_s1r_p3"
ART = ROOT / "artifacts" / "drtp_s1r_p3"
RUNS = (("R0_G_REF", "G", 2001), ("R1_B_REF", "B", 2002))
MILESTONES = (("250k", 976), ("500k", 1953), ("750k", 2930), ("1m", 3907))
TAPE_NAMES = ("T0", "T1", "T2", "T3", "T4")
FAILURE_CONDITIONS = ("f0", "timing", "duration", "compound")
REQUIRED_MILESTONE_FILES = (
    "actor_critic_milestone_{label}.pt",
    "actor_critic_milestone_{label}_training_state.pt",
    "actor_critic_runtime_state_milestone_{label}.pt",
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def write_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def finite_mean(rows: list[dict], key: str) -> float:
    values = []
    for row in rows:
        try:
            value = float(row[key])
        except (KeyError, TypeError, ValueError):
            continue
        if math.isfinite(value):
            values.append(value)
    return float(np.mean(values)) if values else math.nan


def load_tapes() -> list[dict]:
    manifest = json.loads((ROOT / "artifacts/drtp_s1r_protocol_v2/eval_manifest.json").read_text(encoding="utf-8"))
    tapes = manifest["tapes"]
    if tuple(t["label"] for t in tapes) != TAPE_NAMES:
        raise RuntimeError("P3 tape labels do not match frozen T0-T4 contract")
    if any(len(t["episode_ids"]) != 100 for t in tapes):
        raise RuntimeError("P3 tape episode count mismatch")
    return tapes


def audit_training_artifacts() -> tuple[list[dict], bool]:
    rows, technical = [], True
    for run, ref, seed in RUNS:
        run_dir = OUT / "runs" / run
        manifest_path = run_dir / "run_manifest.json"
        if not manifest_path.exists():
            technical = False
            rows.append({"run": run, "reference": ref, "seed": seed, "status": "MISSING_MANIFEST"})
            continue
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        row = {"run": run, "reference": ref, "seed": seed, "status": manifest.get("status"),
               "parameter_count": manifest.get("parameter_count"),
               "environment_steps": manifest.get("environment_steps"),
               "from_scratch": manifest.get("from_scratch"),
               "resume": manifest.get("resume"),
               "canonical_seeds_used": manifest.get("canonical_seeds_used")}
        required = [run_dir / "actor_critic_latest.pt", run_dir / "actor_critic_training_state_latest.pt",
                    run_dir / "actor_critic_runtime_state_latest.pt", run_dir / "train_log.csv",
                    run_dir / "drtp_topology_sampler_log.csv", run_dir / "drtp_topology_sampler_manifest.json"]
        for label, _update in MILESTONES:
            required.extend(run_dir / pattern.format(label=label) for pattern in REQUIRED_MILESTONE_FILES)
        missing = [str(p) for p in required if not p.exists() or p.stat().st_size == 0]
        row["missing_count"] = len(missing)
        row["missing"] = ";".join(missing)
        if manifest.get("status") != "completed" or manifest.get("parameter_count") != 116728 or \
                manifest.get("environment_steps") != 1000192 or manifest.get("from_scratch") is not True or \
                manifest.get("resume") is not False or missing:
            technical = False
        rows.append(row)
    write_csv(ART / "training_integrity.csv", rows)
    return rows, technical


def checkpoint_rows() -> list[dict]:
    rows = []
    for run, ref, seed in RUNS:
        run_dir = OUT / "runs" / run
        for label, update in MILESTONES:
            for kind, pattern in (("model", "actor_critic_milestone_{label}.pt"),
                                  ("training_state", "actor_critic_milestone_{label}_training_state.pt"),
                                  ("runtime_state", "actor_critic_runtime_state_milestone_{label}.pt")):
                path = run_dir / pattern.format(label=label)
                rows.append({"run": run, "reference": ref, "seed": seed, "milestone": label,
                             "update": update, "kind": kind, "path": str(path.relative_to(ROOT)),
                             "exists": path.exists(), "size": path.stat().st_size if path.exists() else 0,
                             "sha256": sha256(path) if path.exists() else ""})
        final = run_dir / "actor_critic_latest.pt"
        rows.append({"run": run, "reference": ref, "seed": seed, "milestone": "1m", "update": 3907,
                     "kind": "final_model", "path": str(final.relative_to(ROOT)), "exists": final.exists(),
                     "size": final.stat().st_size if final.exists() else 0,
                     "sha256": sha256(final) if final.exists() else ""})
    write_csv(ART / "checkpoint_hashes.csv", rows)
    return rows


def evaluation_task(task: tuple[str, int, str, str, list[int], list[dict], str]) -> list[dict]:
    from run_drtp_sg_development_evaluation import evaluate_cell
    return evaluate_cell(task)


def run_final_evaluation(tapes: list[dict]) -> tuple[list[dict], dict]:
    eval_root = OUT / "evaluations" / "final"
    if eval_root.exists() and any(eval_root.iterdir()):
        raise FileExistsError(f"refusing to overwrite {eval_root}")
    eval_root.mkdir(parents=True, exist_ok=False)
    tasks = []
    for run, _ref, seed in RUNS:
        checkpoint = OUT / "runs" / run / "actor_critic_latest.pt"
        for tape in tapes:
            conditions = []
            for c in tape["conditions"]:
                conditions.append({"name": c["name"], "start_step": c["failure_start_step"],
                                   "duration_steps": c["failure_duration_steps"]})
            tasks.append(("drtp_sg", seed, str(checkpoint), "1m", tape["episode_ids"], conditions, tape["tape_hash"]))
    rows: list[dict] = []
    context = mp.get_context("spawn")
    with ProcessPoolExecutor(max_workers=min(4, len(tasks)), mp_context=context) as pool:
        futures = [pool.submit(evaluation_task, task) for task in tasks]
        for future in as_completed(futures):
            rows.extend(future.result())
    rows.sort(key=lambda r: (int(r["train_seed"]), r["tape_hash"], r["topology_condition"], int(r["development_episode_id"])))
    write_csv(eval_root / "raw_episode_metrics.csv", rows)
    summary = []
    for run, ref, seed in RUNS:
        for tape in tapes:
            for condition in tape["conditions"]:
                name = condition["name"]
                subset = [r for r in rows if int(r["train_seed"]) == seed and r["tape_hash"] == tape["tape_hash"]
                          and r["topology_condition"] == name]
                summary.append({"run": run, "reference": ref, "seed": seed, "tape": tape["label"],
                                "condition": name, "J": finite_mean(subset, "J"),
                                "collision": finite_mean(subset, "collision"),
                                "timeout": finite_mean(subset, "timeout"),
                                "constraint_violation": finite_mean(subset, "constraint_violation"),
                                "failure_exposure": finite_mean(subset, "failure_exposed"),
                                "episode_length": finite_mean(subset, "terminal_step"),
                                "pre_trigger_collision": finite_mean(
                                    [{"v": float(r["collision"]) if int(r["terminal_step"]) < int(condition.get("failure_start_step") or 10**9) else 0.0} for r in subset], "v")})
    write_csv(eval_root / "per_reference_tape_condition_summary.csv", summary)
    return rows, {"raw_rows": len(rows), "summary_rows": len(summary), "evaluation_root": str(eval_root.relative_to(ROOT))}


def metric_summary(rows: list[dict], tapes: list[dict]) -> tuple[list[dict], dict]:
    by_ref = {ref: [r for r in rows if int(r["train_seed"]) == seed] for _run, ref, seed in RUNS}
    metrics = {"f0": "f0", "timing": "timing", "duration": "duration", "compound": "compound"}
    gap_rows, gate = [], {}
    for ref, ref_rows in by_ref.items():
        for tape in tapes:
            for metric, condition in metrics.items():
                subset = [r for r in ref_rows if r["tape_hash"] == tape["tape_hash"] and r["topology_condition"] == condition]
                gap_rows.append({"reference": ref, "tape": tape["label"], "metric": metric, "J": finite_mean(subset, "J"),
                                 "timeout": finite_mean(subset, "timeout"), "collision": finite_mean(subset, "collision"),
                                 "exposure": finite_mean(subset, "failure_exposed")})
    for metric in metrics:
        g = [r["J"] for r in gap_rows if r["reference"] == "G" and r["metric"] == metric]
        b = [r["J"] for r in gap_rows if r["reference"] == "B" and r["metric"] == metric]
        gate[f"mean_gap_{metric}"] = float(np.mean(g) - np.mean(b))
        gate[f"tape_positive_{metric}"] = sum(x > y for x, y in zip(g, b))
    g_timeout = [r["timeout"] for r in gap_rows if r["reference"] == "G"]
    b_timeout = [r["timeout"] for r in gap_rows if r["reference"] == "B"]
    gate["mean_timeout_quality_gap"] = float(np.mean(b_timeout) - np.mean(g_timeout))
    gate["tape_positive_timeout_quality"] = sum(x < y for x, y in zip(g_timeout, b_timeout))
    gate["R1"] = all(gate[f"mean_gap_{m}"] > 0 for m in metrics)
    gate["R2"] = sum(gate[f"tape_positive_{m}"] >= 4 for m in metrics) >= 3
    gate["R3"] = gate["mean_timeout_quality_gap"] > 0 and gate["tape_positive_timeout_quality"] >= 3
    write_csv(ART / "reference_gap_by_tape.csv", gap_rows)
    write_json(ART / "reference_gate_metrics.json", gate)
    return gap_rows, gate


def telemetry_env(seed: int, condition: dict) -> UAVIntercept3DEnv:
    onset = condition.get("start_step")
    duration = condition.get("duration_steps")
    failure = onset is not None
    return UAVIntercept3DEnv(UAVIntercept3DConfig(
        seed=seed, target_policy="straight", strict_target_sensing=True,
        agent_target_info_bottleneck=True, relay_dependent_task=True,
        business_grounded_geometry=True, communication_range_scale=1.0,
        communication_dropout_prob=0.0, message_delay_steps=0,
        radar_dropout_prob=0.0, max_steps=260, min_success_step=260,
        failed_blue_agent=1 if failure else -1,
        node_failure_start_step=int(onset or 0), node_failure_duration_steps=int(duration or 0)))


def telemetry_cell(task: tuple[str, int, str, str, str, list[int], dict]) -> list[dict]:
    run, seed, checkpoint_str, milestone, tape, episode_ids, condition = task
    agent = fl.build_agent({"graph_encoder": "single", "hidden_dim": 115}, Path(checkpoint_str), seed)
    output = []
    for episode_id in episode_ids:
        env = telemetry_env(episode_id, condition)
        obs, share, graph = env.reset()
        initial_range = float(env._mean_target_range())
        progress = []
        records = []
        while True:
            step = int(env.step_count)
            actions = evaluator.policy_action(agent, obs, share, graph)
            obs, share, graph, rewards, dones, info = env.step(actions)
            current_range = float(info.get("mean_range", env._mean_target_range()))
            task_progress = float(np.clip((initial_range - current_range) / max(initial_range, 1e-9), -1.0, 1.0))
            stage = int(bool(info.get("chain_support_t", 0.0))) + int(bool(info.get("chain_closed", 0.0)))
            records.append({"env_step": step, "failure_relative_step": step - int(condition.get("start_step") or 0),
                            "task_progress": task_progress, "task_stage": stage,
                            "relay_failure_active": int(float(info.get("node_failure_active", 0.0)) > .5),
                            "path": str(info.get("attacker_cache_paths_t", "")),
                            "task_support": int(float(info.get("chain_support_t", 0.0)) > .5),
                            "legal_information": int(float(info.get("attacker_legal_target_information_t", 0.0)) > .5),
                            "cache_age": float(info.get("target_cache_age_mean", 0.0)),
                            "mean_range": current_range, "collision": float(info.get("collision", 0.0)),
                            "timeout": float(info.get("timeout", 0.0)),
                            "constraint_violation": float(info.get("constraint_violation", 0.0)),
                            "terminal_step": int(info.get("step", step)) if np.all(dones) else None})
            progress.append(task_progress)
            if np.all(dones):
                break
        for index, rec in enumerate(records):
            window = progress[max(0, index - 4):index + 1]
            rec["stagnation"] = int(len(window) >= 5 and abs(window[-1] - window[0]) <= 1e-6)
        output.append({"protocol": "DRTP-S1R-P3-MILESTONE-TRAJECTORY-V1", "run": run, "seed": seed,
                       "milestone": milestone, "tape": tape, "condition": condition["name"],
                       "episode_id": episode_id, "records": records,
                       "scheduled_failure_onset": condition.get("start_step"),
                       "scheduled_failure_duration": condition.get("duration_steps"),
                       "failure_exposure": any(r["relay_failure_active"] for r in records),
                       "terminal_step": records[-1]["terminal_step"] or records[-1]["env_step"]})
    return output


def run_milestone_telemetry(tapes: list[dict]) -> dict:
    telemetry_root = OUT / "milestone_telemetry"
    telemetry_root.mkdir(parents=True, exist_ok=True)
    tp50 = json.loads((ROOT / "artifacts/drtp_s1r_protocol_v2/tp50_manifest.json").read_text(encoding="utf-8"))["episodes"]
    by_tape = {label: [int(x["episode_id"]) for x in tp50 if x["tape"] == label] for label in TAPE_NAMES}
    tasks = []
    for run, _ref, seed in RUNS:
        for milestone, _update in MILESTONES:
            checkpoint = OUT / "runs" / run / f"actor_critic_milestone_{milestone}.pt"
            for tape in tapes:
                for condition in tape["conditions"]:
                    tasks.append((run, seed, str(checkpoint), milestone, tape["label"], by_tape[tape["label"]],
                                  {"name": condition["name"], "start_step": condition["failure_start_step"],
                                   "duration_steps": condition["failure_duration_steps"]}))
    path = telemetry_root / "tp50_step_telemetry.jsonl.gz"
    count = 0
    with gzip.open(path, "wt", encoding="utf-8") as output:
        context = mp.get_context("spawn")
        with ProcessPoolExecutor(max_workers=4, mp_context=context) as pool:
            futures = [pool.submit(telemetry_cell, task) for task in tasks]
            for future in as_completed(futures):
                for record in future.result():
                    output.write(json.dumps(record, separators=(",", ":"), default=str) + "\n")
                    count += 1
    manifest = {"protocol": "DRTP-S1R-P3-MILESTONE-TRAJECTORY-V1", "records": count,
                "step_telemetry_gzip": str(path.relative_to(ROOT)), "sha256": sha256(path),
                "milestones": [x[0] for x in MILESTONES], "tp50_per_tape": 10,
                "conditions_per_tape": 5, "tapes": list(TAPE_NAMES)}
    write_json(ART / "milestone_telemetry_manifest.json", manifest)
    return manifest


def precursor_summary() -> dict:
    path = OUT / "milestone_telemetry" / "tp50_step_telemetry.jsonl.gz"
    rows = []
    with gzip.open(path, "rt", encoding="utf-8") as f:
        for line in f:
            item = json.loads(line)
            if item["milestone"] != "500k" or item["condition"] == "nominal":
                continue
            records = item["records"]
            onset = int(item["scheduled_failure_onset"] or 0)
            window = [r for r in records if onset <= r["env_step"] < onset + 40]
            eligible = len(window) == 40 and any(r["env_step"] == onset - 1 for r in records)
            if not eligible:
                continue
            p1 = (window[-1]["task_progress"] - window[0]["task_progress"]) / 40.0
            p2 = -float(np.mean([r["stagnation"] for r in window]))
            p3 = float(window[-1]["task_stage"] > window[0]["task_stage"])
            rows.append({"run": item["run"], "reference": "G" if item["run"] == "R0_G_REF" else "B",
                         "tape": item["tape"], "condition": item["condition"], "episode_id": item["episode_id"],
                         "P1": p1, "P2": p2, "P3": p3, "failure_exposure": item["failure_exposure"]})
    write_csv(ART / "tp50_precursor_raw.csv", rows)
    summary = []
    for metric in ("P1", "P2", "P3"):
        g = [float(r[metric]) for r in rows if r["reference"] == "G"]
        b = [float(r[metric]) for r in rows if r["reference"] == "B"]
        summary.append({"metric": metric, "G_mean": float(np.mean(g)) if g else math.nan,
                        "B_mean": float(np.mean(b)) if b else math.nan,
                        "gap_G_minus_B": (float(np.mean(g)) - float(np.mean(b))) if g and b else math.nan,
                        "eligible": bool(g and b and float(np.mean(g)) - float(np.mean(b)) > 0)})
    write_csv(ART / "tp50_precursor_summary.csv", summary)
    eligible = sum(bool(r["eligible"]) for r in summary)
    result = {"metrics": summary, "eligible_metric_count": eligible, "required": 2, "pass": eligible >= 2}
    write_json(ART / "precursor_reference_gate.json", result)
    return result


def write_reports(technical: bool, gate: dict, precursor: dict, evaluation: dict, telemetry: dict, outcome: str) -> None:
    common = ("\nHistorical v1/v2 contracts are preserved. This P3 result does not revise "
              "the earlier execution history and does not claim an RNG root cause, "
              "policy-basin cause, or intervention benefit.\n")
    (ROOT / "docs/DRTP_S1R_P3_TRAINING_INTEGRITY_REPORT.md").write_text(
        "# DRTP S1-R P3 Training Integrity Report\n\n"
        f"Technical integrity: **{'PASS' if technical else 'FAIL'}**.\n\n"
        "The two authorized runs are R0_G_REF (seed 2001) and R1_B_REF (seed 2002), "
        "each with 3,907 updates and 1,000,192 environment steps. Milestone model, "
        "training-state, runtime-state, hashes, PPO logs, and DRTP logs are listed in "
        "`artifacts/drtp_s1r_p3/checkpoint_hashes.csv`.\n" + common, encoding="utf-8")
    (ROOT / "docs/DRTP_S1R_P3_REFERENCE_PERFORMANCE_REPORT.md").write_text(
        "# DRTP S1-R P3 Reference Performance Report\n\n"
        f"Final evaluation records: `{evaluation.get('raw_rows', 0)}`.\n\n"
        f"R1: `{gate.get('R1')}`; R2: `{gate.get('R2')}`; R3: `{gate.get('R3')}`.\n\n"
        "Per-tape gaps are in `artifacts/drtp_s1r_p3/reference_gap_by_tape.csv`; "
        "raw records are retained under `results/development/drtp_s1r_p3/evaluations/final/`.\n" + common, encoding="utf-8")
    (ROOT / "docs/DRTP_S1R_P3_PRECURSOR_REFERENCE_REPORT.md").write_text(
        "# DRTP S1-R P3 Precursor Reference Report\n\n"
        f"Milestone telemetry records: `{telemetry.get('records', 0)}`; precursor gate: "
        f"`{precursor.get('pass')}` with `{precursor.get('eligible_metric_count')}/3` metrics eligible.\n\n"
        "The 500k TP50 precursor is confirmatory only and never substitutes for the 1M final result.\n" + common, encoding="utf-8")
    write_json(ART / "p3_final_decision.json", {"protocol": "DRTP-S1R-P3-G-B-REFERENCE-V1",
                                                "technical_valid": technical, "gate": gate,
                                                "precursor": precursor, "outcome": outcome,
                                                "evaluation": evaluation, "telemetry": telemetry,
                                                "scientific_env_steps": 2000384, "P4_started": False,
                                                "heldout_started": False, "canonical_seeds_used": False})
    (ROOT / "docs/DRTP_S1R_P3_FINAL_REPORT.md").write_text(
        "# DRTP S1-R P3 Final Report\n\n"
        f"## Outcome: `{outcome}`\n\n"
        f"Technical valid: `{technical}`. R1/R2/R3: `{gate.get('R1')}` / `{gate.get('R2')}` / `{gate.get('R3')}`. "
        f"Precursor pass: `{precursor.get('pass')}`. P4 started: `False`.\n\n"
        "P3 stops here. No intervention, held-out, canonical, extension, or new algorithm is started automatically.\n" + common,
        encoding="utf-8")


def main() -> None:
    ART.mkdir(parents=True, exist_ok=True)
    tapes = load_tapes()
    integrity, technical = audit_training_artifacts()
    checkpoint_rows()
    if not technical:
        outcome = "P3_TECHNICAL_INVALID"
        write_reports(False, {}, {"pass": False, "eligible_metric_count": 0}, {"raw_rows": 0}, {"records": 0}, outcome)
        return
    rows, evaluation = run_final_evaluation(tapes)
    _gaps, gate = metric_summary(rows, tapes)
    telemetry = run_milestone_telemetry(tapes)
    precursor = precursor_summary()
    if not (gate["R1"] and gate["R2"] and gate["R3"]):
        outcome = "F_REFERENCE_NOT_REPRODUCED"
    elif not precursor["pass"]:
        outcome = "F_PRECURSOR_REFERENCE_NOT_SEPARATED"
    else:
        outcome = "P3_REFERENCE_QUALIFIED"
    write_reports(True, gate, precursor, evaluation, telemetry, outcome)
    write_json(OUT / "p3_analysis_completion.json", {"status": "completed", "outcome": outcome})


if __name__ == "__main__":
    main()
