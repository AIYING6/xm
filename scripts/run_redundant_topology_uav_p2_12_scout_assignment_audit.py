"""Deterministic, zero-training P2.12 Scout-assignment interface audit."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from algorithms.redundant_topology_role_sg_mappo import RoleSharedSGMPPO
from envs.redundant_topology_uav_env import ROLE_RELAY, ROLE_SCOUT, ROLE_TERMINAL, RedundantTopologyUAVEnv, scale_config

PROTOCOL = "P2_12_SCOUT_ASSIGNMENT_INTERFACE_AUDIT_V1"
CONTRACT = ROOT / "docs/redundant_topology_uav_p2_12_20260903/P2_12_SCOUT_ASSIGNMENT_INTERFACE_CONTRACT.md"


def one_hot_bijective(rows: np.ndarray) -> bool:
    return bool(all(np.count_nonzero(row) == 1 for row in rows) and len({int(np.argmax(row)) for row in rows}) == len(rows))


def rollout_signature(env: RedundantTopologyUAVEnv) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    env.reset(seed_env=901020)
    actions = (
        np.asarray([1, 2, 0, 0, 0, 0], dtype=np.int64),
        np.asarray([1, 2, 0, 0, 1, 2], dtype=np.int64),
        np.asarray([1, 2, 0, 0, 1, 2], dtype=np.int64),
    )
    reward, done = [], []
    for action in actions:
        _, _, _, r, d, _ = env.step(action)
        reward.append(r.copy()); done.append(d.copy())
    return env.positions.copy(), env.completed.copy(), np.stack(reward), np.stack(done)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", default="results/development/redundant_topology_uav_p2_12_audit")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        print(json.dumps({"protocol": PROTOCOL, "execute_required": True, "training_started": False})); return
    out = Path(args.output_root)
    if out.exists():
        raise RuntimeError("P2.12 audit output exists; refusing overwrite")
    legacy = RedundantTopologyUAVEnv(scale_config("main"))
    terminal_only = RedundantTopologyUAVEnv(scale_config("main", assignment_observation=True))
    enabled = RedundantTopologyUAVEnv(scale_config("main", assignment_observation=True, scout_assignment_observation=True))
    _, _, terminal_graph = terminal_only.reset(seed_env=901011)
    _, _, enabled_graph = enabled.reset(seed_env=901011)
    base_dim = 8 + 3 * enabled.k
    terminal_rows = enabled_graph["node_features"][enabled.terminal_ids, base_dim:]
    scout_rows = enabled_graph["node_features"][enabled.scout_ids, base_dim:]
    relay_rows = enabled_graph["node_features"][enabled.relay_ids, base_dim:]
    scales_ok = True
    scale_preferences: dict[str, list[list[float]]] = {}
    for scale in ("small", "main", "large"):
        env = RedundantTopologyUAVEnv(scale_config(scale, assignment_observation=True, scout_assignment_observation=True))
        _, _, graph = env.reset(seed_env=901000)
        dim = 8 + 3 * env.k
        s_rows = graph["node_features"][env.scout_ids, dim:]
        t_rows = graph["node_features"][env.terminal_ids, dim:]
        scales_ok &= one_hot_bijective(s_rows) and one_hot_bijective(t_rows)
        scale_preferences[scale] = s_rows.tolist()
    runtime_source = RedundantTopologyUAVEnv(scale_config("main", assignment_observation=True, scout_assignment_observation=True))
    runtime_source.reset(seed_env=901012)
    restored = RedundantTopologyUAVEnv(scale_config("main", assignment_observation=True, scout_assignment_observation=True))
    restored.load_runtime_state_dict(runtime_source.runtime_state_dict())
    forward_agent = RoleSharedSGMPPO(enabled.obs_dim, enabled.share_obs_dim, enabled.action_dim)
    with torch.no_grad():
        graph = enabled.graph_observation()
        obs = torch.as_tensor(graph["node_features"][None], dtype=torch.float32)
        roles = torch.as_tensor(graph["roles"][None], dtype=torch.long)
        adj = torch.as_tensor(graph["active_adj"][None], dtype=torch.float32)
        forward_finite = bool(torch.isfinite(forward_agent.scout_actor(obs, roles, adj)).all())
    checks = {
        "default_observation_shape_unchanged": legacy.obs_dim == 8 + 3 * legacy.k,
        "enabled_shape_uses_existing_single_append_block": enabled.obs_dim == terminal_only.obs_dim == base_dim + enabled.k,
        "terminal_only_behavior_preserved": bool(np.all(terminal_graph["node_features"][terminal_only.scout_ids, base_dim:] == 0)),
        "scout_preference_one_hot_bijective": one_hot_bijective(scout_rows),
        "terminal_preference_one_hot_bijective": one_hot_bijective(terminal_rows),
        "relay_preference_zero": bool(np.all(relay_rows == 0)),
        "all_scale_scout_and_terminal_bijections": scales_ok,
        "action_masks_unchanged": bool(np.array_equal(terminal_graph["action_masks"], enabled_graph["action_masks"])),
        "transition_reward_and_timing_unchanged": all(np.array_equal(a, b) for a, b in zip(rollout_signature(terminal_only), rollout_signature(enabled))),
        "enabled_runtime_restore_exact": bool(np.array_equal(runtime_source.actor_observation(), restored.actor_observation())),
        "role_actor_forward_finite": forward_finite,
        "contract_present": CONTRACT.exists(),
        "training_started": False,
        "evaluation_started": False,
        "automatic_continuation": False,
    }
    required = {key: value for key, value in checks.items() if key not in {"training_started", "evaluation_started", "automatic_continuation"}}
    verdict = "P2_12_SCOUT_ASSIGNMENT_INTERFACE_VALIDATED" if all(required.values()) else "P2_12_SCOUT_ASSIGNMENT_INTERFACE_FAIL"
    payload = {"protocol": PROTOCOL, "verdict": verdict, "checks": checks, "main_scout_preference": scout_rows.tolist(), "main_terminal_preference": terminal_rows.tolist(), "scale_scout_preferences": scale_preferences, "training_started": False, "p2_13_authorized": False, "automatic_continuation": False}
    diag = out / "diagnostics"; diag.mkdir(parents=True)
    (diag / "P2_12_AUDIT.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    (diag / "P2_12_FINAL_VERDICT.md").write_text("# P2.12 final verdict\n\n`" + verdict + "`\n\n```json\n" + json.dumps(payload, indent=2) + "\n```\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    if verdict != "P2_12_SCOUT_ASSIGNMENT_INTERFACE_VALIDATED":
        raise RuntimeError("P2.12 interface audit failed")


if __name__ == "__main__":
    main()
