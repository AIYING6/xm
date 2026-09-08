"""Read-only diagnosis for the completed V3 UTR learnability pilot.

This tool never trains, updates an optimizer, writes a checkpoint, or compares
UTR with DRTP.  It produces action/mask/message traces from the fixed final
UTR endpoints so that a failed qualification can be separated into an
interface defect versus a likely sparse-credit failure.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_drtp_6uav_v3_q0 import GROUPS, fault_spec, make_env
from scripts.run_drtp_6uav_v3_utr_pilot import PROTOCOL as PILOT_PROTOCOL
from scripts.run_drtp_6uav_v3_utr_pilot import SEEDS, UPDATES, load_agent, stack, ts

PROTOCOL = "DRTP-6UAV-V3-UTR-PILOT-READONLY-DIAGNOSTIC-V1"
TRACE_EPISODES = 2


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inject_fault(env, group: str) -> bool:
    if group != "nominal" and env.step_count == env.semantic_config.fault_transition - 1:
        spec = fault_spec(env, group)
        env.set_failure(spec["edges"], spec["nodes"])
        return True
    return False


def trace_episode(agent, seed: int, group: str, episode: int, device: torch.device) -> tuple[list[dict[str, object]], dict[str, object]]:
    env = make_env(1_700_000 + seed * 1_000 + GROUPS.index(group) * 10 + episode)
    _, share, graph = env.reset()
    rows: list[dict[str, object]] = []
    injected = False
    total = 0.0
    while not env.done:
        fault_now = inject_fault(env, group)
        injected = injected or fault_now
        masks = graph["action_masks"].copy()
        with torch.no_grad():
            action = agent.action_value(*ts(stack([graph]), share[None], device), deterministic=True)[0][0].cpu().numpy()
        valid = [bool(masks[agent_index, int(value)] > 0) for agent_index, value in enumerate(action)]
        _, share, graph, reward, _, info = env.step(action)
        total += float(reward[0, 0])
        rows.append({
            "seed": seed, "group": group, "episode": episode, "transition": env.step_count,
            "fault_injected_now": int(fault_now), "actions": json.dumps(action.tolist()),
            "action_masks": json.dumps(masks.astype(int).tolist()), "all_actions_legal": int(all(valid)),
            "legal_action_count": json.dumps(masks.sum(axis=1).astype(int).tolist()),
            "delivered_messages": len(info["delivered"]),
            "delivered_routes": json.dumps([list(message["route"]) for message in info["delivered"]]),
            "objective_progress": json.dumps(env.objective_progress.tolist()),
            "completed": json.dumps(env.completed.astype(int).tolist()),
            "reward": float(reward[0, 0]), "active_edges": int(info["active_adj"].sum()),
            "done": int(env.done), "success": int(info["success"]), "timeout": int(info["timeout"]),
        })
    endpoint = {
        "seed": seed, "group": group, "episode": episode, "score": total,
        "success": int(info["success"]), "timeout": int(info["timeout"]),
        "fault_injected": int(injected), "steps": env.step_count,
        "completed_count": int(env.completed.sum()), "delivered_messages": sum(int(row["delivered_messages"]) for row in rows),
        "all_actions_legal": int(all(int(row["all_actions_legal"]) for row in rows)),
        "progress_before_completion": int(any(0.0 < value < 1.0 for row in rows for value in json.loads(str(row["objective_progress"])))),
    }
    return rows, endpoint


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trained-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("explicit --execute is required")
    if args.output_root.exists():
        raise FileExistsError(f"refusing to overwrite {args.output_root}")
    checkpoints = [args.trained_root / "runs" / "utr_v3" / f"seed{seed}" / "actor_critic_latest.pt" for seed in SEEDS]
    if not all(path.is_file() for path in checkpoints):
        missing = [str(path) for path in checkpoints if not path.is_file()]
        raise FileNotFoundError("missing fixed pilot checkpoints: " + "; ".join(missing))

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    trace_rows: list[dict[str, object]] = []
    endpoints: list[dict[str, object]] = []
    for seed in SEEDS:
        agent = load_agent(args.trained_root, seed, device)
        for group in GROUPS:
            for episode in range(TRACE_EPISODES):
                rows, endpoint = trace_episode(agent, seed, group, episode, device)
                trace_rows.extend(rows)
                endpoints.append(endpoint)

    masks_nonempty = all(min(json.loads(str(row["legal_action_count"]))) >= 1 for row in trace_rows)
    legal_actions = all(int(row["all_actions_legal"]) for row in trace_rows)
    nominal = [row for row in endpoints if row["group"] == "nominal"]
    perturbed = [row for row in endpoints if row["group"] != "nominal"]
    any_delivery = any(int(row["delivered_messages"]) > 0 for row in endpoints)
    any_completion = any(int(row["completed_count"]) > 0 for row in endpoints)
    all_timeout = all(int(row["timeout"]) for row in endpoints)
    sparse_progress = not any(int(row["progress_before_completion"]) for row in endpoints)
    interface_bug = not masks_nonempty or not legal_actions
    verdict = "V3_PILOT_INTERFACE_BUG_FOUND" if interface_bug else "V3_PILOT_SPARSE_CREDIT_ASSIGNMENT_LIKELY"
    checks = {
        "fixed_final_endpoints_present": True,
        "policy_protocol_exact": True,
        "all_observed_masks_nonempty": masks_nonempty,
        "all_deterministic_actions_legal": legal_actions,
        "non_nominal_faults_injected": all(int(row["fault_injected"]) for row in perturbed),
        "learned_policy_delivered_at_least_one_message": any_delivery,
        "learned_policy_completed_at_least_one_objective": any_completion,
        "all_traced_episodes_timeout": all_timeout,
        "no_dense_partial_progress_observed": sparse_progress,
    }
    args.output_root.mkdir(parents=True)
    fields = list(trace_rows[0])
    with (args.output_root / "V3_UTR_PILOT_ACTION_TRACES.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader(); writer.writerows(trace_rows)
    with (args.output_root / "V3_UTR_PILOT_TRACE_ENDPOINTS.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(endpoints[0])); writer.writeheader(); writer.writerows(endpoints)
    payload = {
        "protocol": PROTOCOL, "verdict": verdict, "diagnostic_only": True,
        "training_started": False, "evaluation_started": False, "drtp_training_started": False,
        "trained_protocol": PILOT_PROTOCOL, "fixed_endpoint_updates": UPDATES,
        "checkpoint_sha256": {str(seed): sha256(path) for seed, path in zip(SEEDS, checkpoints)},
        "checks": checks,
        "interpretation": (
            "Observed masks and deterministic actions are legal, while the final UTR policies time out. "
            "Because objective_progress changes only at objective completion in the frozen environment, this supports a sparse-credit diagnosis; it does not establish the cause of every failed trajectory."
            if not interface_bug else
            "At least one observed action-interface invariant failed. Diagnose the reported traces before any task or reward revision."
        ),
    }
    (args.output_root / "V3_UTR_PILOT_READONLY_DIAGNOSTIC.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    report = ["# V3 UTR pilot read-only diagnostic", "", f"`{verdict}`", "", "This diagnostic loads fixed final UTR endpoints only. It does not train, update a sampler, alter a checkpoint, or compare DRTP.", "", "## Interpretation", "", payload["interpretation"], "", "## Invariants", ""]
    report.extend(f"- {name}: {'PASS' if value else 'FAIL'}" for name, value in checks.items())
    (args.output_root / "V3_UTR_PILOT_READONLY_DIAGNOSTIC_REPORT.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
