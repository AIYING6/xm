"""Authorized, fixed K=3 E-UTR/E-DRTP 0.5M directional pilot."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import replace
from pathlib import Path
import statistics
import sys
import time

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]

from algorithms.ri_gmappo.reliability_ensemble import pooled_categorical_action
from algorithms.ri_gmappo.simple_ri_gmappo import stack_graphs, train_ri_gmappo
from envs.uav_intercept_3d_env import ACTION3D_TABLE
import run_drtp_sg_development_evaluation as base_evaluation
import run_drtp_sg_strict_10m_single as strict
import run_phase_fl_single as fl


FREEZE = ROOT / "configs" / "reliable_drtp_ensemble_p1_freeze.json"
TAPE = ROOT / "configs" / "reliable_drtp_ensemble_p1_tape.json"
ARMS = {"e_utr": "utr", "e_drtp": "drtp"}
FAILURE_CONDITIONS = ("F0_44_80", "T28_28_80", "D120_44_120", "C28_120")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_freeze() -> dict:
    return json.loads(FREEZE.read_text(encoding="utf-8"))


def read_tape() -> dict:
    tape = json.loads(TAPE.read_text(encoding="utf-8"))
    tape["episode_ids"] = list(range(int(tape["episode_start"]), int(tape["episode_start"]) + int(tape["episode_count"])))
    return tape


def tape_hash() -> str:
    return hashlib.sha256(
        json.dumps(read_tape(), sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def bundles() -> dict[str, dict[str, tuple[int, ...]]]:
    return {
        cohort: {name: tuple(seeds) for name, seeds in members.items()}
        for cohort, members in read_freeze()["cohorts"].items()
        if cohort in {"A", "B"}
    }


def all_seeds() -> tuple[int, ...]:
    return tuple(seed for cohort in bundles().values() for members in cohort.values() for seed in members)


def cohort_for_bundle(bundle: str) -> str:
    return "A" if bundle.startswith("A") else "B"


def training_config(arm: str, seed: int, out_dir: Path):
    if arm not in ARMS or seed not in all_seeds():
        raise ValueError("unauthorized ensemble P1 arm or seed")
    base = strict.training_config("utr_sg", strict.SEEDS[0], out_dir)
    return replace(
        base, seed=seed, updates=1953, save_interval=976,
        milestone_updates={976: "250k", 1953: "500k"}, out_dir=str(out_dir),
        drtp_sampler_mode=ARMS[arm], drtp_sampler_seed=seed,
        drtp_sampler_total_updates=1953, drtp_sampler_logging=True,
        runtime_state_checkpointing=True, runtime_state_save_interval=976,
        evaluation_enabled=False,
    )


def train(args: argparse.Namespace) -> None:
    freeze = read_freeze()
    if not args.execute or not freeze["authorization"]["member_training_authorized"]:
        raise RuntimeError("explicit frozen member-training authorization required")
    out = args.output_root / "runs" / args.arm / f"seed{args.seed}"
    if out.exists():
        raise FileExistsError(f"refusing rerun/overwrite: {out}")
    out.mkdir(parents=True, exist_ok=False)
    cfg = training_config(args.arm, args.seed, out)
    manifest = {
        "protocol": freeze["protocol"], "status": "running", "arm": args.arm,
        "sampler": ARMS[args.arm], "seed": args.seed, "updates": 1953,
        "environment_steps": 499968, "ensemble_member_only": True,
        "member_selection_uses_evaluation": False,
        "evaluation_enabled": False, "early_stopping": False,
        "checkpoint_promotion": False, "seed_replacement": False,
        "automatic_continuation": False, "distillation_enabled": False,
        "freeze_sha256": sha256(FREEZE), "tape_sha256": sha256(TAPE),
        "tape_hash": tape_hash(), "started_at": time.time(),
    }
    (out / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    try:
        train_ri_gmappo(cfg)
        required = [
            out / "actor_critic_milestone_250k.pt",
            out / "actor_critic_milestone_500k.pt",
            out / "actor_critic_runtime_state_milestone_500k.pt",
            out / "train_log.csv", out / "drtp_topology_sampler_log.csv",
        ]
        if not all(path.exists() for path in required):
            raise RuntimeError("missing required frozen trajectory artifact")
        manifest.update({
            "status": "completed", "completed_at": time.time(),
            "checkpoint_500k_sha256": sha256(out / "actor_critic_milestone_500k.pt"),
        })
    except BaseException as error:
        manifest.update({"status": "failed", "error": repr(error)})
        (out / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        raise
    (out / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def pooled_action(agents: list, obs: np.ndarray, share: np.ndarray, graph: dict) -> np.ndarray:
    device = next(agents[0].parameters()).device
    packed = stack_graphs([graph])
    tensors = (
        torch.as_tensor(obs[None], dtype=torch.float32, device=device),
        torch.as_tensor(packed["node_feat"], dtype=torch.float32, device=device),
        torch.as_tensor(packed["edge_feat"], dtype=torch.float32, device=device),
        torch.as_tensor(packed["role"], dtype=torch.long, device=device),
        torch.as_tensor(packed["adj"], dtype=torch.float32, device=device),
        torch.as_tensor(share[None], dtype=torch.float32, device=device),
    )
    relation = torch.as_tensor(packed["relation_adj"], dtype=torch.float32, device=device)
    intent = torch.as_tensor(packed["intent_label"], dtype=torch.long, device=device)
    with torch.no_grad():
        logits = [
            agent.actor(*tensors[:5], agent.num_agents, relation_adj=relation, intent_label=intent)[0]
            for agent in agents
        ]
        actions, _ = pooled_categorical_action(logits, deterministic=True)
    return actions.squeeze(0).cpu().numpy()


def evaluate_episode(agents: list, method: str, unit: str, cohort: str, episode_id: int, condition: dict) -> dict:
    spec = None if condition["name"] == "nominal" else (int(condition["start_step"]), int(condition["duration_steps"]))
    env = base_evaluation.variant_env(episode_id, spec)
    obs, share, graph = env.reset()
    reward_sum = control_effort = 0.0
    while True:
        actions = pooled_action(agents, obs, share, graph)
        control_effort += float(np.abs(ACTION3D_TABLE[actions, :2]).sum())
        obs, share, graph, rewards, dones, info = env.step(actions)
        reward_sum += float(np.sum(rewards))
        if np.all(dones):
            break
    return {
        "protocol": read_freeze()["protocol"], "method": method, "unit": unit, "cohort": cohort,
        "development_episode_id": episode_id, "condition": condition["name"], "J": reward_sum,
        "collision": float(info["collision"]), "timeout": float(info["timeout"]),
        "constraint_violation": float(info["constraint_violation"]),
        "terminal_step": int(info["step"]), "control_effort": control_effort,
    }


def evaluate_task(task: tuple[str, str, str, list[str], list[int], dict]) -> list[dict]:
    method, unit, cohort, checkpoint_strings, episode_ids, condition = task
    torch.set_num_threads(1)
    agents = [
        fl.build_agent({"graph_encoder": "single", "hidden_dim": 115}, Path(checkpoint), 1)
        for checkpoint in checkpoint_strings
    ]
    return [evaluate_episode(agents, method, unit, cohort, episode_id, condition) for episode_id in episode_ids]


def completed_run(output_root: Path, arm: str, seed: int) -> Path:
    run = output_root / "runs" / arm / f"seed{seed}"
    manifest = json.loads((run / "run_manifest.json").read_text(encoding="utf-8"))
    if manifest.get("status") != "completed" or manifest.get("tape_hash") != tape_hash():
        raise RuntimeError(f"invalid completed run: {run}")
    checkpoint = run / "actor_critic_milestone_500k.pt"
    if not checkpoint.exists():
        raise FileNotFoundError(checkpoint)
    return checkpoint


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def evaluate(args: argparse.Namespace) -> None:
    if not args.execute or not read_freeze()["authorization"]["development_evaluation_authorized"]:
        raise RuntimeError("explicit frozen evaluation authorization required")
    tape = read_tape()
    out = args.output_root / "evaluations" / "final_05m"
    if out.exists():
        raise FileExistsError(f"refusing overwrite: {out}")
    tasks = []
    for arm in ARMS:
        for seed in all_seeds():
            checkpoint = str(completed_run(args.output_root, arm, seed))
            for condition in tape["conditions"]:
                tasks.append((f"single_{arm}", f"seed{seed}", cohort_for_bundle("A" if seed <= 4609 else "B"), [checkpoint], tape["episode_ids"], condition))
        for cohort, named_bundles in bundles().items():
            for bundle, seeds in named_bundles.items():
                checkpoints = [str(completed_run(args.output_root, arm, seed)) for seed in seeds]
                for condition in tape["conditions"]:
                    tasks.append((arm, bundle, cohort, checkpoints, tape["episode_ids"], condition))
    out.mkdir(parents=True, exist_ok=False)
    workers = min(args.workers, len(tasks))
    total = len(tasks) * len(tape["episode_ids"])
    print(f"Reliable ensemble P1 evaluation: workers={workers}, cells={len(tasks)}, episodes={total}", flush=True)
    rows: list[dict] = []
    with ProcessPoolExecutor(max_workers=workers, mp_context=mp.get_context("spawn")) as pool:
        futures = [pool.submit(evaluate_task, task) for task in tasks]
        for future in as_completed(futures):
            rows.extend(future.result())
            print(f"Reliable ensemble P1 evaluation progress {len(rows)}/{total} ({100 * len(rows) / total:.2f}%)", flush=True)
    if len(rows) != total:
        raise RuntimeError("incomplete evaluation")
    rows.sort(key=lambda row: (row["method"], row["cohort"], row["unit"], row["condition"], row["development_episode_id"]))
    write_csv(out / "raw_episode_metrics.csv", rows)
    grouped: dict[tuple[str, str, str, str], list[dict]] = {}
    for row in rows:
        grouped.setdefault((row["method"], row["cohort"], row["unit"], row["condition"]), []).append(row)
    summary = []
    for (method, cohort, unit, condition), group in grouped.items():
        summary.append({
            "method": method, "cohort": cohort, "unit": unit, "condition": condition,
            "J": statistics.mean(float(row["J"]) for row in group),
            "collision": statistics.mean(float(row["collision"]) for row in group),
            "timeout": statistics.mean(float(row["timeout"]) for row in group),
            "constraint_violation": statistics.mean(float(row["constraint_violation"]) for row in group),
        })
    write_csv(out / "summary.csv", summary)
    (out / "evaluation_manifest.json").write_text(json.dumps({
        "protocol": read_freeze()["protocol"], "status": "completed", "raw_rows": len(rows),
        "workers": workers, "tape_hash": tape_hash(), "formal_tape_used": False,
        "independent_tape_used": False, "heldout_tape_used": False,
    }, indent=2) + "\n", encoding="utf-8")


def endpoint(rows: list[dict], method: str, cohort: str, unit: str) -> dict[str, float]:
    values = {row["condition"]: row for row in rows if row["method"] == method and row["cohort"] == cohort and row["unit"] == unit}
    required = {"nominal", *FAILURE_CONDITIONS}
    if set(values) != required:
        raise RuntimeError(f"incomplete endpoint: {method}/{cohort}/{unit}")
    return {
        "J_nominal": float(values["nominal"]["J"]),
        "J_pert_mean": statistics.mean(float(values[name]["J"]) for name in FAILURE_CONDITIONS),
        "J_pert_worst": min(float(values[name]["J"]) for name in FAILURE_CONDITIONS),
        "collision": statistics.mean(float(values[name]["collision"]) for name in FAILURE_CONDITIONS),
        "timeout": statistics.mean(float(values[name]["timeout"]) for name in FAILURE_CONDITIONS),
        "constraint": max(float(values[name]["constraint_violation"]) for name in FAILURE_CONDITIONS),
    }


def aggregate(args: argparse.Namespace) -> None:
    if not args.execute:
        raise RuntimeError("--execute required")
    evaluation = args.output_root / "evaluations" / "final_05m"
    manifest = json.loads((evaluation / "evaluation_manifest.json").read_text(encoding="utf-8"))
    if manifest.get("status") != "completed" or manifest.get("tape_hash") != tape_hash():
        raise RuntimeError("invalid evaluation manifest")
    with (evaluation / "summary.csv").open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    out = args.output_root / "diagnostics" / "reliable_ensemble_p1_gate"
    if out.exists():
        raise FileExistsError(f"refusing overwrite: {out}")
    freeze = read_freeze()
    epsilon, safety_margin = freeze["gate"]["epsilon_J"], freeze["gate"]["safety_margin"]
    cohort_reports = {}
    for cohort, named_bundles in bundles().items():
        bundle_rows, single_drtp_scores = [], []
        for bundle, seeds in named_bundles.items():
            utr, drtp = endpoint(rows, "e_utr", cohort, bundle), endpoint(rows, "e_drtp", cohort, bundle)
            gain = drtp["J_pert_mean"] - utr["J_pert_mean"]
            bundle_rows.append({
                "bundle": bundle, "members": list(seeds), "gain_e_drtp_vs_e_utr": gain,
                "e_utr": utr, "e_drtp": drtp,
                "catastrophic": gain < -epsilon,
                "safety_ok": drtp["collision"] - utr["collision"] <= safety_margin and drtp["timeout"] - utr["timeout"] <= safety_margin and drtp["constraint"] <= utr["constraint"],
            })
            single_drtp_scores.extend(endpoint(rows, "single_e_drtp", cohort, f"seed{seed}")["J_pert_mean"] for seed in seeds)
        ensemble_scores = [row["e_drtp"]["J_pert_mean"] for row in bundle_rows]
        gains = [row["gain_e_drtp_vs_e_utr"] for row in bundle_rows]
        criteria = {
            "positive_mean_gain_vs_e_utr": statistics.mean(gains) > 0,
            "no_catastrophic_bundle": not any(row["catastrophic"] for row in bundle_rows),
            "lower_tail_not_worse_than_members": min(ensemble_scores) >= min(single_drtp_scores) - epsilon,
            "upper_tail_retained_vs_members": max(ensemble_scores) >= max(single_drtp_scores) - epsilon,
            "safety": all(row["safety_ok"] for row in bundle_rows),
        }
        cohort_reports[cohort] = {
            "decision": "COHORT_DIRECTIONAL_GO" if all(criteria.values()) else "COHORT_NO_GO",
            "criteria": criteria, "mean_gain": statistics.mean(gains),
            "ensemble_range": max(ensemble_scores) - min(ensemble_scores),
            "single_member_range": max(single_drtp_scores) - min(single_drtp_scores),
            "bundles": bundle_rows,
        }
    decision = "RELIABILITY_ENSEMBLE_P1_DIRECTIONAL_GO" if all(report["decision"] == "COHORT_DIRECTIONAL_GO" for report in cohort_reports.values()) else "RELIABILITY_ENSEMBLE_P1_NO_GO"
    out.mkdir(parents=True)
    payload = {
        "decision": decision, "cohorts": cohort_reports, "independent_unit": "ensemble_bundle",
        "pooled_cohorts_for_inference": False, "distillation_started": False,
        "automatic_continuation_started": False, "mainline_a_modified": False,
    }
    (out / "RELIABILITY_ENSEMBLE_P1_DECISION.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    report = [
        "# Reliable-DRTP ensemble P1 gate", "",
        f"**Decision:** {decision}.", "",
        "The independent unit is the ensemble bundle. Cohorts were not pooled. No distillation, continuation, tuning, member replacement, or retry was started.", "",
    ]
    for cohort, value in cohort_reports.items():
        report.extend([f"## Cohort {cohort}", "", f"Decision: {value['decision']}. Mean E-DRTP minus E-UTR robust gain: {value['mean_gain']:.3f}.", "", "| Criterion | Result |", "| --- | --- |"])
        report.extend([f"| {name} | {result} |" for name, result in value["criteria"].items()])
        report.append("")
    (out / "RELIABILITY_ENSEMBLE_P1_REPORT.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(json.dumps({"decision": decision, "report": str(out / "RELIABILITY_ENSEMBLE_P1_REPORT.md")}, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("train", "evaluate", "aggregate"))
    parser.add_argument("--arm", choices=tuple(ARMS))
    parser.add_argument("--seed", type=int, choices=all_seeds())
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=9)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if args.mode == "train":
        if args.arm is None or args.seed is None:
            parser.error("train requires --arm and --seed")
        train(args)
    elif args.mode == "evaluate":
        evaluate(args)
    else:
        aggregate(args)


if __name__ == "__main__":
    main()
