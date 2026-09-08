"""Zero-training diagnostic calibration for 6-UAV topology-fault discriminability.

This tool deliberately does *not* train a policy, update a sampler, alter a
checkpoint, or compare UTR with DRTP.  It replays frozen UTR endpoints under a
small, predeclared family of task geometries to establish whether a candidate
6-UAV task has enough post-fault decision pressure to distinguish nominal and
faulted topology groups.  Its output is a protocol-design diagnostic, never a
paper performance result.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import statistics
import sys
from pathlib import Path
from typing import Any

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from algorithms.redundant_topology_role_sg_mappo import RoleSharedSGMPPO
from envs.redundant_topology_uav_env import RedundantTopologyUAVEnv, scale_config
from scripts.run_redundant_topology_uav_p2 import fault_spec, graph_stack, tensors


PROTOCOL = "DRTP-6UAV-TASK-DISCRIMINATION-CALIBRATION-V1"
CONFIG = ROOT / "configs" / "drtp_6uav_task_discrimination_calibration_v1.json"
UTR_ARM = "utr_scout_terminal_assigned_role_sg_mappo"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def spaced(count: int, x: float, width: float = 20.0) -> np.ndarray:
    ys = np.asarray([0.0], dtype=np.float32) if count == 1 else np.linspace(-width / 2, width / 2, count, dtype=np.float32)
    return np.stack([np.full(count, x, dtype=np.float32), ys], axis=1)


def make_env(seed: int, group: str, candidate: dict[str, Any]) -> RedundantTopologyUAVEnv:
    """Build a same-interface environment and apply only declared task geometry."""
    env = RedundantTopologyUAVEnv(
        scale_config(
            "main",
            seed_env=seed,
            seed_comm=seed + 100_000,
            seed_topology=seed + 200_000,
            scout_sense_range=float(candidate["scout_sense_range"]),
            relay_radio_range=float(candidate["relay_radio_range"]),
            terminal_speed=float(candidate["terminal_speed"]),
            tau_max=int(candidate["tau_max"]),
            deadline_steps=int(candidate["deadline_steps"]),
            boundary=float(candidate["boundary"]),
        )
    )
    env._calibration_group = group
    return env


def reset_geometry(env: RedundantTopologyUAVEnv, candidate: dict[str, Any]) -> tuple[np.ndarray, np.ndarray, dict[str, np.ndarray]]:
    """Set only frozen role lanes and objective lanes after ordinary reset.

    The observation shape, role order, action interface, reward computation,
    legal topology, failure masks, and termination semantics remain native.
    """
    env.reset()
    env.positions = np.concatenate(
        (
            spaced(len(env.scout_ids), float(candidate["scout_x"])),
            spaced(len(env.relay_ids), float(candidate["relay_x"])),
            spaced(len(env.terminal_ids), float(candidate["terminal_x"])),
        ),
        axis=0,
    )
    env.objective_positions = spaced(env.k, float(candidate["objective_x"]))
    # Assignments only order same-lane objectives and agents. Recreate them so
    # they are derived from the declared candidate geometry rather than a
    # hidden prior reset geometry.
    terminal_order = env.terminal_ids[np.argsort(env.positions[env.terminal_ids, 1])]
    scout_order = env.scout_ids[np.argsort(env.positions[env.scout_ids, 1])]
    objective_order = np.argsort(env.objective_positions[:, 1])
    env.terminal_assignment = {int(t): int(o) for t, o in zip(terminal_order, objective_order)}
    env.scout_assignment = {int(s): int(o) for s, o in zip(scout_order, objective_order)}
    return env.actor_observation(), env.critic_observation(), env.graph_observation()


def maybe_fault(env: RedundantTopologyUAVEnv, fault_step: int) -> None:
    if env._calibration_group != "nominal" and env.step_count == fault_step:
        before = int(env.active_adjacency().sum())
        spec = fault_spec(env, env._calibration_group)
        env.set_failure(spec["edges"], spec["nodes"])
        env._fault_injected = True
        env._fault_step = int(env.step_count)
        env._active_before = before
        env._active_after = int(env.active_adjacency().sum())


def load_agent(checkpoint: Path, device: torch.device, candidate: dict[str, Any]) -> RoleSharedSGMPPO:
    state = torch.load(checkpoint, map_location=device, weights_only=False)
    env = make_env(1, "nominal", candidate)
    agent = RoleSharedSGMPPO(env.obs_dim, env.share_obs_dim, env.action_dim).to(device)
    agent.load_state_dict(state["model"])
    agent.eval()
    return agent


def episode(agent: RoleSharedSGMPPO, group: str, seed: int, candidate: dict[str, Any], fault_step: int, device: torch.device) -> dict[str, Any]:
    env = make_env(seed, group, candidate)
    _, share, graph = reset_geometry(env, candidate)
    total = 0.0
    while not env.done:
        maybe_fault(env, fault_step)
        with torch.no_grad():
            action = agent.action_value(*tensors(graph_stack([graph]), share[None], device), deterministic=True)[0][0].cpu().numpy()
        _, share, graph, reward, _, info = env.step(action)
        total += float(reward[0, 0])
    injected = int(bool(getattr(env, "_fault_injected", False)))
    return {
        "group": group,
        "score": total,
        "success": int(info["success"]),
        "collision": float(info["collision_pair"]),
        "timeout": int(info["timeout"]),
        "episode_steps": int(env.step_count),
        "fault_injected": injected,
        "fault_injected_at": getattr(env, "_fault_step", ""),
        "active_edges_before": getattr(env, "_active_before", int(env.active_adjacency().sum())),
        "active_edges_after": getattr(env, "_active_after", int(env.active_adjacency().sum())),
        "post_fault_steps": int(env.step_count - fault_step) if injected else "",
    }


def avg(rows: list[dict[str, Any]], key: str) -> float:
    return float(np.mean([float(row[key]) for row in rows]))


def candidate_summary(
    rows: list[dict[str, Any]], candidate: dict[str, Any], rule: dict[str, Any], fault_step: int
) -> dict[str, Any]:
    nominal = [row for row in rows if row["group"] == "nominal"]
    faulted = [row for row in rows if row["group"] != "nominal"]
    groups = sorted(set(row["group"] for row in faulted))
    nominal_success = avg(nominal, "success")
    perturbed_success = avg(faulted, "success")
    drops = {
        group: nominal_success - avg([row for row in faulted if row["group"] == group], "success")
        for group in groups
    }
    affected = sum(drop >= float(rule["nominal_minus_perturbed_success_min"]) for drop in drops.values())
    injected_ok = all(
        int(row["fault_injected"]) == 1
        and int(row["fault_injected_at"]) == fault_step
        and int(row["active_edges_after"]) < int(row["active_edges_before"])
        and int(row["episode_steps"]) > 3
        for row in faulted
    )
    post_fault = [int(row["post_fault_steps"]) for row in faulted]
    checks = {
        "fault_trigger_effective": injected_ok,
        "nominal_learnable": nominal_success >= float(rule["nominal_success_min"]),
        "perturbed_not_ceiling": perturbed_success < float(rule["perturbed_success_max_exclusive"]),
        "perturbed_not_all_failure": perturbed_success > float(rule["perturbed_success_min_exclusive"]),
        "mean_fault_effect": nominal_success - perturbed_success >= float(rule["nominal_minus_perturbed_success_min"]),
        "multiple_groups_affected": affected >= int(rule["affected_groups_min"]),
        "post_fault_decision_horizon": statistics.median(post_fault) >= int(rule["post_fault_steps_median_min"]),
    }
    return {
        "candidate": candidate["id"],
        "description": candidate["description"],
        "episodes": len(rows),
        "nominal_success": nominal_success,
        "perturbed_success": perturbed_success,
        "nominal_minus_perturbed_success": nominal_success - perturbed_success,
        "nominal_score": avg(nominal, "score"),
        "perturbed_score": avg(faulted, "score"),
        "nominal_timeout": avg(nominal, "timeout"),
        "perturbed_timeout": avg(faulted, "timeout"),
        "median_post_fault_steps": float(statistics.median(post_fault)),
        "groups_with_success_drop": affected,
        "success_drop_by_group": drops,
        "checks": checks,
        "verdict": "CALIBRATION_PASS" if all(checks.values()) else "CALIBRATION_FAIL",
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trained-root", type=Path, required=True, help="Extracted v2 result root containing frozen UTR checkpoints.")
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--episodes-per-group", type=int, default=None)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("explicit --execute is required")
    if args.output_root.exists():
        raise FileExistsError(f"refusing to overwrite {args.output_root}")

    spec = json.loads(CONFIG.read_text(encoding="utf-8"))
    if spec["protocol"] != PROTOCOL:
        raise RuntimeError("unexpected calibration configuration")
    fault_step = int(spec["evaluation"]["fault_step"])
    episodes = int(args.episodes_per_group or spec["evaluation"]["episodes_per_group_per_seed"])
    groups = tuple(spec["evaluation"]["groups"])
    seeds = tuple(int(seed) for seed in spec["source_checkpoints"]["seeds"])
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    all_rows: list[dict[str, Any]] = []
    checkpoints: dict[int, str] = {}
    for candidate in spec["candidates"]:
        for train_seed in seeds:
            checkpoint = args.trained_root / "runs" / UTR_ARM / f"seed{train_seed}" / "actor_critic_latest.pt"
            manifest = checkpoint.with_name("run_manifest.json")
            if not checkpoint.is_file() or not manifest.is_file():
                raise FileNotFoundError(f"missing frozen UTR endpoint for seed {train_seed}")
            state = json.loads(manifest.read_text(encoding="utf-8"))
            if state.get("status") != "completed" or state.get("checkpoint_sha256") != sha256(checkpoint):
                raise RuntimeError(f"invalid frozen UTR endpoint for seed {train_seed}")
            checkpoints[train_seed] = state["checkpoint_sha256"]
            agent = load_agent(checkpoint, device, candidate)
            for group_index, group in enumerate(groups):
                for index in range(episodes):
                    row = episode(
                        agent,
                        group,
                        910_000 + train_seed * 10_000 + group_index * episodes + index,
                        candidate,
                        fault_step,
                        device,
                    )
                    row.update({"candidate": candidate["id"], "training_seed": train_seed, "episode": index, "checkpoint_sha256": checkpoints[train_seed]})
                    all_rows.append(row)

    summaries = []
    for candidate in spec["candidates"]:
        rows = [row for row in all_rows if row["candidate"] == candidate["id"]]
        summaries.append(candidate_summary(rows, candidate, spec["eligibility_rule"], fault_step))
    args.output_root.mkdir(parents=True)
    write_csv(args.output_root / "CALIBRATION_RAW_EPISODES.csv", all_rows)
    write_csv(args.output_root / "CALIBRATION_CANDIDATE_SUMMARY.csv", [
        {
            "candidate": row["candidate"],
            "verdict": row["verdict"],
            "nominal_success": row["nominal_success"],
            "perturbed_success": row["perturbed_success"],
            "nominal_minus_perturbed_success": row["nominal_minus_perturbed_success"],
            "nominal_score": row["nominal_score"],
            "perturbed_score": row["perturbed_score"],
            "nominal_timeout": row["nominal_timeout"],
            "perturbed_timeout": row["perturbed_timeout"],
            "median_post_fault_steps": row["median_post_fault_steps"],
            "groups_with_success_drop": row["groups_with_success_drop"],
            **{f"check_{key}": value for key, value in row["checks"].items()},
        }
        for row in summaries
    ])
    payload = {
        "protocol": PROTOCOL,
        "verdict": "CALIBRATION_CANDIDATE_AVAILABLE" if any(row["verdict"] == "CALIBRATION_PASS" for row in summaries) else "CALIBRATION_NO_CANDIDATE",
        "diagnostic_only": True,
        "training_started": False,
        "algorithm_modified": False,
        "checkpoint_overwritten": False,
        "source_utr_training_seeds": list(seeds),
        "episodes_per_group_per_seed": episodes,
        "fault_step": fault_step,
        "checkpoint_sha256": checkpoints,
        "candidates": summaries,
    }
    (args.output_root / "DRTP_6UAV_TASK_DISCRIMINATION_CALIBRATION.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    lines = ["# 6-UAV task-discrimination calibration", "", f"`{payload['verdict']}`", "", "This is a zero-training protocol-design diagnostic. It is not a DRTP result and must not enter a manuscript performance table.", ""]
    for row in summaries:
        lines.extend([
            f"## {row['candidate']} — {row['verdict']}",
            "",
            f"Nominal success={row['nominal_success']:.3f}; perturbed success={row['perturbed_success']:.3f}; difference={row['nominal_minus_perturbed_success']:.3f}; median post-fault steps={row['median_post_fault_steps']:.1f}; affected groups={row['groups_with_success_drop']}.",
            "",
        ])
    (args.output_root / "DRTP_6UAV_TASK_DISCRIMINATION_CALIBRATION.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2), flush=True)


if __name__ == "__main__":
    main()
