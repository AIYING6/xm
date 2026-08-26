"""Zero-training REL-A0 multi-tape evaluation and deterministic smoke."""
from __future__ import annotations

import argparse
import csv
from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import json
import math
import multiprocessing as mp
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import run_phase_rsg1_development_smoke as base  # noqa: E402
from envs.uav_intercept_3d_env import ACTION3D_TABLE, UAVIntercept3DConfig, UAVIntercept3DEnv  # noqa: E402


PROTOCOL = "DRTP-REL-A0-MULTI-TAPE-EVALUATION-V1"
METHODS = ("utr_sg", "drtp_sg")
SEEDS = (1901, 1902, 2001, 2002, 2003)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def env_for(episode_id: int, condition: dict) -> UAVIntercept3DEnv:
    onset = condition.get("failure_start_step", condition.get("start_step"))
    duration = condition.get("failure_duration_steps", condition.get("duration_steps"))
    failure = condition["name"] != "nominal"
    return UAVIntercept3DEnv(UAVIntercept3DConfig(
        seed=episode_id, target_policy="straight", strict_target_sensing=True,
        agent_target_info_bottleneck=True, relay_dependent_task=True,
        business_grounded_geometry=True, communication_range_scale=1.0,
        communication_dropout_prob=0.0, message_delay_steps=0,
        radar_dropout_prob=0.0, max_steps=260, min_success_step=260,
        failed_blue_agent=1 if failure else -1,
        node_failure_start_step=int(onset or 0),
        node_failure_duration_steps=int(duration or 0),
    ))


def run_episode(agent, method: str, seed: int, tape_label: str, tape_hash: str,
                episode_id: int, condition: dict) -> dict:
    env = env_for(episode_id, condition)
    obs, share, graph = env.reset()
    reward_sum = 0.0
    control_effort = 0.0
    traveled = 0.0
    previous = env.blue_pos.copy()
    paths = []
    traces = []
    onset = condition.get("failure_start_step", condition.get("start_step"))
    duration = condition.get("failure_duration_steps", condition.get("duration_steps"))
    while True:
        step = int(env.step_count)
        actions = base.policy_action(agent, obs, share, graph)
        control_effort += float(np.abs(ACTION3D_TABLE[actions, :2]).sum())
        obs, share, graph, rewards, dones, info = env.step(actions)
        reward_sum += float(np.sum(rewards))
        traveled += float(np.linalg.norm(env.blue_pos - previous, axis=1).sum())
        previous = env.blue_pos.copy()
        path = str(info.get("attacker_cache_paths_t", ""))
        paths.append(path)
        traces.append({
            "step": step,
            "failure_active": int(float(info.get("node_failure_active", 0.0)) > .5),
            "path": path,
            "task_support": int(float(info.get("chain_support_t", 0.0)) > .5),
            "legal_info": int(float(info.get("attacker_legal_target_information_t", 0.0)) > .5),
            "cache_age": float(info.get("target_cache_age_mean", 0.0)),
        })
        if np.all(dones):
            break
    active = [x for x in traces if x["failure_active"]]
    denom = max(1, len(active))
    terminal = int(info["step"])
    scheduled = condition["name"] != "nominal"
    survived = (not scheduled) or terminal >= int(onset)
    exposed = bool(active)
    return {
        "protocol": PROTOCOL,
        "tape_label": tape_label,
        "tape_hash": tape_hash,
        "method": method,
        "training_seed": seed,
        "episode_id": episode_id,
        "condition": condition["name"],
        "scheduled_failure_onset": "" if onset is None else int(onset),
        "scheduled_failure_duration": "" if duration is None else int(duration),
        "J": reward_sum,
        "success": float(info["success"]),
        "collision": float(info["collision"]),
        "timeout": float(info["timeout"]),
        "constraint_violation": float(info["constraint_violation"]),
        "terminal_step": terminal,
        "survived_to_onset": int(survived),
        "failure_exposed": int(exposed),
        "pre_trigger_termination": int(scheduled and terminal < int(onset)),
        "direct_path_fraction_failure": float(sum(x["path"] == "0-2" for x in active) / denom),
        "relay_path_fraction_failure": float(sum(x["path"] == "0-1-2" for x in active) / denom),
        "task_support_fraction_failure": float(sum(x["task_support"] for x in active) / denom),
        "legal_information_fraction_failure": float(sum(x["legal_info"] for x in active) / denom),
        "mean_cache_age_failure": float(np.mean([x["cache_age"] for x in active])) if active else math.nan,
        "path_switch_count": sum(a != b for a, b in zip(paths, paths[1:])),
        "traveled_distance": traveled,
        "control_effort": control_effort,
    }


def worker(task: tuple) -> list[dict]:
    method, seed, checkpoint_text, tape = task
    import torch
    torch.set_num_threads(1)
    checkpoint = Path(checkpoint_text)
    agent = base.build_agent({"graph_encoder": "single", "hidden_dim": 115}, checkpoint, seed)
    return [run_episode(agent, method, seed, tape["tape_label"], tape["tape_hash"], int(eid), cond)
            for cond in tape["conditions"] for eid in tape["episode_ids"]]


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]) if rows else ["empty"])
        writer.writeheader()
        writer.writerows(rows)


def load_sources(args: argparse.Namespace) -> list[dict]:
    rows = []
    for method in METHODS:
        for seed in SEEDS:
            root = args.strict_root if seed in (1901, 1902) else args.heldout_root
            run = root / method / f"seed{seed}"
            manifest = json.loads((run / "run_manifest.json").read_text(encoding="utf-8"))
            checkpoint = run / "actor_critic_latest.pt"
            if manifest.get("status") != "completed" or not checkpoint.exists():
                raise RuntimeError(f"invalid source run: {method}/seed{seed}")
            if sha256(checkpoint) != manifest.get("final_checkpoint_sha256"):
                raise RuntimeError(f"checkpoint hash mismatch: {method}/seed{seed}")
            rows.append({"method": method, "seed": seed, "checkpoint": checkpoint,
                         "checkpoint_sha256": sha256(checkpoint), "manifest": manifest})
    return rows


def load_tapes(tape_root: Path) -> list[dict]:
    tapes = []
    for label in ("T0", "T1", "T2", "T3", "T4"):
        tape = json.loads((tape_root / f"{label}_manifest.json").read_text(encoding="utf-8"))
        if tape.get("episode_ids") != list(range(int(tape["episode_ids"][0]), int(tape["episode_ids"][0]) + 100)):
            raise RuntimeError(f"invalid tape ids: {label}")
        tapes.append(tape)
    return tapes


def smoke(args: argparse.Namespace) -> None:
    source = next(x for x in load_sources(args) if x["method"] == "utr_sg" and x["seed"] == 1901)
    tape = load_tapes(args.tape_root)[0]
    conds = tape["conditions"][:2]
    tasks = [("utr_sg", 1901, str(source["checkpoint"]), {**tape, "conditions": conds,
             "episode_ids": tape["episode_ids"][:2]})]
    first = worker(tasks[0])
    second = worker(tasks[0])
    a = json.dumps(first, sort_keys=True, allow_nan=True)
    b = json.dumps(second, sort_keys=True, allow_nan=True)
    result = {"protocol": "DRTP-REL-A0-SMOKE-V1", "training_started": False,
              "checkpoint_sha256": source["checkpoint_sha256"],
              "deterministic_replay": a == b, "rows": len(first),
              "finite_returns": all(math.isfinite(float(row["J"])) for row in first)}
    result["status"] = "PASS" if result["deterministic_replay"] and result["finite_returns"] else "FAIL"
    args.output_root.mkdir(parents=True, exist_ok=True)
    (args.output_root / "smoke_manifest.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    if result["status"] != "PASS":
        raise SystemExit(1)


def full(args: argparse.Namespace) -> None:
    if args.output_root.exists() and any(args.output_root.iterdir()):
        raise FileExistsError(f"refusing to overwrite: {args.output_root}")
    args.output_root.mkdir(parents=True, exist_ok=False)
    sources = load_sources(args)
    tapes = load_tapes(args.tape_root)
    tasks = [(x["method"], x["seed"], str(x["checkpoint"]), tape)
             for x in sources for tape in tapes]
    expected = len(tasks) * 5 * 100
    rows: list[dict] = []
    with ProcessPoolExecutor(max_workers=min(args.workers, len(tasks)), mp_context=mp.get_context("spawn")) as pool:
        futures = [pool.submit(worker, task) for task in tasks]
        completed = 0
        for future in as_completed(futures):
            block = future.result()
            rows.extend(block)
            completed += len(block)
            print(f"REL-A0 evaluation progress {completed}/{expected} ({100 * completed / expected:.2f}%)", flush=True)
    rows.sort(key=lambda x: (x["method"], int(x["training_seed"]), x["tape_label"], x["condition"], int(x["episode_id"])))
    write_csv(args.output_root / "raw_episode_metrics.csv", rows)
    manifest = {"protocol": PROTOCOL, "status": "completed", "training_started": False,
                "raw_rows": len(rows), "tapes": [t["tape_label"] for t in tapes],
                "methods": list(METHODS), "seeds": list(SEEDS), "workers": args.workers,
                "final_checkpoint_only": True, "canonical_used": False, "heldout_training": False}
    (args.output_root / "evaluation_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--strict-root", type=Path, required=True)
    p.add_argument("--heldout-root", type=Path, required=True)
    p.add_argument("--tape-root", type=Path, required=True)
    p.add_argument("--output-root", type=Path, required=True)
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--smoke", action="store_true")
    p.add_argument("--execute", action="store_true")
    args = p.parse_args()
    if not args.execute:
        raise SystemExit("NO-GO: explicit --execute is required")
    if args.smoke:
        smoke(args)
    else:
        full(args)


if __name__ == "__main__":
    main()
