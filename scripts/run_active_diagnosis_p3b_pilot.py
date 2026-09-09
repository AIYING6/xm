"""Staged P3B pilot: common prefix, value calibration, then frozen arms.

The command refuses to start arm-specific training unless the common-prefix
calibration demonstrates a decision-relevant balanced-prior cell and adequate
held-out gate-decision agreement.  Evaluation remains a separate command.
"""

from __future__ import annotations

import argparse
import copy
import csv
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from algorithms.active_diagnosis.pilot_runner import (
    PILOT_ARMS,
    ActiveDiagnosisPPOConfig,
    calibrate_task_value_estimator,
    collect_rollout,
    evaluate_episode,
    make_runtime,
    runtime_state_dict,
    update_from_rollout,
)
from algorithms.active_diagnosis.recurrent_sg_mappo import RecurrentSGMAPPO
from algorithms.active_diagnosis.task_value_estimator import (
    TaskValueEstimator,
    TaskValueReplayBuffer,
    task_value_checkpoint,
)
from envs.active_diagnosis_semantic_env import RECOVERABLE_RANGE_LOSS
from envs.active_diagnosis_trainable_uav_env import (
    ActiveDiagnosisTrainableConfig,
    ActiveDiagnosisTrainableUAVEnv,
    HARD_TERMINAL_COMM_FAILURE,
)


PROTOCOL = "ACTIVE-DIAGNOSIS-P3B-PILOT-V1"
FROZEN_SEEDS = (83011, 83012, 83013)
NUM_ENVS = 4
PREFIX_UPDATES = 976
ARM_UPDATES = 2931
HIDDEN_DIM = 96
ROLE_DIM = 8


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _environment_set(seed: int) -> list[ActiveDiagnosisTrainableUAVEnv]:
    hypotheses = (RECOVERABLE_RANGE_LOSS, HARD_TERMINAL_COMM_FAILURE) * 2
    return [
        ActiveDiagnosisTrainableUAVEnv(ActiveDiagnosisTrainableConfig(hypothesis, seed * 100 + index))
        for index, hypothesis in enumerate(hypotheses)
    ]


def _agent_and_estimator(device: torch.device):
    probe = ActiveDiagnosisTrainableUAVEnv()
    agent = RecurrentSGMAPPO(
        probe.obs_dim, probe.share_obs_dim, probe.action_dim,
        hidden_dim=HIDDEN_DIM, role_dim=ROLE_DIM,
    ).to(device)
    estimator = TaskValueEstimator(probe.obs_dim, hidden_dim=64).to(device)
    return agent, estimator, probe.obs_dim


def _config(updates: int) -> ActiveDiagnosisPPOConfig:
    del updates
    return ActiveDiagnosisPPOConfig(
        rollout_steps=64, bptt_horizon=16, gamma=0.99, gae_lambda=0.95,
        clip_coef=0.2, entropy_coef=0.01, value_coef=0.5,
        max_grad_norm=0.5, ppo_epochs=4,
    )


def _assert_seed(seed: int) -> None:
    if seed not in FROZEN_SEEDS:
        raise ValueError(f"seed {seed} is outside the frozen pilot set")


def train_prefix(seed: int, output_root: Path, updates: int = PREFIX_UPDATES) -> Path:
    _assert_seed(seed)
    output = output_root / "prefix" / f"seed{seed}"
    if output.exists():
        raise FileExistsError(f"refusing to overwrite {output}")
    output.mkdir(parents=True)
    torch.manual_seed(seed); np.random.seed(seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    agent, _, gate_state_dim = _agent_and_estimator(device)
    optimizer = torch.optim.Adam(agent.parameters(), lr=3e-4)
    envs = _environment_set(seed)
    runtime = make_runtime(
        "recurrent_mappo", envs, agent, recoverable_prior=0.5,
        device=device, seed_base=seed * 1_000_000,
    )
    replay = TaskValueReplayBuffer(gate_state_dim, capacity=4096, seed=seed)
    unused_estimator = TaskValueEstimator(gate_state_dim, hidden_dim=64).to(device)
    cfg = _config(updates)
    with (output / "train_log.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=(
            "update", "environment_steps", "mean_reward", "actor_loss",
            "value_loss", "gradient_norm", "controlled_fraction",
        ))
        writer.writeheader()
        for update in range(1, updates + 1):
            batch = collect_rollout(agent, unused_estimator, replay, runtime, cfg, device=device)
            metrics = update_from_rollout(agent, optimizer, batch, cfg, device=device)
            row = {
                "update": update,
                "environment_steps": update * NUM_ENVS * cfg.rollout_steps,
                "mean_reward": float(batch["rewards"].mean()),
                **metrics,
            }
            if not all(math.isfinite(float(value)) for key, value in row.items() if key != "update"):
                raise FloatingPointError(row)
            writer.writerow(row); stream.flush()
    torch.save({
        "format": f"{PROTOCOL}-COMMON-PREFIX",
        "seed": seed,
        "updates": updates,
        "environment_steps": updates * NUM_ENVS * cfg.rollout_steps,
        "model": agent.state_dict(),
        "optimizer": optimizer.state_dict(),
        "runtime_at_split_discarded": True,
    }, output / "prefix_checkpoint.pt")
    _write_json(output / "run_manifest.json", {
        "protocol": PROTOCOL, "stage": "common_prefix", "seed": seed,
        "status": "completed", "updates": updates,
        "environment_steps": updates * NUM_ENVS * cfg.rollout_steps,
        "performance_evaluation_started": False,
    })
    return output


def run_calibration(seed: int, output_root: Path, geometry_count: int = 16) -> Path:
    _assert_seed(seed)
    if geometry_count < 4:
        raise ValueError("calibration requires at least four geometry seeds")
    prefix_path = output_root / "prefix" / f"seed{seed}" / "prefix_checkpoint.pt"
    if not prefix_path.is_file():
        raise FileNotFoundError(prefix_path)
    output = output_root / "calibration" / f"seed{seed}"
    if output.exists():
        raise FileExistsError(f"refusing to overwrite {output}")
    output.mkdir(parents=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    agent, estimator, _ = _agent_and_estimator(device)
    prefix = torch.load(prefix_path, map_location=device, weights_only=False)
    agent.load_state_dict(prefix["model"])
    optimizer = torch.optim.Adam(estimator.parameters(), lr=3e-4)
    geometry_seeds = [seed * 1000 + index for index in range(geometry_count)]
    train_count = geometry_count * 3 // 4
    report = calibrate_task_value_estimator(
        agent, estimator, optimizer, geometry_seeds=geometry_seeds,
        train_geometry_count=train_count, gradient_steps=600, device=device,
    )
    quality_checks = {
        "full_64_episode_factorial": report["episodes"] == 64 if geometry_count == 16 else report["episodes"] == 4 * geometry_count,
        "actor_unchanged": not report["actor_parameters_changed"],
        "no_ppo_updates": report["ppo_updates"] == 0,
        "finite_validation_error": math.isfinite(report["validation_mean_absolute_error"]),
        "heldout_gate_decision_agreement_at_least_75_percent": report["validation_gate_decision_agreement"] >= 0.75,
        "balanced_prior_contains_decision_relevant_cases": report["decision_relevant_balanced_prior_present"],
    }
    quality_pass = all(quality_checks.values())
    serializable_report = {
        key: value for key, value in report.items() if key not in {"replay", "records"}
    }
    serializable_report.update({
        "quality_checks": quality_checks,
        "quality_verdict": "TASK_VALUE_CALIBRATION_PASS" if quality_pass else "TASK_VALUE_CALIBRATION_STOP",
        "arm_specific_training_authorized": quality_pass,
    })
    _write_json(output / "calibration_report.json", serializable_report)
    torch.save({
        "format": f"{PROTOCOL}-TASK-VALUE-CALIBRATION",
        "seed": seed,
        "prefix_model": copy.deepcopy(prefix["model"]),
        "prefix_optimizer": copy.deepcopy(prefix["optimizer"]),
        "task_value": task_value_checkpoint(estimator, optimizer, report["replay"]),
        "quality_pass": quality_pass,
    }, output / "calibration_checkpoint.pt")
    return output


def train_arm(seed: int, arm: str, output_root: Path, updates: int = ARM_UPDATES) -> Path:
    _assert_seed(seed)
    if arm not in PILOT_ARMS:
        raise ValueError(arm)
    calibration_path = output_root / "calibration" / f"seed{seed}" / "calibration_checkpoint.pt"
    if not calibration_path.is_file():
        raise FileNotFoundError(calibration_path)
    output = output_root / "runs" / arm / f"seed{seed}"
    if output.exists():
        raise FileExistsError(f"refusing to overwrite {output}")
    output.mkdir(parents=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    agent, estimator, gate_state_dim = _agent_and_estimator(device)
    calibration = torch.load(calibration_path, map_location=device, weights_only=False)
    if not calibration["quality_pass"]:
        raise RuntimeError("calibration STOP forbids arm-specific performance training")
    agent.load_state_dict(calibration["prefix_model"])
    estimator.load_state_dict(calibration["task_value"]["model"])
    estimator.eval()
    for parameter in estimator.parameters():
        parameter.requires_grad_(False)
    optimizer = torch.optim.Adam(agent.parameters(), lr=3e-4)
    optimizer.load_state_dict(calibration["prefix_optimizer"])
    envs = _environment_set(seed + 1000)
    runtime = make_runtime(
        arm, envs, agent, recoverable_prior=0.5,
        device=device, seed_base=(seed + 1000) * 1_000_000,
    )
    task_replay = TaskValueReplayBuffer(gate_state_dim, capacity=4096, seed=seed + 1000)
    cfg = _config(updates)
    with (output / "train_log.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=(
            "update", "logical_total_updates", "logical_environment_steps", "mean_reward",
            "actor_loss", "value_loss", "gradient_norm", "controlled_fraction", "completed_episodes",
        ))
        writer.writeheader()
        for local_update in range(1, updates + 1):
            batch = collect_rollout(agent, estimator, task_replay, runtime, cfg, device=device)
            metrics = update_from_rollout(agent, optimizer, batch, cfg, device=device)
            logical_update = PREFIX_UPDATES + local_update
            writer.writerow({
                "update": local_update,
                "logical_total_updates": logical_update,
                "logical_environment_steps": logical_update * NUM_ENVS * cfg.rollout_steps,
                "mean_reward": float(batch["rewards"].mean()),
                **metrics,
                "completed_episodes": runtime.completed_episodes,
            })
            stream.flush()
    torch.save(agent.state_dict(), output / "actor_critic_latest.pt")
    torch.save({
        "format": f"{PROTOCOL}-ARM-RUNTIME",
        "seed": seed, "arm": arm, "local_updates": updates,
        "logical_total_updates": PREFIX_UPDATES + updates,
        "model": agent.state_dict(), "optimizer": optimizer.state_dict(),
        "runtime": runtime_state_dict(runtime),
        "task_value_model": estimator.state_dict(),
        "task_replay": task_replay.state_dict(),
    }, output / "runtime_checkpoint_latest.pt")
    _write_json(output / "run_manifest.json", {
        "protocol": PROTOCOL, "stage": "arm_specific", "seed": seed, "arm": arm,
        "status": "completed", "prefix_updates": PREFIX_UPDATES,
        "arm_updates": updates, "logical_total_updates": PREFIX_UPDATES + updates,
        "logical_environment_steps": (PREFIX_UPDATES + updates) * NUM_ENVS * cfg.rollout_steps,
        "checkpoint_selection": "fixed_endpoint_only", "evaluation_started": False,
    })
    return output


def evaluate_arm(seed: int, arm: str, output_root: Path, episodes_per_cell: int = 100) -> Path:
    _assert_seed(seed)
    if arm not in PILOT_ARMS:
        raise ValueError(arm)
    run = output_root / "runs" / arm / f"seed{seed}"
    checkpoint = run / "actor_critic_latest.pt"
    calibration_path = output_root / "calibration" / f"seed{seed}" / "calibration_checkpoint.pt"
    if not checkpoint.is_file() or not calibration_path.is_file():
        raise FileNotFoundError("fixed endpoint or calibration checkpoint is missing")
    output = output_root / "evaluations" / arm
    output.mkdir(parents=True, exist_ok=True)
    destination = output / f"seed{seed}_fixed_1m.csv"
    if destination.exists():
        raise FileExistsError(f"refusing to overwrite {destination}")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    agent, estimator, _ = _agent_and_estimator(device)
    agent.load_state_dict(torch.load(checkpoint, map_location=device, weights_only=True))
    calibration = torch.load(calibration_path, map_location=device, weights_only=False)
    estimator.load_state_dict(calibration["task_value"]["model"])
    agent.eval(); estimator.eval()
    cells = (
        (0.5, RECOVERABLE_RANGE_LOSS, 850000),
        (0.5, HARD_TERMINAL_COMM_FAILURE, 850100),
        (0.9, RECOVERABLE_RANGE_LOSS, 850200),
        (0.9, HARD_TERMINAL_COMM_FAILURE, 850300),
    )
    fields = (
        "protocol", "arm", "training_seed", "recoverable_prior", "hypothesis",
        "episode_id", "return", "success", "timeout", "collision",
        "constraint_violation", "steps", "probe_count", "fallback_count",
    )
    with destination.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields); writer.writeheader()
        for prior, hypothesis, first_id in cells:
            for offset in range(episodes_per_cell):
                episode_id = first_id + offset
                metrics = evaluate_episode(
                    agent, estimator, arm=arm, hypothesis=hypothesis,
                    seed=episode_id, recoverable_prior=prior, device=device,
                )
                writer.writerow({
                    "protocol": PROTOCOL, "arm": arm, "training_seed": seed,
                    "recoverable_prior": prior, "hypothesis": hypothesis,
                    "episode_id": episode_id, **metrics,
                })
                stream.flush()
    return destination


def aggregate(output_root: Path) -> Path:
    rows = []
    for arm in PILOT_ARMS:
        for seed in FROZEN_SEEDS:
            path = output_root / "evaluations" / arm / f"seed{seed}_fixed_1m.csv"
            if not path.is_file():
                raise FileNotFoundError(path)
            with path.open(newline="", encoding="utf-8") as stream:
                rows.extend(csv.DictReader(stream))
    metric_names = ("return", "success", "timeout", "collision", "constraint_violation", "probe_count")
    per_seed = []
    for arm in PILOT_ARMS:
        for seed in FROZEN_SEEDS:
            for prior in (0.5, 0.9):
                selected = [
                    row for row in rows
                    if row["arm"] == arm and int(row["training_seed"]) == seed
                    and float(row["recoverable_prior"]) == prior
                ]
                by_hypothesis = {
                    hypothesis: [row for row in selected if row["hypothesis"] == hypothesis]
                    for hypothesis in (RECOVERABLE_RANGE_LOSS, HARD_TERMINAL_COMM_FAILURE)
                }
                summary = {"arm": arm, "training_seed": seed, "recoverable_prior": prior}
                for metric in metric_names:
                    recoverable = float(np.mean([float(row[metric]) for row in by_hypothesis[RECOVERABLE_RANGE_LOSS]]))
                    hard = float(np.mean([float(row[metric]) for row in by_hypothesis[HARD_TERMINAL_COMM_FAILURE]]))
                    summary[f"expected_{metric}"] = prior * recoverable + (1.0 - prior) * hard
                    summary[f"recoverable_{metric}"] = recoverable
                    summary[f"hard_{metric}"] = hard
                per_seed.append(summary)
    diagnostics = output_root / "diagnostics" / "final_1m"
    diagnostics.mkdir(parents=True, exist_ok=True)
    per_seed_path = diagnostics / "P3B_PER_SEED_ENDPOINTS.csv"
    with per_seed_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(per_seed[0])); writer.writeheader(); writer.writerows(per_seed)
    method_rows = []
    for arm in PILOT_ARMS:
        for prior in (0.5, 0.9):
            selected = [row for row in per_seed if row["arm"] == arm and row["recoverable_prior"] == prior]
            values = np.asarray([row["expected_return"] for row in selected], dtype=np.float64)
            method_rows.append({
                "arm": arm, "recoverable_prior": prior, "training_seeds": len(values),
                "mean_return": float(values.mean()), "median_return": float(np.median(values)),
                "worst_seed_return": float(values.min()), "sample_sd_return": float(values.std(ddof=1)),
                "mean_success": float(np.mean([row["expected_success"] for row in selected])),
                "mean_timeout": float(np.mean([row["expected_timeout"] for row in selected])),
                "mean_collision": float(np.mean([row["expected_collision"] for row in selected])),
                "mean_constraint_violation": float(np.mean([row["expected_constraint_violation"] for row in selected])),
                "mean_probe_count": float(np.mean([row["expected_probe_count"] for row in selected])),
            })
    summary_path = diagnostics / "P3B_METHOD_SUMMARY.csv"
    with summary_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(method_rows[0])); writer.writeheader(); writer.writerows(method_rows)
    _write_json(diagnostics / "P3B_FINAL_REPORT.json", {
        "protocol": PROTOCOL,
        "verdict": "P3B_FIXED_ENDPOINT_REPORTED",
        "independent_unit": "training_seed",
        "training_seeds": list(FROZEN_SEEDS),
        "priors_reported_separately": True,
        "automatic_algorithm_revision": False,
    })
    return diagnostics


def preflight(output_root: Path) -> dict[str, Any]:
    freeze = json.loads((ROOT / "configs" / "active_diagnosis_p3b_pilot_freeze.json").read_text())
    return {
        "protocol": PROTOCOL,
        "verdict": "P3B_STAGED_RUNNER_IMPLEMENTED",
        "output_root": str(output_root),
        "arms": list(PILOT_ARMS),
        "seeds": list(FROZEN_SEEDS),
        "common_prefix_updates": PREFIX_UPDATES,
        "arm_specific_updates": ARM_UPDATES,
        "logical_total_updates": PREFIX_UPDATES + ARM_UPDATES,
        "logical_environment_steps": (PREFIX_UPDATES + ARM_UPDATES) * NUM_ENVS * 64,
        "calibration_quality_stop_enforced": True,
        "freeze_status": freeze["status"],
        "training_started": False,
        "evaluation_started": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("preflight", "prefix", "calibrate", "train-arm", "evaluate", "aggregate"))
    parser.add_argument("--seed", type=int)
    parser.add_argument("--arm", choices=PILOT_ARMS)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--updates", type=int)
    parser.add_argument("--geometry-count", type=int, default=16)
    parser.add_argument("--episodes-per-cell", type=int, default=100)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if args.command == "preflight":
        print(json.dumps(preflight(args.output_root), indent=2))
        return
    if not args.execute:
        raise SystemExit("refusing to execute training/calibration without --execute")
    if args.command == "aggregate":
        aggregate(args.output_root)
        return
    if args.seed is None:
        raise SystemExit("stage requires --seed")
    if args.command == "prefix":
        train_prefix(args.seed, args.output_root, args.updates or PREFIX_UPDATES)
    elif args.command == "calibrate":
        run_calibration(args.seed, args.output_root, args.geometry_count)
    elif args.command == "train-arm":
        if args.arm is None:
            raise SystemExit("train-arm requires --arm")
        train_arm(args.seed, args.arm, args.output_root, args.updates or ARM_UPDATES)
    else:
        if args.arm is None:
            raise SystemExit("evaluate requires --arm")
        evaluate_arm(args.seed, args.arm, args.output_root, args.episodes_per_cell)


if __name__ == "__main__":
    main()
