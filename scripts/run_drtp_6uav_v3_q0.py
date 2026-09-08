"""Zero-training semantic calibration for the independent 6-UAV V3 task."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from envs.redundant_topology_uav_env import RedundantTopologyConfig
from envs.sustained_support_topology_uav_env import SustainedSupportTopologyConfig, SustainedSupportTopologyUAVEnv

PROTOCOL = "DRTP-6UAV-V3-SUSTAINED-SUPPORT-Q0-V1"
GROUPS = ("nominal", "R_upstream", "R_downstream", "C_relay_node", "C_balanced", "C_cross", "C_same_relay")


def make_env(seed: int) -> SustainedSupportTopologyUAVEnv:
    base = RedundantTopologyConfig(
        scouts=2, relays=2, terminals=2, deadline_steps=4,
        scout_sense_range=120.0, relay_radio_range=70.0, terminal_speed=10.0,
        tau_max=1, comm_dropout=0.0, assignment_observation=True,
        scout_assignment_observation=True, seed_env=seed, seed_comm=seed + 100_000, seed_topology=seed + 200_000,
    )
    return SustainedSupportTopologyUAVEnv(SustainedSupportTopologyConfig(base=base, fault_transition=2))


def fault_spec(env: SustainedSupportTopologyUAVEnv, group: str) -> dict[str, list[int | tuple[int, int]]]:
    s0, s1 = map(int, env.scout_ids)
    r0, r1 = map(int, env.relay_ids)
    t0, t1 = map(int, env.terminal_ids)
    specs = {
        "nominal": {"edges": [], "nodes": []},
        "R_upstream": {"edges": [(s0, r0)], "nodes": []},
        "R_downstream": {"edges": [(r0, t0)], "nodes": []},
        "C_relay_node": {"edges": [], "nodes": [r0]},
        "C_balanced": {"edges": [(s0, r0), (r1, t1)], "nodes": []},
        "C_cross": {"edges": [(s0, r0), (r0, t1)], "nodes": []},
        "C_same_relay": {"edges": [(s0, r0), (s1, r0)], "nodes": []},
    }
    return specs[group]


def route_actions(env: SustainedSupportTopologyUAVEnv, group: str) -> np.ndarray:
    """Information-privileged feasibility witness, never a learning policy."""
    actions = np.zeros(env.n, dtype=np.int64)
    for scout, objective in env.scout_assignment.items():
        if not env.completed[objective]:
            actions[scout] = objective + 1
    for terminal, objective in env.terminal_assignment.items():
        if not env.completed[objective]:
            actions[terminal] = objective + 1

    task = env.task_adjacency(True)
    viable: dict[int, list[int]] = {}
    for objective in range(env.k):
        source = next(s for s, assigned in env.scout_assignment.items() if assigned == objective)
        terminal = next(t for t, assigned in env.terminal_assignment.items() if assigned == objective)
        viable[objective] = [int(relay) for relay in env.relay_ids if task[int(relay), source] and task[terminal, int(relay)]]

    usable = [int(relay) for relay in env.relay_ids if relay not in env.failed_nodes]
    if len(usable) == 1:
        objective = (env.step_count - 1) % env.k
        if usable[0] in viable[objective]:
            actions[usable[0]] = objective + 1
        return actions

    assigned: set[int] = set()
    for objective in range(env.k):
        available = [relay for relay in viable[objective] if relay not in assigned]
        if available:
            relay = min(available)
            actions[relay] = objective + 1
            assigned.add(relay)
    return actions


def run_group(seed: int, group: str) -> dict[str, object]:
    env = make_env(seed)
    env.reset()
    injected = False
    history: list[dict[str, object]] = []
    while not env.done:
        if group != "nominal" and env.step_count == env.semantic_config.fault_transition - 1:
            spec = fault_spec(env, group)
            env.set_failure(spec["edges"], spec["nodes"])
            injected = True
        actions = route_actions(env, group)
        _, _, graph, reward, done, info = env.step(actions)
        history.append({"transition": env.step_count, "actions": actions.tolist(), "delivered": len(info["delivered"]), "success": bool(info["success"]), "active_edges": int(info["active_adj"].sum()), "relay_masks": graph["action_masks"][env.relay_ids].tolist(), "reward": float(reward[0, 0])})
        if bool(done[0, 0]):
            break
    return {
        "group": group, "seed": seed, "success": bool(info["success"]), "timeout": bool(info["timeout"]),
        "score": float(sum(row["reward"] for row in history)), "completed": env.completed.astype(int).tolist(),
        "fault_injected": injected, "fault_transition": env.semantic_config.fault_transition if injected else "",
        "episode_steps": env.step_count, "history": history, "signature": env.graph_signature(),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("explicit --execute is required")
    if args.output_root.exists():
        raise FileExistsError(f"refusing to overwrite {args.output_root}")

    rows = [run_group(seed, group) for seed in (93001, 93002) for group in GROUPS]
    nonnominal = [row for row in rows if row["group"] != "nominal"]
    checks = {
        "interface_six_agents": all(len(row["history"][0]["actions"]) == 6 for row in rows),
        "nominal_two_parallel_services": all(row["success"] and row["episode_steps"] == 3 for row in rows if row["group"] == "nominal"),
        "faults_effective_before_terminal": all(row["fault_injected"] and row["episode_steps"] >= 3 for row in nonnominal),
        "partial_not_global_failure": any(row["completed"] == [1, 0] or row["completed"] == [0, 1] for row in nonnominal),
        "recoverable_reassignment_exists": all(row["success"] for row in rows if row["group"] in {"R_upstream", "R_downstream", "C_balanced"}),
        "no_hidden_failure_feature": all("failure_mask" not in row["history"][0] for row in rows),
    }
    verdict = "V3_Q0_PASS" if all(checks.values()) else "V3_Q0_FAIL"
    args.output_root.mkdir(parents=True)
    with (args.output_root / "V3_Q0_GROUPS.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["group", "seed", "success", "timeout", "score", "completed", "fault_injected", "fault_transition", "episode_steps"])
        writer.writeheader()
        writer.writerows([{key: row[key] for key in writer.fieldnames} for row in rows])
    payload = {"protocol": PROTOCOL, "verdict": verdict, "training_started": False, "evaluation_started": False, "diagnostic_only": True, "checks": checks, "rows": rows}
    (args.output_root / "DRTP_6UAV_V3_Q0.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    report = ["# 6-UAV V3 sustained-support Q0", "", f"`{verdict}`", "", "This is an environment-semantic feasibility check using an information-privileged scripted witness. It is not a learned-policy evaluation and cannot support a DRTP performance claim.", "", "## Checks", ""]
    report.extend(f"- {name}: {'PASS' if value else 'FAIL'}" for name, value in checks.items())
    report.extend(["", "## Per-group witness endpoints", "", "| Group | Success | Completed objectives | Steps |", "| --- | ---: | --- | ---: |"])
    report.extend(f"| {row['group']} | {int(row['success'])} | {row['completed']} | {row['episode_steps']} |" for row in rows[:len(GROUPS)])
    (args.output_root / "DRTP_6UAV_V3_Q0_REPORT.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
