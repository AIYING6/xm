"""Posthoc-only C-topology headroom and assignment-behaviour audit."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from envs.redundant_topology_uav_env import ROLE_SCOUT, ROLE_TERMINAL
import scripts.run_redundant_topology_uav_p2r as core
from scripts.run_redundant_topology_uav_p2 import maybe_fault
import scripts.run_redundant_topology_uav_p3_p2 as p3

PROTOCOL = "REDUNDANT-TOPOLOGY-UAV-P4-P0-C-GROUP-ATTRIBUTION-V1"
ARMS = p3.ARMS
SEEDS = p3.SEEDS
C_GROUPS = ("C_relay_node", "C_balanced", "C_cross", "C_same_relay")
EPISODES = 24
CONTRACT = ROOT / "docs/redundant_topology_uav_p3_20260903/P4_P0_C_GROUP_ATTRIBUTION_CONTRACT.md"


def policy_episode(agent: torch.nn.Module, group: str, seed: int, device: torch.device) -> dict[str, object]:
    env = p3.make_env(seed, group)
    _, share, graph = env.reset()
    scout_nonidle = scout_aligned = scout_decisions = 0
    terminal_nonidle = terminal_aligned = terminal_decisions = 0
    total_reward = 0.0
    while not env.done:
        maybe_fault(env)
        with torch.no_grad():
            actions = agent.action_value(*core.tensors(core.graph_stack([graph]), share[None], device), deterministic=True)[0][0].cpu().numpy()
        for agent_id, action in enumerate(actions):
            role = int(env.roles[agent_id])
            if role == ROLE_SCOUT:
                scout_decisions += 1
                if int(action) != 0:
                    scout_nonidle += 1
                    scout_aligned += int(int(action) == env.scout_assignment[agent_id] + 1)
            elif role == ROLE_TERMINAL:
                terminal_decisions += 1
                if int(action) != 0:
                    terminal_nonidle += 1
                    terminal_aligned += int(int(action) == env.terminal_assignment[agent_id] + 1)
        _, share, graph, rewards, _, info = env.step(actions)
        total_reward += float(rewards[0, 0])
    return {
        "group": group, "seed": seed, "success": int(info["success"]), "timeout": int(info["timeout"]),
        "collision": float(info["collision_pair"]), "score": total_reward,
        "completed_objectives": int(env.completed.sum()),
        "scout_nonidle_rate": scout_nonidle / max(1, scout_decisions),
        "scout_assigned_nonidle_rate": scout_aligned / max(1, scout_nonidle),
        "terminal_nonidle_rate": terminal_nonidle / max(1, terminal_decisions),
        "terminal_assigned_nonidle_rate": terminal_aligned / max(1, terminal_nonidle),
    }


def audit(output_root: Path, source_root: Path, device: torch.device) -> None:
    p3.configure_core()
    rows: list[dict[str, object]] = []
    for arm_index, arm in enumerate(ARMS):
        for seed in SEEDS:
            checkpoint = source_root / "runs" / arm / f"seed{seed}" / "runtime_1m.pt"
            if not checkpoint.is_file():
                raise RuntimeError(f"missing retained P3-P2 endpoint checkpoint: {checkpoint}")
            agent = core.load_agent(checkpoint, device)
            for group_index, group in enumerate(C_GROUPS):
                for episode in range(EPISODES):
                    row = policy_episode(agent, group, 960000 + arm_index * 100000 + seed * 100 + group_index * EPISODES + episode, device)
                    # `seed` inside policy_episode is the diagnostic episode seed;
                    # retain the independent training seed separately for aggregation.
                    row.update({"arm": arm, "training_seed": seed, "episode": episode})
                    rows.append(row)
    diag = output_root / "diagnostics"; diag.mkdir(parents=True, exist_ok=True)
    fields = ("arm", "training_seed", "seed", "group", "episode", "success", "timeout", "collision", "score", "completed_objectives", "scout_nonidle_rate", "scout_assigned_nonidle_rate", "terminal_nonidle_rate", "terminal_assigned_nonidle_rate")
    with (diag / "P4_P0_C_GROUP_EVENT_LEDGER.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader(); writer.writerows(rows)
    write_report(rows, diag)


def write_report(rows: list[dict[str, object]], diag: Path) -> None:
    """Summarize rows by the independent training seed, never episode seed."""
    fields = ("arm", "training_seed", "seed", "group", "episode", "success", "timeout", "collision", "score", "completed_objectives", "scout_nonidle_rate", "scout_assigned_nonidle_rate", "terminal_nonidle_rate", "terminal_assigned_nonidle_rate")
    summary: list[dict[str, object]] = []
    metric_names = fields[5:]
    for arm in ARMS:
        for seed in SEEDS:
            values = [row for row in rows if row["arm"] == arm and int(row["training_seed"]) == seed]
            summary.append({"arm": arm, "seed": seed, **{name: float(np.mean([float(row[name]) for row in values])) for name in metric_names}})
    with (diag / "P4_P0_C_GROUP_SEED_SUMMARY.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary[0])); writer.writeheader(); writer.writerows(summary)
    utr = [row for row in summary if row["arm"] == p3.UTR]
    headroom = [row for row in utr if row["success"] < 0.75]
    scout_low = sum(row["scout_assigned_nonidle_rate"] <= 0.50 for row in headroom)
    terminal_low = sum(row["terminal_assigned_nonidle_rate"] <= 0.50 for row in headroom)
    if len(headroom) < 3:
        verdict = "P4_P0_NO_C_HEADROOM"
    elif scout_low >= 3 or terminal_low >= 3:
        verdict = "P4_P0_CREDIT_ASSIGNMENT_CANDIDATE"
    else:
        verdict = "P4_P0_HEADROOM_WITHOUT_ASSIGNMENT_MECHANISM"
    payload = {"protocol": PROTOCOL, "verdict": verdict, "c_groups": list(C_GROUPS), "episodes_per_cell": EPISODES,
               "utr_headroom_seed_count": len(headroom), "headroom_seed_ids": [row["seed"] for row in headroom],
               "scout_low_alignment_headroom_seed_count": scout_low,
               "terminal_low_alignment_headroom_seed_count": terminal_low,
               "independent_unit": "training_seed", "training_started": False,
               "checkpoint_selection": "fixed_runtime_1m_only", "automatic_continuation": False}
    (diag / "P4_P0_FINAL_VERDICT.md").write_text("# P4-P0 final verdict\n\n`" + verdict + "`\n\n```json\n" + json.dumps(payload, indent=2) + "\n```\n", encoding="utf-8")
    (diag / "P4_P0_GATE_DECISION.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    (diag / "P4_P0_ATTRIBUTION_REPORT.md").write_text(
        "# P4-P0 C-group attribution report\n\n"
        "This is fixed-checkpoint descriptive behaviour telemetry. Assignment alignment is not causal proof and cannot by itself authorize an intervention.\n\n"
        "```json\n" + json.dumps(payload, indent=2) + "\n```\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))


def aggregate_existing(output_root: Path) -> None:
    """Repair only the summary of a completed legacy ledger; takes no env steps."""
    ledger = output_root / "diagnostics" / "P4_P0_C_GROUP_EVENT_LEDGER.csv"
    if not ledger.is_file():
        raise RuntimeError("existing P4-P0 event ledger is missing")
    rows: list[dict[str, object]] = []
    with ledger.open(encoding="utf-8") as handle:
        for raw in csv.DictReader(handle):
            arm = str(raw["arm"])
            if arm not in ARMS:
                raise RuntimeError("legacy ledger contains an unexpected arm")
            arm_index = ARMS.index(arm)
            # Legacy episode seed = 960000 + arm_index*100000 + training_seed*100 + offset<100.
            raw["training_seed"] = (int(raw["seed"]) - 960000 - arm_index * 100000) // 100
            rows.append(raw)
    write_report(rows, output_root / "diagnostics")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", default="results/development/redundant_topology_uav_p3_p2")
    parser.add_argument("--output-root", default="results/development/redundant_topology_uav_p4_p0")
    parser.add_argument("--aggregate-existing", action="store_true", help="repair only an existing event-ledger summary")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        print(json.dumps({"protocol": PROTOCOL, "execute_required": True, "training_started": False, "evaluation_only": True}, indent=2)); return
    if not CONTRACT.is_file():
        raise RuntimeError("frozen P4-P0 contract is missing")
    if args.aggregate_existing:
        aggregate_existing(Path(args.output_root))
    else:
        audit(Path(args.output_root), Path(args.source_root), torch.device("cuda" if torch.cuda.is_available() else "cpu"))


if __name__ == "__main__":
    main()
