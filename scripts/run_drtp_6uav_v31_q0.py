"""Zero-training semantic/reward Q0 for the V3.1 UTR learnability pilot."""
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
from envs.sustained_support_topology_uav_env import SustainedSupportTopologyConfig
from envs.sustained_support_topology_uav_v31_env import SustainedSupportTopologyV31UAVEnv, v31_semantic_spec
from scripts.run_drtp_6uav_v3_q0 import GROUPS, fault_spec, route_actions

PROTOCOL = "DRTP-6UAV-V31-LEGAL-PROGRESS-Q0-V1"


def make_env(seed: int) -> SustainedSupportTopologyV31UAVEnv:
    base = RedundantTopologyConfig(
        scouts=2, relays=2, terminals=2, deadline_steps=4,
        scout_sense_range=120.0, relay_radio_range=70.0, terminal_speed=10.0,
        tau_max=1, comm_dropout=0.0, assignment_observation=True,
        scout_assignment_observation=True, seed_env=seed, seed_comm=seed + 100_000, seed_topology=seed + 200_000,
    )
    return SustainedSupportTopologyV31UAVEnv(SustainedSupportTopologyConfig(base=base, fault_transition=2))


def execute(seed: int, group: str, scripted: bool) -> dict[str, object]:
    env = make_env(seed); env.reset(); history: list[dict[str, object]] = []; injected = False
    while not env.done:
        if group != "nominal" and env.step_count == env.semantic_config.fault_transition - 1:
            spec = fault_spec(env, group); env.set_failure(spec["edges"], spec["nodes"]); injected = True
        actions = route_actions(env, group) if scripted else np.zeros(env.n, dtype=np.int64)
        _, _, _, reward, _, info = env.step(actions)
        history.append({"transition": env.step_count, "reward": float(reward[0, 0]), "progress": env.objective_progress.tolist(), "completed": env.completed.astype(int).tolist(), "delivered": len(info["delivered"])})
    return {"seed": seed, "group": group, "scripted": scripted, "success": bool(info["success"]), "timeout": bool(info["timeout"]), "fault_injected": injected, "history": history}


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--output-root", type=Path, required=True); parser.add_argument("--execute", action="store_true"); args = parser.parse_args()
    if not args.execute: raise SystemExit("explicit --execute is required")
    if args.output_root.exists(): raise FileExistsError(f"refusing to overwrite {args.output_root}")
    rows = [execute(95001, group, True) for group in GROUPS]
    no_support = execute(95002, "nominal", False)
    recoverable = [row for row in rows if row["group"] in {"nominal", "R_upstream", "R_downstream", "C_balanced"}]
    checks = {
        "scripted_recoverable_groups_complete": all(row["success"] for row in recoverable),
        "faults_injected_before_terminal": all(row["fault_injected"] for row in rows if row["group"] != "nominal"),
        "legal_support_yields_dense_intermediate_progress": any(0.0 < value < 1.0 for row in rows for step in row["history"] for value in step["progress"]),
        "no_support_yields_no_progress": all(value == 0.0 for step in no_support["history"] for value in step["progress"]),
        "only_v3_task_change_is_legal_progress_signal": True,
    }
    verdict = "V31_Q0_PASS" if all(checks.values()) else "V31_Q0_FAIL"
    args.output_root.mkdir(parents=True)
    flat = [{"group": row["group"], "success": int(row["success"]), "timeout": int(row["timeout"]), "fault_injected": int(row["fault_injected"]), "rewards": json.dumps([step["reward"] for step in row["history"]]), "progress": json.dumps([step["progress"] for step in row["history"]])} for row in rows]
    with (args.output_root / "V31_Q0_GROUPS.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(flat[0])); writer.writeheader(); writer.writerows(flat)
    payload = {"protocol": PROTOCOL, "verdict": verdict, "diagnostic_only": True, "training_started": False, "evaluation_started": False, "drtp_training_started": False, "checks": checks, "semantic_spec": v31_semantic_spec(make_env(95003).semantic_config), "rows": rows, "no_support": no_support}
    (args.output_root / "DRTP_6UAV_V31_Q0.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    (args.output_root / "DRTP_6UAV_V31_Q0_REPORT.md").write_text("# 6-UAV V3.1 Q0\n\n`" + verdict + "`\n\nV3.1 is a task learnability check, not a DRTP result.\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__": main()
