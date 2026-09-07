"""Read-only Q0 for a discriminative six-UAV fault-timing protocol.

This utility neither trains nor writes into an existing run/evaluation tree.  It
loads frozen 10M checkpoints only to verify that every non-nominal topology
condition is injected before its episode terminates under the proposed timing.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.run_drtp_6uav_cross_scale_formal import (
    ALL_GROUPS,
    ARMS,
    SEEDS,
    digest,
    fault_spec,
    graph_stack,
    load_agent,
    make_env,
    tensors,
)


PROTOCOL = "DRTP-6UAV-FAULT-TIMING-Q0-V1"


def run_episode(agent, arm: str, seed: int, group: str, episode_seed: int, fault_step: int, device: torch.device) -> dict:
    env = make_env(episode_seed, group)
    _, share, graph = env.reset()
    injected = False
    injected_at = None
    active_before = int(env.active_adjacency().sum())
    active_after = active_before
    while not env.done:
        if group != "nominal" and env.step_count == fault_step:
            spec = fault_spec(env, group)
            env.set_failure(spec["edges"], spec["nodes"])
            injected = True
            injected_at = int(env.step_count)
            active_after = int(env.active_adjacency().sum())
        with torch.no_grad():
            action = agent.action_value(
                *tensors(graph_stack([graph]), share[None], device), deterministic=True
            )[0][0].cpu().numpy()
        _, share, graph, _, _, info = env.step(action)
    return {
        "arm": arm,
        "train_seed": seed,
        "group": group,
        "episode_seed": episode_seed,
        "fault_step": fault_step,
        "episode_steps": int(env.step_count),
        "fault_injected": injected,
        "fault_injected_at": injected_at if injected_at is not None else "",
        "faulted_edge_count": len(env.failure_mask),
        "active_edges_before": active_before,
        "active_edges_after": active_after,
        "completed_after_fault": bool(injected and env.step_count > fault_step),
        "success": int(info["success"]),
        "timeout": int(info["timeout"]),
        "collision": float(info["collision_pair"]),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trained-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--fault-step", type=int, default=2)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("explicit --execute is required")
    if args.fault_step < 0:
        raise ValueError("fault step must be non-negative")
    if args.output_root.exists():
        raise FileExistsError(f"refusing to overwrite {args.output_root}")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    rows: list[dict] = []
    for arm in ARMS:
        for seed in SEEDS:
            run = args.trained_root / "runs" / arm / f"seed{seed}"
            checkpoint = run / "actor_critic_latest.pt"
            manifest = json.loads((run / "run_manifest.json").read_text(encoding="utf-8"))
            if manifest.get("status") != "completed" or manifest.get("checkpoint_sha256") != digest(checkpoint):
                raise RuntimeError(f"invalid frozen checkpoint: {run}")
            agent = load_agent(checkpoint, device)
            for group_index, group in enumerate(ALL_GROUPS):
                rows.append(run_episode(agent, arm, seed, group, 960_000 + seed * 100 + group_index, args.fault_step, device))

    non_nominal = [row for row in rows if row["group"] != "nominal"]
    checks = {
        "all_non_nominal_faults_injected": all(row["fault_injected"] for row in non_nominal),
        "all_non_nominal_completed_after_fault": all(row["completed_after_fault"] for row in non_nominal),
        "all_non_nominal_change_active_edges": all(row["active_edges_after"] < row["active_edges_before"] for row in non_nominal),
        "nominal_remains_unfaulted": all(not row["fault_injected"] and row["faulted_edge_count"] == 0 for row in rows if row["group"] == "nominal"),
    }
    verdict = "DRTP_6UAV_FAULT_TIMING_Q0_PASS" if all(checks.values()) else "DRTP_6UAV_FAULT_TIMING_Q0_FAIL"
    args.output_root.mkdir(parents=True)
    with (args.output_root / "DRTP_6UAV_FAULT_TIMING_Q0_LEDGER.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    report = {
        "protocol": PROTOCOL,
        "verdict": verdict,
        "fault_step": args.fault_step,
        "checks": checks,
        "checkpoint_count": len(ARMS) * len(SEEDS),
        "environment_steps": 0,
        "ppo_updates": 0,
        "training_started": False,
        "evaluation_started": False,
        "automatic_continuation": False,
    }
    payload = json.dumps(report, indent=2) + "\n"
    (args.output_root / "DRTP_6UAV_FAULT_TIMING_Q0_REPORT.json").write_text(payload, encoding="utf-8")
    (args.output_root / "DRTP_6UAV_FAULT_TIMING_Q0_REPORT.md").write_text(
        f"# 6-UAV fault-timing Q0\n\n`{verdict}`\n\n"
        "This is a read-only checkpoint timing validation. It is not a performance evaluation.\n\n```json\n"
        + payload + "```\n",
        encoding="utf-8",
    )
    print(payload, end="")


if __name__ == "__main__":
    main()
