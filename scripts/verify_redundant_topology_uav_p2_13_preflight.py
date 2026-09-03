"""Zero-training integrity preflight for the P2.13 requalification contract."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from algorithms.redundant_topology_role_sg_mappo import RoleSharedSGMPPO
from envs.redundant_topology_uav_env import RedundantTopologyUAVEnv, scale_config

PROTOCOL = "P2_13_SCOUT_TERMINAL_ASSIGNED_REQUALIFICATION_PREFLIGHT_V1"
SEEDS = (67011, 67012, 67013, 67014, 67015)
HISTORICAL = {6201, 6202, 6203, 65011, 65012, 65013, 65014, 65015, 66011, 66012, 66013, 66014, 66015}
RESERVED = {67021, 67022, 67023, 67024, 67025, 67031, 67032, 67033, 67034, 67035}
CONTRACT = ROOT / "docs/redundant_topology_uav_p2_13_20260903/P2_13_ASSIGNED_BASELINE_REQUALIFICATION_CONTRACT.md"


def bijective(rows: np.ndarray) -> bool:
    return bool(all(np.count_nonzero(row) == 1 for row in rows) and len({int(np.argmax(row)) for row in rows}) == len(rows))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", default="results/development/redundant_topology_uav_p2_13/preflight")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        print(json.dumps({"protocol": PROTOCOL, "execute_required": True, "training_started": False})); return
    out = Path(args.output_root)
    if out.exists():
        raise RuntimeError("P2.13 preflight output exists; refusing overwrite")
    env = RedundantTopologyUAVEnv(scale_config("main", assignment_observation=True, scout_assignment_observation=True))
    _, _, graph = env.reset(seed_env=SEEDS[0])
    base_dim = 8 + 3 * env.k
    scout_rows = graph["node_features"][env.scout_ids, base_dim:]
    terminal_rows = graph["node_features"][env.terminal_ids, base_dim:]
    relay_rows = graph["node_features"][env.relay_ids, base_dim:]
    agent = RoleSharedSGMPPO(env.obs_dim, env.share_obs_dim, env.action_dim)
    with torch.no_grad():
        forward = agent.scout_actor(torch.as_tensor(graph["node_features"][None]), torch.as_tensor(graph["roles"][None]), torch.as_tensor(graph["active_adj"][None], dtype=torch.float32))
    checks = {
        "five_fresh_paired_training_seeds": len(SEEDS) == len(set(SEEDS)) == 5 and not set(SEEDS) & HISTORICAL,
        "reserved_cohorts_disjoint": not set(SEEDS) & RESERVED and not HISTORICAL & RESERVED,
        "scout_and_terminal_assignment_enabled": env.config.assignment_observation and env.config.scout_assignment_observation,
        "single_append_block_shape": env.obs_dim == base_dim + env.k,
        "scout_assignment_bijective": bijective(scout_rows),
        "terminal_assignment_bijective": bijective(terminal_rows),
        "relay_assignment_zero": bool(np.all(relay_rows == 0)),
        "corrected_role_learner_importable": agent.scout_actor is not agent.terminal_actor and agent.relay_actor.action_dim == 1,
        "role_actor_forward_finite": bool(torch.isfinite(forward).all()),
        "contract_present": CONTRACT.exists(),
        "training_started": False,
        "evaluation_started": False,
        "automatic_continuation": False,
    }
    required = {key: value for key, value in checks.items() if key not in {"training_started", "evaluation_started", "automatic_continuation"}}
    verdict = "P2_13_PREFLIGHT_PASS" if all(required.values()) else "P2_13_PREFLIGHT_FAIL"
    source = ROOT / "envs/redundant_topology_uav_env.py"
    payload = {"protocol": PROTOCOL, "verdict": verdict, "checks": checks, "training_seeds": SEEDS, "reserved_independent_replication": sorted(RESERVED)[:5], "reserved_confirmatory": sorted(RESERVED)[5:], "environment_sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "training_started": False, "p3_authorized": False, "automatic_continuation": False}
    diag = out / "diagnostics"; diag.mkdir(parents=True)
    (diag / "P2_13_PREFLIGHT.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    (diag / "P2_13_PREFLIGHT_REPORT.md").write_text("# P2.13 preflight\n\n**Verdict:** `" + verdict + "`.\n\n```json\n" + json.dumps(payload, indent=2) + "\n```\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    if verdict != "P2_13_PREFLIGHT_PASS":
        raise RuntimeError("P2.13 preflight failed")


if __name__ == "__main__":
    main()
