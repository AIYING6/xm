"""No-training audit of the opt-in physical Scout -> Relay -> Attacker path."""
from __future__ import annotations

import csv
import json
from dataclasses import replace
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from envs.uav_intercept_3d_env import ROLE_ATTACKER, ROLE_INTERCEPTOR, ROLE_RELAY, ROLE_SCOUT
from scripts import run_l4_corrected_contract_requalification as l4r
from scripts import run_l4_delay_development as l4
from scripts import run_new_project_l0_single_interceptor as l0

OUT = ROOT / "results" / "relay_path_redesign_identifiability_audit_v3"
SEEDS = tuple(range(910_000, 910_008))
PROTOCOL = "RELAY_PATH_REDESIGN_IDENTIFIABILITY_AUDIT_V1"


def cfg(seed: int, out_dir: Path):
    return replace(
        l4r.cfg(seed, out_dir, updates=1),
        relay_identifiable_initial_formation=True,
        relay_identifiable_target_initial_position=(3_500.0, -4_200.0, 5_000.0),
        protocol_version=PROTOCOL,
        run_id=f"relay_path_audit_seed{seed}",
    )


def role_id(env, role: int) -> int:
    return next(i for i, typ in enumerate(env.config.blue_types) if typ.role == role)


def action(env):
    """Transparent oracle controller, used only to establish task feasibility."""
    value = np.asarray(l0.scripted_oracle_actions(env), dtype=np.int64)
    out = l4._continuous_from_legacy(env, value)
    for i, typ in enumerate(env.config.blue_types):
        if typ.role not in {ROLE_ATTACKER, ROLE_INTERCEPTOR}:
            out[i, 2] = -1.0
    return out


def run(seed: int, relay_disabled: bool = False):
    env = l0.make_env(cfg(seed, OUT / "template"), seed, training=False)
    relay = role_id(env, ROLE_RELAY); attacker = role_id(env, ROLE_ATTACKER); scout = role_id(env, ROLE_SCOUT)
    if relay_disabled:
        original = env._is_comm_failed
        env._is_comm_failed = lambda agent: bool(original(agent) or agent == relay)  # type: ignore[method-assign]
    obs, share, graph = env.reset()
    rows, observations, states = [], [], []
    while True:
        command = action(env)
        obs, share, graph, _reward, dones, info = env.step(command)
        path = list(env.target_cache_path[attacker])
        direct_distance = float(np.linalg.norm(env.blue_pos[scout] - env.blue_pos[attacker]))
        direct_range = float(env.config.communication_range_scale * min(env.config.blue_types[scout].comm_range, env.config.blue_types[attacker].comm_range))
        relay_sender_packet = env.sender_packet_cache[attacker].get(relay)
        relay_packet_target = bool(relay_sender_packet and float(relay_sender_packet.get("target_validity", 0.0)) > 0.5)
        relay_only = bool(
            env._has_fresh_target_cache(attacker)
            and path == [scout, relay, attacker]
            and env.detected_by[attacker] < 0.5
            and direct_distance > direct_range
        )
        rows.append({
            "episode_seed": seed, "step": int(env.step_count),
            "scout_to_relay_delivered": int(env.comm_adj[relay, scout] > 0.5),
            "relay_to_attacker_delivered": int(env.comm_adj[attacker, relay] > 0.5),
            "direct_scout_to_attacker_physical": int(direct_distance <= direct_range),
            "attacker_local_target_sensing": int(env.detected_by[attacker] > 0.5),
            "attacker_cache_valid": int(env._has_fresh_target_cache(attacker)),
            "attacker_cache_path": ">".join(map(str, path)),
            "attacker_cache_contains_relay": int(relay in path),
            "relay_status_packet_has_target_claim": int(relay_packet_target),
            "relay_only_target_evidence": int(relay_only),
        })
        observations.append(obs[attacker].copy())
        states.append((env.blue_pos.copy(), env.red_pos.copy()))
        if bool(np.all(dones)):
            return rows, observations, states, l0.outcome(info), int(info["step"])


def main() -> None:
    if OUT.exists() and any(OUT.iterdir()):
        raise FileExistsError(f"refusing to overwrite audit output: {OUT}")
    OUT.mkdir(parents=True, exist_ok=True)
    records, episodes = [], []
    for seed in SEEDS:
        active_rows, active_obs, active_states, active_outcome, active_steps = run(seed)
        blocked_rows, blocked_obs, blocked_states, blocked_outcome, blocked_steps = run(seed, relay_disabled=True)
        records.extend(active_rows)
        n = min(len(active_obs), len(blocked_obs))
        info_changed = any(not np.array_equal(active_obs[i], blocked_obs[i]) for i in range(n))
        physical_equal = all(np.array_equal(active_states[i][0], blocked_states[i][0]) and np.array_equal(active_states[i][1], blocked_states[i][1]) for i in range(n))
        relay_steps = [r["step"] for r in active_rows if r["relay_only_target_evidence"]]
        episodes.append({
            "episode_seed": seed, "oracle_outcome": active_outcome, "oracle_steps": active_steps,
            "relay_disabled_outcome": blocked_outcome, "first_relay_only_evidence_step": min(relay_steps) if relay_steps else None,
            "relay_only_evidence_steps": len(relay_steps),
            "attacker_information_changes_when_relay_disabled": int(info_changed),
            "physical_trajectory_is_identical": int(physical_equal),
        })
    with (OUT / "relay_path_records.csv").open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0])); writer.writeheader(); writer.writerows(records)
    with (OUT / "relay_path_episode_summary.csv").open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(episodes[0])); writer.writeheader(); writer.writerows(episodes)
    all_two_hop = all(e["relay_only_evidence_steps"] > 0 for e in episodes)
    all_changed = all(e["attacker_information_changes_when_relay_disabled"] for e in episodes)
    all_physics = all(e["physical_trajectory_is_identical"] for e in episodes)
    oracle_feasible = all(e["oracle_outcome"] == "NEUTRALIZED" for e in episodes)
    onset_exists = all(e["first_relay_only_evidence_step"] is not None and int(e["first_relay_only_evidence_step"]) < int(e["oracle_steps"]) for e in episodes)
    passed = all_two_hop and all_changed and all_physics and oracle_feasible and onset_exists
    payload = {
        "protocol": PROTOCOL, "performance_use_prohibited": True, "episode_seeds": list(SEEDS),
        "conditions": {"range_scale": 0.5, "dropout": 0.3, "delay_steps": 8, "actor_contract": "recipient-specific local sensing or delivered/cache-valid target packet"},
        "checks": {"relay_only_evidence_every_episode": all_two_hop, "relay_removal_changes_attacker_information": all_changed, "relay_removal_preserves_physics": all_physics, "oracle_neutralization_every_episode": oracle_feasible, "pre_terminal_failure_onset_window_exists": onset_exists},
        "episodes": episodes,
        "verdict": "RELAY_PATH_IDENTIFIED__READY_FOR_L5_FAILURE_CALIBRATION" if passed else "RELAY_PATH_NO_GO__RELAY_FAILURE_CLAIM_DROPPED",
        "no_l5_training_authorized": True,
    }
    (OUT / "RELAY_PATH_IDENTIFIABILITY_AUDIT.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
