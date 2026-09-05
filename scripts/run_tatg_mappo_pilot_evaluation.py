"""Fixed endpoint-only evaluation for the completed four-arm TATG pilot.

This interface deliberately owns no optimiser, training loop, resume path or
checkpoint selector.  It reads only each registered ``actor_critic_latest.pt``
after the frozen update-3907 endpoint and evaluates it on the frozen
development tape.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import multiprocessing as mp
import sys
from dataclasses import replace
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.simple_ri_gmappo import (  # noqa: E402
    RIGMAPPOAgent,
    load_matching_state_dict,
    make_env,
    stack_graphs,
)
from algorithms.ri_gmappo.tatg_outer_rollout import TATGActorCriticSystem  # noqa: E402
from algorithms.ri_gmappo.tatg_sequence_runner import TATGSequenceActorRunner  # noqa: E402
from envs.uav_intercept_3d_env import ACTION3D_TABLE  # noqa: E402
from scripts.run_tatg_mappo_pilot_single import (  # noqa: E402
    ALL_ARMS,
    BASELINE_ARM,
    FROZEN_SEEDS,
    TEMPORAL_ARMS,
    _build_snapshot,
    pilot_config,
)


FREEZE = ROOT / "configs" / "tatg_mappo_pilot_p4_evaluation_freeze.json"
TAPE = ROOT / "configs" / "tatg_mappo_pilot_development_tape.json"
PROTOCOL = "TATG-MAPPO-FRESH-SEED-PILOT-P4-FIXED-ENDPOINT-EVALUATION-V1"
EXPECTED_UPDATES = 3907
EXPECTED_STEPS = 1_000_192


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def evaluation_env_config(arm: str, train_seed: int, episode_id: int, condition: dict[str, Any]):
    base = pilot_config(arm, train_seed, "evaluation-unused-output")
    nominal = str(condition["name"]) == "nominal"
    return replace(
        base,
        failed_blue_agent=-1 if nominal else int(condition["failed_blue_agent"]),
        node_failure_start_step=0 if nominal else int(condition["start_step"]),
        node_failure_duration_steps=0 if nominal else int(condition["duration_steps"]),
    ), int(episode_id)


def build_snapshot_agent(arm: str, train_seed: int, checkpoint: Path, device: torch.device) -> RIGMAPPOAgent:
    cfg, probe_seed = evaluation_env_config(arm, train_seed, 0, {"name": "nominal"})
    env = make_env(cfg, probe_seed, training=False)
    obs, share_obs, graph = env.reset()
    agent = _build_snapshot(graph, obs, share_obs, env, cfg).to(device)
    load_matching_state_dict(agent, str(checkpoint), device)
    agent.eval()
    return agent


def build_temporal_system(arm: str, train_seed: int, checkpoint: Path, device: torch.device) -> TATGActorCriticSystem:
    cfg = pilot_config(arm, train_seed, "evaluation-unused-output")
    env = make_env(cfg, 0, training=False)
    obs, share_obs, graph = env.reset()
    snapshot = _build_snapshot(graph, obs, share_obs, env, cfg)
    system = TATGActorCriticSystem(snapshot, memory_kind=TEMPORAL_ARMS[arm]).to(device)
    payload = torch.load(checkpoint, map_location=device, weights_only=False)
    system.load_state_dict(payload, strict=True)
    system.eval()
    return system


def snapshot_action(agent: RIGMAPPOAgent, obs: np.ndarray, share_obs: np.ndarray, graph: dict[str, np.ndarray]) -> np.ndarray:
    device = next(agent.parameters()).device
    packed = stack_graphs([graph])
    with torch.no_grad():
        actions, *_ = agent.get_action_and_value(
            torch.as_tensor(obs[None], dtype=torch.float32, device=device),
            torch.as_tensor(packed["node_feat"], dtype=torch.float32, device=device),
            torch.as_tensor(packed["edge_feat"], dtype=torch.float32, device=device),
            torch.as_tensor(packed["role"], dtype=torch.long, device=device),
            torch.as_tensor(packed["adj"], dtype=torch.float32, device=device),
            torch.as_tensor(share_obs[None], dtype=torch.float32, device=device),
            relation_adj=torch.as_tensor(packed["relation_adj"], dtype=torch.float32, device=device),
            deterministic=True,
            intent_label=torch.as_tensor(packed["intent_label"], dtype=torch.long, device=device),
        )
    return actions.squeeze(0).cpu().numpy()


def temporal_action(runner: TATGSequenceActorRunner, obs: np.ndarray, graph: dict[str, np.ndarray], device: torch.device) -> np.ndarray:
    with torch.no_grad():
        step = runner.act(
            torch.as_tensor(obs[None], dtype=torch.float32, device=device),
            torch.as_tensor(graph["node_feat"][None], dtype=torch.float32, device=device),
            torch.as_tensor(graph["edge_feat"][None], dtype=torch.float32, device=device),
            torch.as_tensor(graph["role"][None], dtype=torch.long, device=device),
            torch.as_tensor(graph["adj"][None], dtype=torch.float32, device=device),
            torch.as_tensor(graph["relation_adj"][None], dtype=torch.float32, device=device),
            deterministic=True,
        )
    return step.actions.squeeze(0).cpu().numpy()


def episode(arm: str, train_seed: int, policy: RIGMAPPOAgent | TATGActorCriticSystem, checkpoint_hash: str, episode_id: int, condition: dict[str, Any], device: torch.device) -> dict[str, Any]:
    cfg, reset_seed = evaluation_env_config(arm, train_seed, episode_id, condition)
    env = make_env(cfg, reset_seed, training=False)
    obs, share_obs, graph = env.reset()
    if arm == BASELINE_ARM:
        runner = None
    else:
        runner = TATGSequenceActorRunner(
            policy.temporal_actor,
            torch.as_tensor(graph["relation_adj"][None], dtype=torch.float32, device=device),
            torch.as_tensor(graph["edge_feat"][None], dtype=torch.float32, device=device),
        )
    reward_sum = 0.0
    control_effort = 0.0
    while True:
        if runner is None:
            actions = snapshot_action(policy, obs, share_obs, graph)  # type: ignore[arg-type]
        else:
            actions = temporal_action(runner, obs, graph, device)
        control_effort += float(np.abs(ACTION3D_TABLE[actions, :2]).sum())
        obs, share_obs, graph, rewards, dones, info = env.step(actions)
        reward_sum += float(np.sum(rewards))
        if bool(np.all(dones)):
            break
    return {
        "protocol": PROTOCOL,
        "method": arm,
        "train_seed": int(train_seed),
        "topology_condition": str(condition["name"]),
        "development_episode_id": int(episode_id),
        "J": reward_sum,
        "success": float(info["success"]),
        "collision": float(info["collision"]),
        "timeout": float(info["timeout"]),
        "constraint_violation": float(info["constraint_violation"]),
        "terminal_step": int(info["step"]),
        "control_effort": control_effort,
        "checkpoint_sha256": checkpoint_hash,
        "scheduled_failure_onset": "" if str(condition["name"]) == "nominal" else int(condition["start_step"]),
        "scheduled_failure_duration": "" if str(condition["name"]) == "nominal" else int(condition["duration_steps"]),
    }


def evaluate_cell(task: tuple[str, int, str, list[int], list[dict[str, Any]], str]) -> list[dict[str, Any]]:
    arm, train_seed, checkpoint_text, episode_ids, conditions, tape_hash = task
    torch.set_num_threads(1)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    checkpoint = Path(checkpoint_text)
    policy: RIGMAPPOAgent | TATGActorCriticSystem
    if arm == BASELINE_ARM:
        policy = build_snapshot_agent(arm, train_seed, checkpoint, device)
    else:
        policy = build_temporal_system(arm, train_seed, checkpoint, device)
    checkpoint_hash = sha256(checkpoint)
    rows = []
    for condition in conditions:
        for episode_id in episode_ids:
            row = episode(arm, train_seed, policy, checkpoint_hash, episode_id, condition, device)
            row["tape_sha256"] = tape_hash
            rows.append(row)
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError(f"refusing to write empty evaluation file: {path}")
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def mean(rows: list[dict[str, Any]], key: str) -> float:
    values = [float(row[key]) for row in rows if key in row and math.isfinite(float(row[key]))]
    return float(sum(values) / len(values)) if values else math.nan


def validate_inputs(trained_root: Path, output_root: Path) -> tuple[dict[str, Any], dict[str, Any], list[tuple[str, int, str, list[int], list[dict[str, Any]], str]], list[dict[str, Any]]]:
    if output_root.exists():
        raise FileExistsError(f"refusing to overwrite fixed endpoint evaluation: {output_root}")
    freeze = load_json(FREEZE)
    tape = load_json(TAPE)
    expected_ids = list(range(780000, 780100))
    if tape.get("protocol") != "TATG-MAPPO-FRESH-SEED-PILOT-DEVELOPMENT-TAPE-V1" or tape.get("episode_ids") not in (None, expected_ids):
        if tape.get("episode_start") != 780000 or tape.get("episode_count") != 100:
            raise RuntimeError("invalid frozen TATG development tape")
    if tape.get("development_only") is not True or len(tape.get("conditions", [])) != 5:
        raise RuntimeError("invalid development-only TATG tape")
    tape_hash = sha256(TAPE)
    tasks = []
    manifests = []
    for arm in ALL_ARMS:
        for train_seed in FROZEN_SEEDS:
            run = trained_root / "runs" / arm / f"seed{train_seed}"
            manifest = load_json(run / "run_manifest.json")
            if manifest.get("status") != "completed" or int(manifest.get("updates", -1)) != EXPECTED_UPDATES or int(manifest.get("environment_steps", -1)) != EXPECTED_STEPS:
                raise RuntimeError(f"incomplete or non-frozen source run: {arm}/seed{train_seed}")
            if manifest.get("checkpoint_selection") != "fixed_endpoint_only":
                raise RuntimeError(f"source run allows checkpoint selection: {arm}/seed{train_seed}")
            checkpoint = run / "actor_critic_latest.pt"
            if not checkpoint.is_file():
                raise FileNotFoundError(checkpoint)
            tasks.append((arm, int(train_seed), str(checkpoint), expected_ids, list(tape["conditions"]), tape_hash))
            manifests.append({"arm": arm, "seed": int(train_seed), "run_manifest_sha256": sha256(run / "run_manifest.json"), "checkpoint_sha256": sha256(checkpoint)})
    if freeze["evaluation"]["total_episodes"] != len(tasks) * len(tape["conditions"]) * len(expected_ids):
        raise RuntimeError("frozen evaluation total is inconsistent")
    return freeze, tape, tasks, manifests


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trained-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=12)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("refusing fixed endpoint evaluation without --execute")
    if args.workers < 1:
        raise ValueError("workers must be positive")
    freeze, tape, tasks, manifests = validate_inputs(args.trained_root, args.output_root)
    args.output_root.mkdir(parents=True, exist_ok=False)
    total = int(freeze["evaluation"]["total_episodes"])
    print(f"TATG pilot endpoint evaluation: cells={len(tasks)}, episodes={total}, workers={min(args.workers, len(tasks))}", flush=True)
    raw: list[dict[str, Any]] = []
    completed = 0
    with ProcessPoolExecutor(max_workers=min(args.workers, len(tasks)), mp_context=mp.get_context("spawn")) as pool:
        futures = [pool.submit(evaluate_cell, task) for task in tasks]
        for future in as_completed(futures):
            rows = future.result()
            raw.extend(rows)
            completed += len(rows)
            print(f"TATG pilot endpoint evaluation progress {completed}/{total} ({100 * completed / total:.2f}%)", flush=True)
    order = {str(condition["name"]): index for index, condition in enumerate(tape["conditions"])}
    raw.sort(key=lambda row: (row["method"], int(row["train_seed"]), order[row["topology_condition"]], int(row["development_episode_id"])))
    write_csv(args.output_root / "raw_episode_metrics.csv", raw)
    summary = []
    for arm in ALL_ARMS:
        for train_seed in FROZEN_SEEDS:
            for condition in order:
                rows = [row for row in raw if row["method"] == arm and int(row["train_seed"]) == train_seed and row["topology_condition"] == condition]
                summary.append({"method": arm, "train_seed": int(train_seed), "condition": condition, "episodes": len(rows), **{key: mean(rows, key) for key in ("J", "success", "collision", "timeout", "constraint_violation", "control_effort")}})
    write_csv(args.output_root / "per_seed_condition_summary.csv", summary)
    (args.output_root / "evaluation_manifest.json").write_text(json.dumps({
        "protocol": PROTOCOL,
        "status": "completed",
        "source_training_root": str(args.trained_root),
        "source_runs": manifests,
        "tape_sha256": sha256(TAPE),
        "raw_rows": len(raw),
        "seed_condition_rows": len(summary),
        "cells": len(tasks),
        "episodes_per_condition": 100,
        "conditions": len(tape["conditions"]),
        "total_episodes": total,
        "fixed_endpoint_update": EXPECTED_UPDATES,
        "training_started": False,
        "resume_started": False,
        "checkpoint_selection": False,
        "automatic_aggregation_or_continuation": False,
    }, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
