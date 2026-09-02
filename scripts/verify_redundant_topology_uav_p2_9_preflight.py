"""Zero-training integrity preflight for P2.9 assigned-observation training."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from algorithms.redundant_topology_role_sg_mappo import RoleSharedSGMPPO
from envs.redundant_topology_uav_env import RedundantTopologyUAVEnv, scale_config

PROTOCOL = "P2_9_ASSIGNED_BASELINE_QUALIFICATION_PREFLIGHT_V1"
SEEDS = (66011, 66012, 66013, 66014, 66015)
HISTORICAL = {6201, 6202, 6203, 65011, 65012, 65013, 65014, 65015}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", default="results/development/redundant_topology_uav_p2_9/preflight")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        print(json.dumps({"protocol": PROTOCOL, "execute_required": True, "training_started": False})); return
    out = Path(args.output_root)
    if out.exists():
        raise RuntimeError("P2.9 preflight output exists; refusing overwrite")
    env = RedundantTopologyUAVEnv(scale_config("main", assignment_observation=True))
    _, _, graph = env.reset(seed_env=SEEDS[0])
    base_dim = 8 + 3 * env.k
    preferences = graph["node_features"][env.terminal_ids, base_dim:]
    learner = RoleSharedSGMPPO(env.obs_dim, env.share_obs_dim, env.action_dim)
    source = ROOT / "envs/redundant_topology_uav_env.py"
    contract = ROOT / "docs/redundant_topology_uav_p2_9_20260903/P2_9_ASSIGNED_BASELINE_QUALIFICATION_CONTRACT.md"
    checks = {
        "five_fresh_matched_seeds": len(SEEDS) == len(set(SEEDS)) == 5 and not set(SEEDS) & HISTORICAL,
        "assignment_observation_enabled": env.config.assignment_observation and env.obs_dim == base_dim + env.k,
        "terminal_preferences_bijective": all(np.count_nonzero(row) == 1 for row in preferences) and len({int(np.argmax(row)) for row in preferences}) == env.k,
        "nonterminal_preference_zero": bool(np.all(graph["node_features"][list(env.scout_ids) + list(env.relay_ids), base_dim:] == 0)),
        "role_shared_learner_importable": learner.scout_actor is not learner.terminal_actor and learner.relay_actor.action_dim == 1,
        "contract_present": contract.exists(),
        "training_started": False,
        "evaluation_started": False,
        "automatic_continuation": False,
    }
    required = {key: value for key, value in checks.items() if key not in {"training_started", "evaluation_started", "automatic_continuation"}}
    verdict = "P2_9_PREFLIGHT_PASS" if all(required.values()) else "P2_9_PREFLIGHT_FAIL"
    payload = {"protocol": PROTOCOL, "verdict": verdict, "checks": checks, "seeds": SEEDS, "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "training_started": False, "p3_authorized": False, "automatic_continuation": False}
    diag = out / "diagnostics"; diag.mkdir(parents=True)
    (diag / "P2_9_PREFLIGHT.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    (diag / "P2_9_PREFLIGHT_REPORT.md").write_text(f"# P2.9 preflight\n\n**Verdict:** `{verdict}`.\n\n```json\n" + json.dumps(payload, indent=2) + "\n```\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    if verdict != "P2_9_PREFLIGHT_PASS":
        raise RuntimeError("P2.9 preflight failed")


if __name__ == "__main__":
    main()
