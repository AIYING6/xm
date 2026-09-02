"""P2.8 deterministic validation for the opt-in assignment observation."""
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

PROTOCOL = "P2_8_LANE_ASSIGNMENT_OBSERVATION_VALIDATION_V1"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def assignment_block(env: RedundantTopologyUAVEnv, graph: dict[str, np.ndarray], terminal: int) -> np.ndarray:
    return graph["node_features"][terminal, 8 + 3 * env.k:]


def delivered_signature(info: dict[str, object]) -> list[tuple[object, ...]]:
    return [
        (item["objective_id"], item["source_scout"], item["relay_id"], tuple(item["route"]), item["t_sense"], item["t_receive"])
        for item in info["delivered"]
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", default="results/development/redundant_topology_uav_p2_8")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        print(json.dumps({"protocol": PROTOCOL, "execute_required": True, "training_started": False}))
        return
    out = Path(args.output_root)
    if out.exists():
        raise RuntimeError("P2.8 output exists; refusing overwrite")

    default = RedundantTopologyUAVEnv(scale_config("main", seed_env=72001, seed_comm=72002, seed_topology=72003))
    enabled = RedundantTopologyUAVEnv(scale_config("main", seed_env=72001, seed_comm=72002, seed_topology=72003, assignment_observation=True))
    _, _, default_graph = default.reset()
    _, _, enabled_graph = enabled.reset()
    default_shape_unchanged = default.obs_dim == 8 + 3 * default.k and default_graph["node_features"].shape == (default.n, default.obs_dim)
    enabled_shape = enabled.obs_dim == default.obs_dim + enabled.k and enabled_graph["node_features"].shape == (enabled.n, enabled.obs_dim)
    terminal_blocks = {int(terminal): assignment_block(enabled, enabled_graph, int(terminal)).tolist() for terminal in enabled.terminal_ids}
    one_hot = all(np.count_nonzero(block) == 1 and np.isclose(np.sum(block), 1.0) for block in terminal_blocks.values())
    role_local = all(np.count_nonzero(enabled_graph["node_features"][agent, 8 + 3 * enabled.k:]) == 0 for agent in np.concatenate((enabled.scout_ids, enabled.relay_ids)))
    bijective = len({int(np.argmax(block)) for block in terminal_blocks.values()}) == enabled.k
    initial_masks_equal = np.array_equal(default_graph["action_masks"], enabled_graph["action_masks"])

    actions = np.asarray([1, 2, 0, 0, 0, 0], dtype=np.int64)
    transition_equal = True
    preference_stable = True
    for _ in range(3):
        d_obs, d_share, d_graph, d_reward, d_done, d_info = default.step(actions)
        e_obs, e_share, e_graph, e_reward, e_done, e_info = enabled.step(actions)
        transition_equal &= np.array_equal(d_obs, e_obs[:, :default.obs_dim]) and np.array_equal(d_share, e_share) and np.array_equal(d_reward, e_reward) and np.array_equal(d_done, e_done)
        transition_equal &= np.array_equal(d_graph["action_masks"], e_graph["action_masks"]) and d_info["signature"] == e_info["signature"] and delivered_signature(d_info) == delivered_signature(e_info)
        for terminal, block in terminal_blocks.items():
            preference_stable &= np.array_equal(assignment_block(enabled, e_graph, terminal), np.asarray(block, dtype=np.float32))
    runtime = enabled.runtime_state_dict()
    restored = RedundantTopologyUAVEnv(scale_config("main", assignment_observation=True))
    restored.load_runtime_state_dict(runtime)
    _, _, restored_graph, restored_reward, restored_done, restored_info = restored.step(actions)
    _, _, enabled_graph_next, enabled_reward_next, enabled_done_next, enabled_info_next = enabled.step(actions)
    restore_exact = np.array_equal(restored_reward, enabled_reward_next) and np.array_equal(restored_done, enabled_done_next) and restored_info["signature"] == enabled_info_next["signature"] and delivered_signature(restored_info) == delivered_signature(enabled_info_next) and np.array_equal(restored_graph["node_features"], enabled_graph_next["node_features"])

    scales = {}
    scale_bijection = True
    for name in ("small", "main", "large"):
        env = RedundantTopologyUAVEnv(scale_config(name, assignment_observation=True))
        _, _, graph = env.reset()
        blocks = [assignment_block(env, graph, int(terminal)) for terminal in env.terminal_ids]
        scale_bijection &= len(blocks) == env.k and all(np.count_nonzero(block) == 1 for block in blocks) and len({int(np.argmax(block)) for block in blocks}) == env.k
        scales[name] = [block.tolist() for block in blocks]
    checks = {
        "default_p1_observation_shape_unchanged": default_shape_unchanged,
        "enabled_shape_is_opt_in_append_only": enabled_shape,
        "terminal_preference_one_hot": one_hot,
        "preference_role_local": role_local,
        "preference_bijective_main": bijective,
        "preference_bijective_all_scales": scale_bijection,
        "action_masks_unchanged": initial_masks_equal,
        "transitions_rewards_and_routes_unchanged": transition_equal,
        "preference_stable_within_episode": preference_stable,
        "enabled_runtime_restore_exact": restore_exact,
        "training_started": False,
        "evaluation_started": False,
    }
    required = {key: value for key, value in checks.items() if key not in {"training_started", "evaluation_started"}}
    verdict = "P2_8_ASSIGNMENT_OBSERVATION_VALIDATED" if all(required.values()) else "P2_8_ASSIGNMENT_OBSERVATION_FAIL"
    payload = {"protocol": PROTOCOL, "verdict": verdict, "checks": checks, "main_terminal_preference": terminal_blocks, "scale_preferences": scales, "training_started": False, "p2_9_authorized": False, "automatic_continuation": False}
    diag = out / "diagnostics"
    write(diag / "P2_8_INTERFACE_CONTRACT.md", (ROOT / "docs/redundant_topology_uav_p2_8_20260903/P2_8_ASSIGNMENT_OBSERVATION_CONTRACT.md").read_text(encoding="utf-8"))
    write(diag / "P2_8_PREFERENCE_AUDIT.md", "# P2.8 preference audit\n\n```json\n" + json.dumps({"main": terminal_blocks, "scales": scales}, indent=2) + "\n```\n")
    write(diag / "P2_8_FINAL_VERDICT.md", f"# P2.8 final verdict\n\n`{verdict}`\n\n```json\n" + json.dumps(payload, indent=2) + "\n```\n")
    write(diag / "P2_8_VALIDATION.json", json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
