"""Engineering-only replay: retaining telemetry must not alter a trajectory."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from envs.uav_intercept_3d_env import UAVIntercept3DConfig, UAVIntercept3DEnv


def run(seed: int, retain_telemetry: bool) -> list[dict]:
    env = UAVIntercept3DEnv(UAVIntercept3DConfig(seed=seed, target_policy="straight", max_steps=32))
    obs, share, graph = env.reset()
    tape = []
    rng = np.random.default_rng(seed + 991)
    for _ in range(32):
        actions = rng.integers(0, env.action_dim, size=env.num_agents, dtype=np.int64)
        nxt_obs, nxt_share, nxt_graph, rewards, dones, info = env.step(actions)
        row = {"actions": actions.copy(), "obs": nxt_obs.copy(), "share": nxt_share.copy(), "node": nxt_graph["node_feat"].copy(), "adj": nxt_graph["adj"].copy(), "rewards": rewards.copy(), "dones": dones.copy()}
        if retain_telemetry:
            row["telemetry"] = {"step": info["step"], "edges": info["comm_connectivity"], "failure": info["node_failure_active"]}
        tape.append(row)
        obs, share, graph = nxt_obs, nxt_share, nxt_graph
        if np.all(dones):
            break
    return tape


def main() -> None:
    p = argparse.ArgumentParser(); p.add_argument("--seed", type=int, default=1601); p.add_argument("--output", type=Path, default=Path("results/development/phase_s2_logging_invariance.json")); a = p.parse_args()
    off, on = run(a.seed, False), run(a.seed, True)
    if len(off) != len(on): raise AssertionError("trajectory length differs")
    fields = ["actions", "obs", "share", "node", "adj", "rewards", "dones"]
    max_diff = 0.0
    for left, right in zip(off, on):
        for field in fields:
            max_diff = max(max_diff, float(np.max(np.abs(np.asarray(left[field], dtype=np.float64) - np.asarray(right[field], dtype=np.float64)))))
    result = {"protocol": "PHASE-S2-LOGGING-INVARIANCE-V1", "seed": a.seed, "steps": len(off), "max_numeric_difference": max_diff, "pass": bool(max_diff == 0.0), "training_started": False}
    a.output.parent.mkdir(parents=True, exist_ok=True); a.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8"); print(json.dumps(result, indent=2))
    if max_diff != 0.0: raise SystemExit(1)


if __name__ == "__main__": main()
