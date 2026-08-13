"""Explicit S2 graph orientation and failure-legality checks."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from envs.uav_intercept_3d_env import (  # noqa: E402
    RELATION_COMMUNICATION,
    RELATION_TASK_SUPPORT,
    UAVIntercept3DConfig,
    UAVIntercept3DEnv,
)


def main() -> None:
    env = UAVIntercept3DEnv(UAVIntercept3DConfig(seed=1701, failed_blue_agent=1, node_failure_start_step=1, node_failure_duration_steps=10))
    env.reset()
    env.blue_pos[:] = np.asarray([[-2000, -6000, 5000], [-2000, 0, 5000], [-2000, 6000, 5000]], dtype=np.float32)
    env._update_sensing_and_comm()
    actions = np.zeros(env.num_agents, dtype=np.int64)
    _, _, graph, _, _, info = env.step(actions)
    checks = {
        "orientation_receiver_sender": bool(graph["relation_adj"].shape[1:] == (4, 4)),
        "self_edges_present": bool(np.all(np.diag(graph["adj"]) == 1.0)),
        "failure_active": bool(info["node_failure_active"] == 1.0),
        "invalid_comm_edge_zeroed": bool(graph["relation_adj"][RELATION_COMMUNICATION, 2, 1] == 0.0),
        "task_support_does_not_bypass_comm": bool(graph["relation_adj"][RELATION_TASK_SUPPORT, 2, 1] == 0.0),
    }
    if not all(checks.values()):
        raise AssertionError(checks)
    result = {"protocol": "PHASE-S2-GRAPH-LEGALITY-V1", "checks": checks, "pass": True, "training_started": False}
    out = ROOT / "results" / "development" / "phase_s2_graph_legality.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
