"""Authorized C2 two-cohort pilot: train, fixed-tape evaluate, and gate."""

from __future__ import annotations

import argparse
import csv
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import replace
import hashlib
import json
import math
import multiprocessing as mp
from pathlib import Path
import statistics
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]

from algorithms.ri_gmappo.simple_ri_gmappo import train_ri_gmappo  # noqa: E402
import run_drtp_sg_development_evaluation as evaluation  # noqa: E402
import run_drtp_sg_strict_10m_single as strict  # noqa: E402


FREEZE = ROOT / "configs" / "drtp_c2_group_weighted_ppo_pilot_freeze.json"
TAPE = ROOT / "configs" / "drtp_c2_group_weighted_ppo_pilot_tape.json"
ARMS = ("utr_sg", "drtp_sg", "group_weighted_utr_sg")
CONDS = ("nominal", "F0_44_80", "T28_28_80", "D120_44_120", "C28_120")
FAIL = CONDS[1:]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tape() -> dict:
    payload = json.loads(TAPE.read_text(encoding="utf-8"))
    payload["episode_ids"] = list(range(int(payload["episode_start"]), int(payload["episode_start"]) + int(payload["episode_count"])))
    payload["tape_hash"] = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return payload


def seeds(freeze: dict) -> tuple[int, ...]:
    return tuple(int(seed) for cohort in ("A", "B") for seed in freeze["cohorts"][cohort])


def cohort(seed: int, freeze: dict) -> str:
    return "A" if seed in freeze["cohorts"]["A"] else "B"


def config(arm: str, seed: int, out_dir: Path, freeze: dict):
    base = strict.training_config("utr_sg", strict.SEEDS[0], out_dir)
    common = dict(
        seed=seed, updates=int(freeze["budget"]["updates"]), save_interval=976,
        milestone_updates={int(key): value for key, value in freeze["budget"]["milestones"].items()},
        out_dir=str(out_dir), evaluation_enabled=False, runtime_state_checkpointing=True,
        runtime_state_save_interval=976, actor_gradient_mode="standard", target_kl=None,
        policy_update_guard_mode="none", fixed_f0_probability=None,
        topology_curriculum_schedule="none", topology_curriculum_logging=False,
    )
    if arm == "drtp_sg":
        return replace(base, **common, drtp_sampler_mode="drtp", drtp_sampler_seed=seed,
                       drtp_sampler_total_updates=int(freeze["budget"]["updates"]),
                       fixed_stratified_topology_sampler=False, group_weighted_actor_enabled=False)
    weighted = arm == "group_weighted_utr_sg"
    candidate = freeze["candidate"]
    return replace(
        base, **common, drtp_sampler_mode="none", fixed_stratified_topology_sampler=True,
        fixed_stratified_topology_sampler_seed=seed, group_weighted_actor_enabled=weighted,
        group_weighted_actor_auto_lagged=weighted, group_weighted_actor_scores=None,
        group_weighted_actor_telemetry=False,
        group_weighted_actor_strength=float(candidate["failure_weight_strength"]),
        group_weighted_actor_min=float(candidate["failure_weight_min"]),
        group_weighted_actor_max=float(candidate["failure_weight_max"]),
    )


def train(arm: str, seed: int, output_root: Path, execute: bool) -> None:
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    if not execute or not freeze["authorization"]["training_authorized"]:
        raise RuntimeError("frozen C2 training authorization is required")
    if arm not in ARMS or seed not in seeds(freeze):
        raise ValueError("unfrozen C2 arm or seed")
    out = output_root / "runs" / arm / f"seed{seed}"
    if out.exists():
        raise FileExistsError(f"refusing rerun or overwrite: {out}")
    out.mkdir(parents=True, exist_ok=False)
    cfg = config(arm, seed, out, freeze)
    manifest = {
        "protocol": freeze["protocol"], "status": "running", "arm": arm, "seed": seed,
        "cohort": cohort(seed, freeze), "updates": cfg.updates,
        "environment_steps": cfg.updates * cfg.num_envs * cfg.rollout_steps,
        "fixed_stratified_topology_sampler": cfg.fixed_stratified_topology_sampler,
        "sampler": cfg.drtp_sampler_mode, "actor_gradient_mode": cfg.actor_gradient_mode,
        "group_weighted_actor_enabled": cfg.group_weighted_actor_enabled,
        "group_weighted_actor_auto_lagged": cfg.group_weighted_actor_auto_lagged,
        "group_weight_parameters": None if not cfg.group_weighted_actor_enabled else {
            "strength": cfg.group_weighted_actor_strength, "min": cfg.group_weighted_actor_min,
            "max": cfg.group_weighted_actor_max,
        },
        "freeze_sha256": sha256(FREEZE), "tape_sha256": sha256(TAPE), "tape_hash": tape()["tape_hash"],
        "early_stopping": False, "checkpoint_promotion": False, "seed_replacement": False,
        "performance_rerun": False, "automatic_continuation": False, "started_at": time.time(),
    }
    (out / "run_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    try:
        train_ri_gmappo(cfg)
        required = [out / "actor_critic_milestone_250k.pt", out / "actor_critic_milestone_500k.pt",
                    out / "actor_critic_runtime_state_milestone_500k.pt", out / "train_log.csv"]
        if cfg.fixed_stratified_topology_sampler:
            required.append(out / "fixed_stratified_topology_sampler_manifest.json")
        if arm == "drtp_sg":
            required.append(out / "drtp_topology_sampler_log.csv")
        if not all(path.is_file() and path.stat().st_size > 0 for path in required):
            raise RuntimeError("missing required frozen trajectory artifact")
        manifest.update({"status": "completed", "completed_at": time.time(),
                         "final_checkpoint_sha256": sha256(out / "actor_critic_latest.pt")})
    except BaseException as exc:
        manifest.update({"status": "failed", "error": repr(exc), "completed_at": time.time()})
        (out / "run_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        raise
    (out / "run_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "C2_TRAJECTORY_COMPLETED", "arm": arm, "seed": seed}, indent=2))


def evaluate(output_root: Path, workers: int, execute: bool) -> None:
    freeze, dev_tape = json.loads(FREEZE.read_text(encoding="utf-8")), tape()
    if not execute or not freeze["authorization"]["evaluation_authorized"]:
        raise RuntimeError("frozen C2 evaluation authorization is required")
    out = output_root / "evaluations" / "final_05m"
    if out.exists():
        raise FileExistsError(f"refusing evaluation overwrite: {out}")
    tasks = []
    for arm in ARMS:
        for seed in seeds(freeze):
            run = output_root / "runs" / arm / f"seed{seed}"
            manifest = json.loads((run / "run_manifest.json").read_text(encoding="utf-8"))
            if manifest.get("status") != "completed" or manifest.get("tape_hash") != dev_tape["tape_hash"]:
                raise RuntimeError(f"invalid C2 trajectory: {run}")
            tasks.append((arm, seed, str(run / "actor_critic_milestone_500k.pt"), "500k",
                          dev_tape["episode_ids"], dev_tape["conditions"], dev_tape["tape_hash"]))
    out.mkdir(parents=True, exist_ok=False)
    rows, done, total = [], 0, len(tasks) * len(dev_tape["conditions"]) * len(dev_tape["episode_ids"])
    print(f"C2 evaluation: workers={workers}, cells={len(tasks)}, episodes={total}", flush=True)
    with ProcessPoolExecutor(max_workers=min(workers, len(tasks)), mp_context=mp.get_context("spawn")) as pool:
        futures = [pool.submit(evaluation.evaluate_cell, task) for task in tasks]
        for future in as_completed(futures):
            rows.extend(future.result()); done = len(rows)
            print(f"C2 evaluation progress {done}/{total} ({100 * done / total:.2f}%)", flush=True)
    if len(rows) != total:
        raise RuntimeError("incomplete C2 evaluation")
    rows.sort(key=lambda row: (row["method"], int(row["train_seed"]), row["topology_condition"], int(row["development_episode_id"])))
    with (out / "raw_episode_metrics.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    summary = []
    for arm in ARMS:
        for seed in seeds(freeze):
            for condition in CONDS:
                cells = [row for row in rows if row["method"] == arm and int(row["train_seed"]) == seed and row["topology_condition"] == condition]
                summary.append({"method": arm, "train_seed": seed, "condition": condition,
                                **{key: sum(float(row[key]) for row in cells) / len(cells) for key in ("J", "collision", "timeout", "constraint_violation")}})
    with (out / "per_seed_condition_summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary[0])); writer.writeheader(); writer.writerows(summary)
    (out / "evaluation_manifest.json").write_text(json.dumps({"status": "completed", "raw_rows": len(rows), "tape_hash": dev_tape["tape_hash"], "checkpoint": "500k"}, indent=2) + "\n", encoding="utf-8")


def metrics(rows: list[dict], arm: str, seed: int) -> dict:
    values = {row["condition"]: row for row in rows if row["method"] == arm and int(row["train_seed"]) == seed}
    if set(values) != set(CONDS):
        raise RuntimeError(f"missing C2 condition rows for {arm}/{seed}")
    value = lambda condition, key="J": float(values[condition][key])
    return {"J_pert_mean": sum(value(c) for c in FAIL) / len(FAIL), "J_F0": value("F0_44_80"),
            "J_pert_worst": min(value(c) for c in FAIL), "collision": sum(value(c, "collision") for c in FAIL) / len(FAIL),
            "timeout": sum(value(c, "timeout") for c in FAIL) / len(FAIL),
            "constraint": max(value(c, "constraint_violation") for c in FAIL)}


def catastrophic(candidate: dict, utr: dict) -> bool:
    return candidate["J_pert_worst"] < 0.7 * utr["J_pert_worst"] and candidate["J_F0"] < 0.7 * utr["J_F0"]


def aggregate(output_root: Path, execute: bool) -> None:
    if not execute:
        raise RuntimeError("--execute required")
    freeze, dev_tape = json.loads(FREEZE.read_text(encoding="utf-8")), tape()
    evaluation_root = output_root / "evaluations" / "final_05m"
    manifest = json.loads((evaluation_root / "evaluation_manifest.json").read_text(encoding="utf-8"))
    report = output_root / "diagnostics" / "c2_group_weighted_ppo_gate"
    if report.exists() or manifest.get("status") != "completed" or manifest.get("tape_hash") != dev_tape["tape_hash"]:
        raise RuntimeError("invalid or previously aggregated C2 evaluation")
    with (evaluation_root / "per_seed_condition_summary.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    epsilon, safety = float(freeze["gate"]["epsilon_J"]), float(freeze["gate"]["safety_delta_limit"])
    def one(name: str) -> dict:
        results = []
        for seed in freeze["cohorts"][name]:
            utr, original, weighted = (metrics(rows, arm, seed) for arm in ARMS)
            results.append({"seed": seed, "gain_original": original["J_pert_mean"] - utr["J_pert_mean"], "gain_weighted": weighted["J_pert_mean"] - utr["J_pert_mean"],
                            "weighted_minus_original": weighted["J_pert_mean"] - original["J_pert_mean"],
                            "original_catastrophic": catastrophic(original, utr), "weighted_catastrophic": catastrophic(weighted, utr),
                            "weighted": weighted, "original": original, "utr": utr})
        original_gains, weighted_gains = [row["gain_original"] for row in results], [row["gain_weighted"] for row in results]
        criteria = {
            "positive_mean_gain_vs_utr": statistics.mean(weighted_gains) > 0.0,
            "at_least_three_nonnegative_gains": sum(gain >= 0.0 for gain in weighted_gains) >= 3,
            "no_new_catastrophic": sum(row["weighted_catastrophic"] for row in results) <= sum(row["original_catastrophic"] for row in results),
            "range_not_larger": max(weighted_gains) - min(weighted_gains) <= max(original_gains) - min(original_gains),
            "sample_sd_not_larger": statistics.stdev(weighted_gains) <= statistics.stdev(original_gains),
            "mean_retained_vs_original": statistics.mean(row["weighted_minus_original"] for row in results) >= -epsilon,
            "upper_tail_retained": all(row["weighted_minus_original"] >= -epsilon for row in results if row["gain_original"] > epsilon),
            "safety": all(row["weighted"]["collision"] - row["utr"]["collision"] <= safety and row["weighted"]["timeout"] - row["utr"]["timeout"] <= safety and row["weighted"]["constraint"] <= row["utr"]["constraint"] for row in results),
        }
        return {"decision": "COHORT_PASS" if all(criteria.values()) else "COHORT_FAIL", "criteria": criteria, "seed_results": results,
                "original_dispersion": {"range": max(original_gains) - min(original_gains), "sample_sd": statistics.stdev(original_gains)},
                "weighted_dispersion": {"range": max(weighted_gains) - min(weighted_gains), "sample_sd": statistics.stdev(weighted_gains)}}
    A, B = one("A"), one("B")
    verdict = "C2_EARLY_GO" if A["decision"] == B["decision"] == "COHORT_PASS" else "C2_NO_GO"
    report.mkdir(parents=True, exist_ok=False)
    payload = {"protocol": freeze["protocol"], "verdict": verdict, "cohort_A": A, "cohort_B": B,
               "pooled_n10_descriptive_only": True, "automatic_continuation_started": False, "mainline_a_modified": False}
    (report / "C2_GATE_DECISION.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    (report / "C2_GATE_REPORT.md").write_text(
        f"# C2 group-weighted PPO two-cohort gate\n\n**Verdict:** `{verdict}`.\n\n"
        f"Cohort A: `{A['decision']}`; Cohort B: `{B['decision']}`. Both cohorts were judged separately; pooled n=10 is descriptive only.\n\n"
        f"No continuation, rerun, weight tuning, or Mainline A modification was started.\n", encoding="utf-8")
    print(json.dumps({"verdict": verdict, "report": str(report / "C2_GATE_REPORT.md")}, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("train", "evaluate", "aggregate"))
    parser.add_argument("--arm", choices=ARMS)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=9)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if args.mode == "train":
        if args.arm is None or args.seed is None:
            parser.error("train requires --arm and --seed")
        train(args.arm, args.seed, args.output_root, args.execute)
    elif args.mode == "evaluate":
        evaluate(args.output_root, args.workers, args.execute)
    else:
        aggregate(args.output_root, args.execute)


if __name__ == "__main__":
    main()
