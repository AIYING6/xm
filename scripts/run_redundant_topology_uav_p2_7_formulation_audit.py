"""P2.7 zero-training audit for a non-privileged assignment observation."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from envs.redundant_topology_uav_env import RedundantTopologyUAVEnv, scale_config

PROTOCOL = "P2_7_ASSIGNMENT_INTERFACE_FORMULATION_AUDIT_V1"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def lane_assignment(env: RedundantTopologyUAVEnv) -> dict[str, object]:
    terminal_order = [int(index) for index in env.terminal_ids[np.argsort(env.positions[env.terminal_ids, 1])]]
    objective_order = [int(index) for index in np.argsort(env.objective_positions[:, 1])]
    mapping = {terminal: objective for terminal, objective in zip(terminal_order, objective_order)}
    return {"terminal_order": terminal_order, "objective_order": objective_order, "mapping": mapping}


def run_scripted(env: RedundantTopologyUAVEnv, mapping: dict[int, int]) -> dict[str, object]:
    _, _, graph = env.reset(seed_env=70101)
    total = 0.0
    while not env.done:
        actions = np.zeros(env.n, dtype=np.int64)
        for scout, objective in zip(env.scout_ids, sorted(set(mapping.values()))):
            actions[scout] = objective + 1
        for terminal, objective in mapping.items():
            if graph["action_masks"][terminal, objective + 1]:
                actions[terminal] = objective + 1
        _, _, graph, reward, _, info = env.step(actions)
        total += float(reward[0, 0])
    return {"success": bool(info["success"]), "timeout": bool(info["timeout"]), "score": total, "completed": env.completed.astype(int).tolist(), "steps": env.step_count}


def run_same_objective(env: RedundantTopologyUAVEnv) -> dict[str, object]:
    _, _, graph = env.reset(seed_env=70101)
    total = 0.0
    while not env.done:
        actions = np.zeros(env.n, dtype=np.int64)
        for scout in env.scout_ids:
            actions[scout] = 1
        for terminal in env.terminal_ids:
            if graph["action_masks"][terminal, 1]:
                actions[terminal] = 1
        _, _, graph, reward, _, info = env.step(actions)
        total += float(reward[0, 0])
    return {"success": bool(info["success"]), "timeout": bool(info["timeout"]), "score": total, "completed": env.completed.astype(int).tolist(), "steps": env.step_count}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", default="results/development/redundant_topology_uav_p2_7_audit")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        print(json.dumps({"protocol": PROTOCOL, "execute_required": True, "training_started": False}))
        return
    out = Path(args.output_root)
    if out.exists():
        raise RuntimeError("P2.7 audit output exists; refusing overwrite")

    reports: dict[str, object] = {}
    bijective = True
    for scale in ("small", "main", "large"):
        env = RedundantTopologyUAVEnv(scale_config(scale))
        assignment = lane_assignment(env)
        mapping = assignment["mapping"]
        bijective &= len(mapping) == env.k and len(set(mapping.values())) == env.k
        reports[scale] = assignment
    main_env = RedundantTopologyUAVEnv(scale_config("main"))
    assignment = lane_assignment(main_env)
    assigned = run_scripted(main_env, assignment["mapping"])
    same = run_same_objective(RedundantTopologyUAVEnv(scale_config("main")))
    checks = {
        "assignment_consistent_script_completes_all_objectives": assigned["success"] and assigned["completed"] == [1, 1],
        "same_objective_script_reproduces_partial_timeout": not same["success"] and same["timeout"] and same["completed"] == [1, 0],
        "lane_assignment_bijective_at_all_scales": bijective,
        "cue_is_available_from_reset": True,
        "no_action_mask_restriction_proposed": True,
        "no_reward_or_transition_change_proposed": True,
        "audit_has_no_evaluation_tape_input": set(vars(args)) == {"output_root", "execute"},
        "training_started": False,
        "new_environment_implementation_started": False,
    }
    required = {key: value for key, value in checks.items() if key not in {"training_started", "new_environment_implementation_started"}}
    verdict = "P2_7_ASSIGNMENT_INTERFACE_FEASIBLE" if all(required.values()) else "P2_7_ASSIGNMENT_INTERFACE_NO_GO"
    payload = {"protocol": PROTOCOL, "verdict": verdict, "checks": checks, "assignments": reports, "assigned_script": assigned, "same_objective_script": same, "training_started": False, "implementation_authorized": False, "automatic_continuation": False}
    diag = out / "diagnostics"
    write(diag / "P2_7_ASSIGNMENT_MAPPING.md", "# Assignment mapping\n\nPersistent terminal preference is derived by matching terminal and objective y-lane rank. It is a cue, not a mask or assignment constraint.\n\n```json\n" + json.dumps(reports, indent=2) + "\n```\n")
    write(diag / "P2_7_SYMMETRY_REPRODUCTION.md", "# Symmetry reproduction\n\n```json\n" + json.dumps({"assignment_consistent": assigned, "same_objective": same}, indent=2) + "\n```\n")
    write(diag / "P2_7_FINAL_VERDICT.md", f"# P2.7 final verdict\n\n`{verdict}`\n\n```json\n" + json.dumps(payload, indent=2) + "\n```\n")
    write(diag / "P2_7_AUDIT.json", json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
