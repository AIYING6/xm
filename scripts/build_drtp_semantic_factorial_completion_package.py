"""Build the paired 2x2 completion package for the DRTP semantic ablation.

The existing Fixed-DRTP and Random-DRTP endpoints are never retrained.  This
package restores them from their result archive, trains only UTR and original
DRTP for the same five seeds, then evaluates all four arms on the identical
frozen endpoint tape.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
import textwrap
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ARCHIVE = ROOT / "output" / "DRTP_STABILIZATION_FINAL_CONFIRMATION_10M.zip"
RESULT_ARCHIVE = Path(r"D:\File\Downloads\drtp_semantic_ablation_nonpaired_10m_results.tar.gz")
PACKAGE = ROOT / "output" / "DRTP_SEMANTIC_ABLATION_FACTORIAL_COMPLETION_10M_V1.zip"
SOURCE_COMMIT = "0e6a34d280794ea4c86c6744af0b2ac20fe0eb56"
SEEDS = (80011, 80012, 80013, 80014, 80015)
OLD_ARMS = ("fixed_drtp_sg", "random_drtp_sg")
NEW_ARMS = ("utr_sg", "drtp_sg")
ALL_ARMS = (*NEW_ARMS, *OLD_ARMS)
EXPECTED_EXISTING_SHA256 = "f088e5aae92c695d5acabdfb703fe49e0dda82b55c3f2be407c773d652b86ce9"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git_source(path: str) -> str:
    return subprocess.check_output(
        ["git", "show", f"{SOURCE_COMMIT}:{path}"], cwd=ROOT, text=True
    )


def replace_once(text: str, old: str, new: str) -> str:
    if text.count(old) != 1:
        raise RuntimeError(f"expected one patch anchor, found {text.count(old)}: {old[:60]!r}")
    return text.replace(old, new)


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")


def source_member(archive: ZipFile, prefix: str, relative: str) -> bytes:
    return archive.read(f"{prefix}/{relative}")


def build_runner() -> str:
    return r'''
"""Train only the missing UTR and original-DRTP factorial-completion arms."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from algorithms.ri_gmappo.simple_ri_gmappo import RIGMAPPOConfig, train_ri_gmappo

PROTOCOL = "DRTP-SEMANTIC-ABLATION-FACTORIAL-COMPLETION-10M-V1"
SEEDS = (80011, 80012, 80013, 80014, 80015)
ARMS = {"utr_sg": ("utr", None), "drtp_sg": ("drtp", None)}
UPDATES, NUM_ENVS, ROLLOUT = 39063, 4, 64
STEPS = UPDATES * NUM_ENVS * ROLLOUT
MILESTONES = {3907: "1m", 11719: "3m", 39063: "10m"}
TAPE_PROTOCOL = "DRTP-SEMANTIC-ABLATION-NONPAIRED-TAPE-V1"
TAPE_IDS = list(range(800000, 800100))

def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def source_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return "package-provenance-only"

def load_tape(output_root: Path) -> dict:
    tape = json.loads((output_root / "tape" / "tape_manifest.json").read_text(encoding="utf-8"))
    if (tape.get("protocol") != TAPE_PROTOCOL or tape.get("episode_ids") != TAPE_IDS
            or tape.get("training_access") != "forbidden"):
        raise RuntimeError("the existing semantic-ablation tape is not the frozen completion tape")
    return tape

def config(arm: str, seed: int, out_dir: Path) -> RIGMAPPOConfig:
    mode, alpha = ARMS[arm]
    return RIGMAPPOConfig(
        env_name="3d_intercept", seed=seed, num_envs=NUM_ENVS, rollout_steps=ROLLOUT, updates=UPDATES,
        hidden_dim=115, role_dim=8, intent_dim=8, graph_encoder="single", role_gate_mode="none",
        target_policy="straight", strict_target_sensing=True, agent_target_info_bottleneck=True,
        relay_dependent_task=True, business_grounded_geometry=True, communication_range_scale=1.0,
        communication_dropout_prob=0.0, message_delay_steps=0, radar_dropout_prob=0.0,
        min_success_step=260, failed_blue_agent=-1, node_failure_start_step=0, node_failure_duration_steps=0,
        evaluation_enabled=False, target_kl=None, save_interval=UPDATES, save_snapshots=False,
        milestone_updates=MILESTONES, out_dir=str(out_dir), device="cuda" if torch.cuda.is_available() else "cpu",
        topology_curriculum_schedule="none", topology_curriculum_logging=False, fixed_f0_probability=None,
        drtp_sampler_mode=mode, drtp_sampler_seed=seed,
        drtp_sampler_anchor_alpha=1.0 if alpha is None else alpha, drtp_sampler_logging=True,
        runtime_state_checkpointing=True, runtime_state_save_interval=UPDATES,
    )

def run_one(arm: str, seed: int, output_root: Path) -> None:
    if arm not in ARMS or seed not in SEEDS:
        raise ValueError("unfrozen factorial-completion arm or seed")
    tape = load_tape(output_root)
    out = output_root / "runs" / arm / f"seed{seed}"
    if out.exists():
        raise FileExistsError(f"refusing to overwrite {out}")
    out.mkdir(parents=True)
    cfg = config(arm, seed, out)
    manifest = {
        "protocol": PROTOCOL, "status": "running", "arm": arm, "seed": seed,
        "sampler_mode": ARMS[arm][0], "anchor_alpha": ARMS[arm][1], "updates": UPDATES,
        "environment_steps": STEPS, "num_envs": NUM_ENVS, "rollout_steps": ROLLOUT,
        "milestone_updates": MILESTONES, "from_scratch": True, "resume": False,
        "early_stopping": False, "checkpoint_promotion": False, "seed_replacement": False,
        "evaluation_during_training": False, "fixed_final_budget_only": True,
        "tape_hash": tape["tape_hash"], "tape_not_read_by_training": True,
        "source_commit": source_commit(), "config": cfg.__dict__,
    }
    manifest_path = out / "run_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")
    train_ri_gmappo(cfg)
    required = [out / "actor_critic_latest.pt", out / "actor_critic_runtime_state_latest.pt",
                out / "drtp_topology_sampler_manifest.json", out / "drtp_topology_sampler_log.csv"]
    for label in MILESTONES.values():
        required += [out / f"actor_critic_milestone_{label}.pt", out / f"actor_critic_runtime_state_milestone_{label}.pt"]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError("missing final artifacts: " + ", ".join(missing))
    manifest.update({"status": "completed", "checkpoint_sha256": digest(out / "actor_critic_latest.pt"),
                     "runtime_state_sha256": digest(out / "actor_critic_runtime_state_latest.pt"),
                     "sampler_manifest_sha256": digest(out / "drtp_topology_sampler_manifest.json")})
    manifest_path.write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({"status": "completed", "arm": arm, "seed": seed}, indent=2), flush=True)

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", choices=tuple(ARMS), required=True)
    parser.add_argument("--seed", choices=SEEDS, type=int, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("explicit --execute is required")
    run_one(args.arm, args.seed, args.output_root)

if __name__ == "__main__":
    main()
'''


def build_evaluator() -> str:
    return r'''
"""Evaluate all four factorial arms on the restored frozen endpoint tape."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]
import run_phase_rsg1_development_smoke as evaluator
from envs.uav_intercept_3d_env import UAVIntercept3DConfig, UAVIntercept3DEnv

PROTOCOL = "DRTP-SEMANTIC-ABLATION-FACTORIAL-COMPLETION-EVALUATION-V1"
SEEDS = (80011, 80012, 80013, 80014, 80015)
ARMS = ("utr_sg", "fixed_drtp_sg", "random_drtp_sg", "drtp_sg")
SAMPLER_MODES = {"utr_sg": "utr", "fixed_drtp_sg": "fixed_drtp", "random_drtp_sg": "random_drtp", "drtp_sg": "drtp"}
UPDATES, STEPS = 39063, 10000128
TAPE_PROTOCOL = "DRTP-SEMANTIC-ABLATION-NONPAIRED-TAPE-V1"
TAPE_IDS = list(range(800000, 800100))

def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def fixed_env(seed: int, condition: dict) -> UAVIntercept3DEnv:
    return UAVIntercept3DEnv(UAVIntercept3DConfig(
        seed=seed, target_policy="straight", strict_target_sensing=True,
        agent_target_info_bottleneck=True, relay_dependent_task=True, business_grounded_geometry=True,
        communication_range_scale=1.0, communication_dropout_prob=0.0, message_delay_steps=0,
        radar_dropout_prob=0.0, max_steps=260, min_success_step=260,
        failed_blue_agent=int(condition["failed_blue_agent"]),
        node_failure_start_step=int(condition["start_step"]),
        node_failure_duration_steps=int(condition["duration_steps"]),
    ))

def evaluate_cell(task: tuple) -> list[dict]:
    arm, seed, checkpoint, episode_ids, conditions, tape_hash = task
    import torch
    torch.set_num_threads(1)
    agent = evaluator.build_agent({"graph_encoder": "single", "hidden_dim": 115}, Path(checkpoint), seed)
    rows = []
    for condition in conditions:
        original = evaluator.frozen_env
        evaluator.frozen_env = lambda episode_seed, failure_on, _c=condition: fixed_env(episode_seed, _c)
        try:
            for episode_id in episode_ids:
                row, _ = evaluator.evaluate_episode(agent, arm, seed, int(episode_id), "nominal" if condition["name"] == "nominal" else "relay_failure")
                row.update({"protocol": PROTOCOL, "topology_condition": condition["name"],
                            "scheduled_failure_onset": int(condition["start_step"]),
                            "scheduled_failure_duration": int(condition["duration_steps"]),
                            "checkpoint_sha256": digest(Path(checkpoint)), "tape_hash": tape_hash})
                rows.append(row)
        finally:
            evaluator.frozen_env = original
    return rows

def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)

def mean(rows: list[dict], key: str) -> float:
    values = [float(row[key]) for row in rows if math.isfinite(float(row[key]))]
    return sum(values) / len(values) if values else math.nan

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trained-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=10)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("explicit --execute is required")
    if args.output_root.exists():
        raise FileExistsError(f"refusing to overwrite {args.output_root}")
    tape = json.loads((args.trained_root / "tape" / "tape_manifest.json").read_text(encoding="utf-8"))
    if (tape.get("protocol") != TAPE_PROTOCOL or tape.get("episode_ids") != TAPE_IDS
            or tape.get("training_access") != "forbidden"):
        raise RuntimeError("invalid frozen semantic-ablation evaluation tape")
    tasks, manifests = [], []
    for arm in ARMS:
        for seed in SEEDS:
            run = args.trained_root / "runs" / arm / f"seed{seed}"
            manifest = json.loads((run / "run_manifest.json").read_text(encoding="utf-8"))
            expected = {"status": "completed", "updates": UPDATES, "environment_steps": STEPS,
                        "from_scratch": True, "resume": False, "early_stopping": False,
                        "checkpoint_promotion": False, "seed_replacement": False, "tape_hash": tape["tape_hash"]}
            if any(manifest.get(key) != value for key, value in expected.items()):
                raise RuntimeError(f"invalid source manifest: {arm}/seed{seed}")
            if manifest.get("sampler_mode") != SAMPLER_MODES[arm]:
                raise RuntimeError(f"wrong sampler mode: {arm}/seed{seed}")
            checkpoint = run / "actor_critic_latest.pt"
            if not checkpoint.is_file() or manifest.get("checkpoint_sha256") != digest(checkpoint):
                raise RuntimeError(f"invalid final checkpoint: {checkpoint}")
            tasks.append((arm, seed, str(checkpoint), tape["episode_ids"], tape["conditions"], tape["tape_hash"]))
            manifests.append(manifest)
    total = len(tasks) * len(tape["conditions"]) * len(tape["episode_ids"])
    print(f"DRTP semantic factorial evaluation: cells={len(tasks)}, episodes={total}, workers={min(args.workers, len(tasks))}", flush=True)
    raw, completed = [], 0
    with ProcessPoolExecutor(max_workers=min(args.workers, len(tasks)), mp_context=mp.get_context("spawn")) as pool:
        futures = [pool.submit(evaluate_cell, task) for task in tasks]
        for future in as_completed(futures):
            rows = future.result(); raw.extend(rows); completed += len(rows)
            print(f"DRTP semantic factorial evaluation progress {completed}/{total} ({100 * completed / total:.2f}%)", flush=True)
    condition_order = {row["name"]: index for index, row in enumerate(tape["conditions"])}
    raw.sort(key=lambda row: (row["method"], int(row["train_seed"]), condition_order[row["topology_condition"]], int(row["development_episode_id"])))
    write_csv(args.output_root / "raw_episode_metrics.csv", raw)
    summary = []
    for arm in ARMS:
        for seed in SEEDS:
            for condition in condition_order:
                subset = [row for row in raw if row["method"] == arm and int(row["train_seed"]) == seed and row["topology_condition"] == condition]
                summary.append({"method": arm, "train_seed": seed, "condition": condition, "episodes": len(subset),
                                "J": mean(subset, "J"), "success": mean(subset, "success_at_horizon"),
                                "collision": mean(subset, "collision"), "timeout": mean(subset, "timeout"),
                                "constraint_violation": mean(subset, "constraint_violation"),
                                "control_effort": mean(subset, "control_effort")})
    write_csv(args.output_root / "per_seed_condition_summary.csv", summary)
    manifest = {"protocol": PROTOCOL, "status": "completed", "endpoint": "final_10m_only",
                "arms": list(ARMS), "seeds": list(SEEDS), "conditions": list(condition_order),
                "raw_episode_rows": len(raw), "summary_rows": len(summary), "tape_hash": tape["tape_hash"],
                "source_run_manifests": manifests, "training_started": False, "automatic_algorithm_revision": False}
    (args.output_root / "evaluation_manifest.json").write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({"status": "completed", "raw_episode_rows": len(raw)}, indent=2), flush=True)

if __name__ == "__main__":
    main()
'''


def build_aggregator() -> str:
    return r'''
"""Aggregate the paired 2x2 DRTP semantic-ablation completion."""
from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections import defaultdict
from pathlib import Path

ARMS = ("utr_sg", "fixed_drtp_sg", "random_drtp_sg", "drtp_sg")
SEEDS = (80011, 80012, 80013, 80014, 80015)
PERTURBED = ("F0", "TE", "TL", "DS", "DL", "CP")
METRICS = ("J_nominal", "J_perturbed", "J_perturbed_worst_condition", "success_perturbed", "timeout_perturbed", "collision_perturbed")
CONTRASTS = {
    "semantic_effect_fixed": ("fixed_drtp_sg", "utr_sg"),
    "adaptive_effect_without_semantics": ("random_drtp_sg", "utr_sg"),
    "adaptive_effect_with_semantics": ("drtp_sg", "fixed_drtp_sg"),
    "semantic_effect_adaptive": ("drtp_sg", "random_drtp_sg"),
}

def average(values): return statistics.fmean(values)
def summary(values):
    return {"mean": average(values), "median": statistics.median(values), "sample_sd": statistics.stdev(values),
            "positive_seeds": sum(value > 0 for value in values), "worst": min(values), "best": max(values)}
def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evaluation-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute: raise SystemExit("explicit --execute is required")
    out = args.output_root / "diagnostics" / "semantic_factorial_completion"
    if out.exists(): raise FileExistsError(out)
    rows = list(csv.DictReader((args.evaluation_root / "per_seed_condition_summary.csv").open(encoding="utf-8")))
    by = defaultdict(dict)
    for row in rows: by[(row["method"], int(row["train_seed"]))][row["condition"]] = row
    endpoints = []
    for arm in ARMS:
        for seed in SEEDS:
            cell = by[(arm, seed)]
            if set(cell) != {"nominal", *PERTURBED}: raise RuntimeError(f"incomplete endpoint: {arm}/{seed}")
            failures = [cell[condition] for condition in PERTURBED]
            endpoints.append({"method": arm, "train_seed": seed,
                "J_nominal": float(cell["nominal"]["J"]), "J_perturbed": average([float(x["J"]) for x in failures]),
                "J_perturbed_worst_condition": min(float(x["J"]) for x in failures),
                "success_perturbed": average([float(x["success"]) for x in failures]),
                "timeout_perturbed": average([float(x["timeout"]) for x in failures]),
                "collision_perturbed": average([float(x["collision"]) for x in failures])})
    summary_rows = []
    for arm in ARMS:
        chosen = [row for row in endpoints if row["method"] == arm]
        output = {"method": arm, "n_training_seeds": len(chosen)}
        for metric in METRICS:
            values = [row[metric] for row in chosen]
            output.update({f"mean_{metric}": average(values), f"median_{metric}": statistics.median(values),
                           f"sample_sd_{metric}": statistics.stdev(values), f"min_{metric}": min(values), f"max_{metric}": max(values)})
        summary_rows.append(output)
    by_key = {(row["method"], row["train_seed"]): row for row in endpoints}
    deltas, effect_summary = [], []
    for name, (candidate, baseline) in CONTRASTS.items():
        values_by_metric = defaultdict(list)
        for seed in SEEDS:
            row = {"contrast": name, "candidate": candidate, "baseline": baseline, "train_seed": seed}
            for metric in METRICS:
                value = by_key[(candidate, seed)][metric] - by_key[(baseline, seed)][metric]
                row[f"delta_{metric}"] = value; values_by_metric[metric].append(value)
            deltas.append(row)
        for metric in METRICS:
            effect_summary.append({"contrast": name, "candidate": candidate, "baseline": baseline, "metric": metric, **summary(values_by_metric[metric])})
    interaction = []
    for metric in METRICS:
        semantic_fixed = next(row for row in effect_summary if row["contrast"] == "semantic_effect_fixed" and row["metric"] == metric)
        semantic_adaptive = next(row for row in effect_summary if row["contrast"] == "semantic_effect_adaptive" and row["metric"] == metric)
        interaction.append({"metric": metric, "difference_in_mean_semantic_effect": semantic_adaptive["mean"] - semantic_fixed["mean"],
                            "interpretation": "descriptive 2x2 interaction; training seed is the unit"})
    out.mkdir(parents=True)
    write_csv(out / "SEMANTIC_FACTORIAL_COMPLETION_ENDPOINTS.csv", endpoints)
    write_csv(out / "SEMANTIC_FACTORIAL_COMPLETION_COHORT_SUMMARY.csv", summary_rows)
    write_csv(out / "SEMANTIC_FACTORIAL_COMPLETION_PAIRED_DELTAS.csv", deltas)
    write_csv(out / "SEMANTIC_FACTORIAL_COMPLETION_EFFECT_SUMMARY.csv", effect_summary)
    write_csv(out / "SEMANTIC_FACTORIAL_COMPLETION_INTERACTION.csv", interaction)
    report = {"protocol": "DRTP-SEMANTIC-ABLATION-FACTORIAL-COMPLETION-10M-V1", "verdict": "SEMANTIC_FACTORIAL_COMPLETION_REPORTED",
              "primary_unit": "training_seed", "n_paired_training_seeds": 5, "arms": list(ARMS), "seed_registry": list(SEEDS),
              "design": {"topology_semantics": [False, True], "adaptive_update": [False, True], "same_endpoint_tape": True},
              "contrasts": CONTRASTS, "automatic_algorithm_revision": False, "automatic_continuation": False}
    (out / "SEMANTIC_FACTORIAL_COMPLETION_FINAL_REPORT.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (out / "SEMANTIC_FACTORIAL_COMPLETION_FINAL_REPORT.md").write_text(
        "# DRTP 语义与自适应析因消融\n\n`SEMANTIC_FACTORIAL_COMPLETION_REPORTED`\n\n"
        "四种方法在相同五个训练种子、相同 10M 预算和同一固定终点评价带下报告。训练种子是独立统计单位；"
        "结果应联合解读回报、下尾、成功、超时和碰撞。该报告不自动触发算法修订。\n", encoding="utf-8")
    print(json.dumps(report, indent=2))

if __name__ == "__main__": main()
'''


def build_preflight() -> str:
    return f'''
"""Validate the restored ablation cohort before training the two missing arms."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

SEEDS = {SEEDS!r}
OLD_ARMS = {OLD_ARMS!r}
NEW_ARMS = {NEW_ARMS!r}
EXPECTED_ARCHIVE_SHA256 = "{EXPECTED_EXISTING_SHA256}"
TAPE_PROTOCOL = "DRTP-SEMANTIC-ABLATION-NONPAIRED-TAPE-V1"
TAPE_IDS = list(range(800000, 800100))

def digest(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda:f.read(1024*1024), b""): h.update(block)
    return h.hexdigest()

def main():
    p=argparse.ArgumentParser(); p.add_argument("--existing-root", type=Path, required=True); p.add_argument("--output-root", type=Path, required=True); p.add_argument("--existing-archive", type=Path, required=True); p.add_argument("--execute", action="store_true"); a=p.parse_args()
    if not a.execute: raise SystemExit("explicit --execute is required")
    if a.output_root.exists(): raise FileExistsError(a.output_root)
    tape=json.loads((a.existing_root/"tape"/"tape_manifest.json").read_text(encoding="utf-8"))
    checks={{"existing_archive_sha256": digest(a.existing_archive)==EXPECTED_ARCHIVE_SHA256,
            "tape_exact": tape.get("protocol")==TAPE_PROTOCOL and tape.get("episode_ids")==TAPE_IDS and tape.get("training_access")=="forbidden",
            "fixed_and_random_completed": True, "new_arms_absent": True,
            "same_seed_registry": True, "no_existing_endpoint_overwrite": True}}
    for arm, mode in {{"fixed_drtp_sg":"fixed_drtp", "random_drtp_sg":"random_drtp"}}.items():
        for seed in SEEDS:
            run=a.existing_root/"runs"/arm/f"seed{{seed}}"; manifest=json.loads((run/"run_manifest.json").read_text(encoding="utf-8"))
            valid=manifest.get("status")=="completed" and manifest.get("seed")==seed and manifest.get("sampler_mode")==mode and manifest.get("updates")==39063 and manifest.get("environment_steps")==10000128 and manifest.get("tape_hash")==tape.get("tape_hash") and (run/"actor_critic_latest.pt").is_file()
            checks["fixed_and_random_completed"] &= valid
    for arm in NEW_ARMS:
        checks["new_arms_absent"] &= not (a.existing_root/"runs"/arm).exists()
    if not all(checks.values()): raise RuntimeError(json.dumps(checks, indent=2))
    report={{"protocol":"DRTP-SEMANTIC-ABLATION-FACTORIAL-COMPLETION-10M-V1","verdict":"SEMANTIC_FACTORIAL_COMPLETION_PREFLIGHT_PASS","checks":checks,"training_started":False,"evaluation_started":False,"automatic_algorithm_revision":False}}
    a.output_root.mkdir(parents=True); (a.output_root/"SEMANTIC_FACTORIAL_COMPLETION_PREFLIGHT.json").write_text(json.dumps(report, indent=2)+"\\n", encoding="utf-8"); print(json.dumps(report, indent=2))
if __name__=="__main__": main()
'''


def build_launcher() -> str:
    return r'''#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python}"
OUTPUT_ROOT="${OUTPUT_ROOT:-results/confirmatory/drtp_semantic_ablation_factorial_completion}"
EXISTING_ABLATION_ARCHIVE="${EXISTING_ABLATION_ARCHIVE:?set EXISTING_ABLATION_ARCHIVE to drtp_semantic_ablation_nonpaired_10m_results.tar.gz}"
MAX_PARALLEL="${MAX_PARALLEL:-10}"
CPU_THREADS_TOTAL="${CPU_THREADS_TOTAL:-20}"
[[ "$MAX_PARALLEL" -ge 1 && "$MAX_PARALLEL" -le 10 ]] || { echo "MAX_PARALLEL must be 1..10" >&2; exit 2; }
[[ ! -e "$OUTPUT_ROOT" ]] || { echo "output root already exists: $OUTPUT_ROOT" >&2; exit 2; }
[[ -f "$EXISTING_ABLATION_ARCHIVE" ]] || { echo "missing existing ablation archive: $EXISTING_ABLATION_ARCHIVE" >&2; exit 2; }
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}" MKL_NUM_THREADS="${MKL_NUM_THREADS:-1}" OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-1}" NUMEXPR_NUM_THREADS="${NUMEXPR_NUM_THREADS:-1}"

parent="$(dirname "$OUTPUT_ROOT")"
mkdir -p "$parent"
stage="$(mktemp -d "${parent}/semantic-factorial-stage.XXXXXX")"
trap 'test -d "$stage" && rmdir "$stage" 2>/dev/null || true' EXIT
tar -xzf "$EXISTING_ABLATION_ARCHIVE" -C "$stage"
[[ -d "$stage/drtp_semantic_ablation_nonpaired" ]] || { echo "unexpected existing-ablation archive layout" >&2; exit 2; }
mv "$stage/drtp_semantic_ablation_nonpaired" "$OUTPUT_ROOT"
rmdir "$stage"; trap - EXIT

"$PYTHON_BIN" scripts/verify_drtp_semantic_factorial_preflight.py --existing-root "$OUTPUT_ROOT" --existing-archive "$EXISTING_ABLATION_ARCHIVE" --output-root "$OUTPUT_ROOT/preflight_factorial" --execute
running=0
for arm in utr_sg drtp_sg; do
  for seed in 80011 80012 80013 80014 80015; do
    "$PYTHON_BIN" scripts/run_drtp_semantic_factorial_completion_single.py --arm "$arm" --seed "$seed" --output-root "$OUTPUT_ROOT" --execute > "$OUTPUT_ROOT/${arm}_${seed}.out" 2> "$OUTPUT_ROOT/${arm}_${seed}.err" &
    running=$((running+1)); if [[ "$running" -ge "$MAX_PARALLEL" ]]; then wait -n; running=$((running-1)); fi
  done
done
wait
printf '%s\n' '{"status":"SEMANTIC_FACTORIAL_COMPLETION_TRAINING_COMPLETE","new_trajectories":10,"reused_trajectories":10,"evaluation_started":false}' > "$OUTPUT_ROOT/SEMANTIC_FACTORIAL_COMPLETION_TRAINING_COMPLETE.json"
"$PYTHON_BIN" scripts/run_drtp_semantic_factorial_completion_evaluation.py --trained-root "$OUTPUT_ROOT" --output-root "$OUTPUT_ROOT/evaluations/factorial_completion_final_10m" --workers "$MAX_PARALLEL" --execute
"$PYTHON_BIN" scripts/aggregate_drtp_semantic_factorial_completion.py --evaluation-root "$OUTPUT_ROOT/evaluations/factorial_completion_final_10m" --output-root "$OUTPUT_ROOT" --execute
printf '%s\n' '{"status":"SEMANTIC_FACTORIAL_COMPLETION_COMPLETE","new_trajectories":10,"reused_trajectories":10,"endpoint_evaluation_completed":true,"automatic_algorithm_revision":false}' > "$OUTPUT_ROOT/SEMANTIC_FACTORIAL_COMPLETION_COMPLETE.json"
'''


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-archive", type=Path, default=SOURCE_ARCHIVE)
    parser.add_argument("--existing-results-archive", type=Path, default=RESULT_ARCHIVE)
    parser.add_argument("--output-package", type=Path, default=PACKAGE)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("explicit --execute is required")
    if args.output_package.exists() or args.output_package.with_suffix(args.output_package.suffix + ".sha256").exists():
        raise FileExistsError(f"refusing to overwrite {args.output_package}")
    if not args.source_archive.is_file() or not args.existing_results_archive.is_file():
        raise FileNotFoundError("both the frozen source archive and the completed ablation archive are required")
    if sha256(args.existing_results_archive) != EXPECTED_EXISTING_SHA256:
        raise RuntimeError("completed ablation archive SHA256 differs from the audited source")

    sampler_source = git_source("algorithms/ri_gmappo/drtp_semantic_ablation_sampler.py")
    expected_base = {
        "algorithms/ri_gmappo/simple_ri_gmappo.py": "b2ae085ed60e20007ee188a044a2dc53d7061d8f7451c562f15244aeeef33873",
        "algorithms/ri_gmappo/drtp_topology_sampler.py": "5fbd46ceb9673a0b613a695dd82f00f46df2705850811784e3048b2c0ce2e741",
        "envs/uav_intercept_3d_env.py": "06e378d34eb390d8095469e98c7c9d37b244e98d92b93b6b20c24edaa7cd29ff",
    }
    with tempfile.TemporaryDirectory(prefix="drtp-semantic-factorial-") as temp:
        temp_root = Path(temp)
        with ZipFile(args.source_archive) as archive:
            prefixes = {name.split("/", 1)[0] for name in archive.namelist() if "/" in name}
            if len(prefixes) != 1:
                raise RuntimeError("source archive must contain exactly one project root")
            prefix = prefixes.pop()
            for relative, expected in expected_base.items():
                if hashlib.sha256(source_member(archive, prefix, relative)).hexdigest() != expected:
                    raise RuntimeError(f"frozen source mismatch: {relative}")
            archive.extractall(temp_root)
        extracted = temp_root / prefix
        package_root = temp_root / "DRTP_SEMANTIC_ABLATION_FACTORIAL_COMPLETION_10M"
        extracted.rename(package_root)
        sampler_path = package_root / "algorithms" / "ri_gmappo" / "drtp_semantic_ablation_sampler.py"
        write(sampler_path, sampler_source)
        learner_path = package_root / "algorithms" / "ri_gmappo" / "simple_ri_gmappo.py"
        learner = learner_path.read_text(encoding="utf-8")
        learner = replace_once(learner,
            "from algorithms.ri_gmappo.drtp_topology_sampler import AnchoredEGTRTopologySampler, EGTRTopologySampler\n",
            "from algorithms.ri_gmappo.drtp_topology_sampler import AnchoredEGTRTopologySampler, EGTRTopologySampler\nfrom algorithms.ri_gmappo.drtp_semantic_ablation_sampler import SemanticAblationTopologySampler\n")
        learner = replace_once(learner,
            '{"none", "utr", "snr", "drtp", "pp_drtp", "r_drtp", "egtr", "anchored_egtr", "drtp_tr", "conservative_drtp"}',
            '{"none", "utr", "snr", "drtp", "pp_drtp", "r_drtp", "egtr", "anchored_egtr", "drtp_tr", "conservative_drtp", "random_drtp", "fixed_drtp"}')
        learner = replace_once(learner, "    if drtp_mode == \"egtr\":\n",
            "    if drtp_mode in {\"random_drtp\", \"fixed_drtp\"}:\n        drtp_sampler = SemanticAblationTopologySampler(drtp_mode, sampler_seed, sampler_updates)\n    elif drtp_mode == \"egtr\":\n")
        write(learner_path, learner)

        freeze = {
            "protocol": "DRTP-SEMANTIC-ABLATION-FACTORIAL-COMPLETION-10M-V1",
            "purpose": "Complete the existing two-arm ablation as a same-seed 2x2 design without retraining Fixed-DRTP or Random-DRTP.",
            "fresh_seed_registry": list(SEEDS),
            "reused_completed_arms": {"fixed_drtp_sg": "restored only", "random_drtp_sg": "restored only"},
            "newly_trained_arms": {"utr_sg": {"topology_semantic": False, "adaptive_update": False}, "drtp_sg": {"topology_semantic": True, "adaptive_update": True}},
            "all_arms": {"utr_sg": [False, False], "fixed_drtp_sg": [True, False], "random_drtp_sg": [False, True], "drtp_sg": [True, True]},
            "identical_controls": ["environment", "PPO", "actor", "critic", "reward", "observation", "action_interface", "failure_condition_library", "nominal_mass", "probability_bounds", "training_budget", "endpoint_evaluation_protocol"],
            "training": {"updates": 39063, "num_envs": 4, "rollout_steps": 64, "environment_steps": 10000128},
            "existing_results_archive_sha256": EXPECTED_EXISTING_SHA256,
            "source_archive_sha256": sha256(args.source_archive),
            "source_members_sha256": {**expected_base, "ablation_sampler": hashlib.sha256(sampler_source.encode("utf-8")).hexdigest(), "patched_learner": sha256(learner_path)},
            "endpoint": "fixed_final_10m_only", "primary_unit": "training_seed", "automatic_algorithm_revision": False, "automatic_continuation": False,
        }
        write(package_root / "configs" / "drtp_semantic_factorial_completion_freeze.json", json.dumps(freeze, indent=2) + "\n")
        write(package_root / "scripts" / "run_drtp_semantic_factorial_completion_single.py", build_runner())
        write(package_root / "scripts" / "run_drtp_semantic_factorial_completion_evaluation.py", build_evaluator())
        write(package_root / "scripts" / "aggregate_drtp_semantic_factorial_completion.py", build_aggregator())
        write(package_root / "scripts" / "verify_drtp_semantic_factorial_preflight.py", build_preflight())
        write(package_root / "scripts" / "launch_drtp_semantic_factorial_completion_autodl.sh", build_launcher())
        write(package_root / "README_FACTORIAL_COMPLETION.md", f"""
        # DRTP semantic factorial completion

        This package restores the audited Fixed-DRTP and Random-DRTP results archive (`{EXPECTED_EXISTING_SHA256}`),
        trains only UTR and original DRTP for the same seeds {list(SEEDS)}, then evaluates all four arms once on the
        same fixed tape. It does not modify, resume, or overwrite the restored ten trajectories.
        """)
        with ZipFile(args.output_package, "w", ZIP_DEFLATED) as archive:
            for path in package_root.rglob("*"):
                if path.is_file():
                    archive.write(path, path.relative_to(temp_root).as_posix())
    package_sha = sha256(args.output_package)
    args.output_package.with_suffix(args.output_package.suffix + ".sha256").write_text(
        f"{package_sha}  {args.output_package.name}\n", encoding="ascii"
    )
    print(json.dumps({"package": str(args.output_package), "sha256": package_sha,
                      "new_trajectories": 10, "reused_trajectories": 10,
                      "new_environment_steps": 100001280}, indent=2))


if __name__ == "__main__":
    main()
