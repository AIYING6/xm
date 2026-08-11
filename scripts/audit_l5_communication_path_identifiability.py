"""Read-only L5 communication-path identifiability audit.

This audit does not train or compare policies.  It asks whether the Relay is
actually on a legal delivered/cache-valid information path in the frozen L4
task before relay failure is made an experimental factor.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from envs.uav_intercept_3d_env import ROLE_ATTACKER, ROLE_INTERCEPTOR, ROLE_RELAY, ROLE_SCOUT
from scripts import run_new_project_l0_single_interceptor as l0
from scripts.run_l4_delay_development import _continuous_from_legacy, cfg


OUT = ROOT / "results" / "l5_communication_path_identifiability_audit"
SEEDS = tuple(range(900_000, 900_008))
HORIZON = 180
PROTOCOL = "L5_COMMUNICATION_PATH_IDENTIFIABILITY_AUDIT_V1"


def _role_name(role: int) -> str:
    return {ROLE_SCOUT: "SCOUT", ROLE_RELAY: "RELAY", ROLE_ATTACKER: "ATTACKER", ROLE_INTERCEPTOR: "ATTACKER"}.get(int(role), f"ROLE_{role}")


def _is_fresh_target_packet(env, packet: dict[str, object] | None) -> bool:
    if packet is None or float(packet.get("validity", 0.0)) <= 0.5:
        return False
    generation = int(packet.get("target_generation_step", -1))
    if generation < 0 or float(packet.get("target_confidence", 0.0)) < float(env.config.min_target_confidence):
        return False
    return env.step_count - generation <= int(env.config.max_target_message_age_steps)


def _scripted_action(env, obs: np.ndarray) -> np.ndarray:
    legacy = np.zeros(env.config.num_blue, dtype=np.int64)
    for i, typ in enumerate(env.config.blue_types):
        if typ.role in {ROLE_ATTACKER, ROLE_INTERCEPTOR}:
            legacy[i] = int(l0.heuristic_action(obs[i : i + 1])[0])
    action = _continuous_from_legacy(env, legacy, already_guidance=True)
    for i, typ in enumerate(env.config.blue_types):
        if typ.role not in {ROLE_ATTACKER, ROLE_INTERCEPTOR}:
            action[i, 2] = -1.0
    return action


def _record_step(env, episode_seed: int) -> list[dict[str, object]]:
    relay_id = next(i for i, typ in enumerate(env.config.blue_types) if typ.role == ROLE_RELAY)
    rows: list[dict[str, object]] = []
    for receiver, receiver_type in enumerate(env.config.blue_types):
        for sender, sender_type in enumerate(env.config.blue_types):
            if receiver == sender:
                continue
            distance = float(np.linalg.norm(env.blue_pos[sender] - env.blue_pos[receiver]))
            max_range = env.config.communication_range_scale * min(receiver_type.comm_range, sender_type.comm_range)
            packet = env.sender_packet_cache[receiver].get(sender)
            rows.append({
                "episode_seed": episode_seed,
                "step": int(env.step_count),
                "receiver": receiver,
                "receiver_role": _role_name(receiver_type.role),
                "sender": sender,
                "sender_role": _role_name(sender_type.role),
                "sender_is_relay": int(sender == relay_id),
                "receiver_is_relay": int(receiver == relay_id),
                "physical_link_available": int(distance <= max_range),
                "distance": distance,
                "effective_range": float(max_range),
                "instantaneously_delivered": int(env.comm_adj[receiver, sender] > 0.5),
                "sender_packet_present": int(packet is not None and float(packet.get("validity", 0.0)) > 0.5),
                "sender_packet_fresh_target_claim": int(_is_fresh_target_packet(env, packet)),
                "sender_packet_target_age": (int(env.step_count - int(packet["target_generation_step"])) if _is_fresh_target_packet(env, packet) else None),
            })
    for receiver, typ in enumerate(env.config.blue_types):
        path = list(env.target_cache_path[receiver])
        rows.append({
            "episode_seed": episode_seed,
            "step": int(env.step_count),
            "receiver": receiver,
            "receiver_role": _role_name(typ.role),
            "sender": -1,
            "sender_role": "TARGET_CACHE",
            "sender_is_relay": 0,
            "receiver_is_relay": int(receiver == relay_id),
            "physical_link_available": None,
            "distance": None,
            "effective_range": None,
            "instantaneously_delivered": None,
            "sender_packet_present": None,
            "sender_packet_fresh_target_claim": int(env._has_fresh_target_cache(receiver)),
            "sender_packet_target_age": int(env._local_target_cache_age(receiver)) if env._has_fresh_target_cache(receiver) else None,
            "target_cache_path": path,
            "target_cache_path_contains_relay": int(relay_id in path),
        })
    return rows


def _run_reference(episode_seed: int) -> tuple[list[dict[str, object]], list[np.ndarray], list[dict[str, object]]]:
    run_cfg = cfg(8901, OUT / "template", updates=1)
    env = l0.make_env(run_cfg, episode_seed, training=False)
    obs, _share, _graph = env.reset()
    rows: list[dict[str, object]] = []
    actions: list[np.ndarray] = []
    states: list[dict[str, object]] = []
    while True:
        action = _scripted_action(env, obs)
        actions.append(action.copy())
        obs, _share, _graph, _reward, dones, info = env.step(action)
        rows.extend(_record_step(env, episode_seed))
        states.append({"blue_pos": env.blue_pos.copy(), "red_pos": env.red_pos.copy(), "outcome": l0.outcome(info), "done": bool(np.all(dones))})
        if bool(np.all(dones)):
            return rows, actions, states


def _verify_physical_replay(episode_seed: int, actions: list[np.ndarray], reference_states: list[dict[str, object]]) -> dict[str, object]:
    """Disable Relay communication only while replaying the identical commands.

    This proves that the counterfactual changes no dynamics, positions, or
    mission terminal condition.  Legal-information causal effect is assessed
    separately by provenance erasure, so communication RNG stream changes do
    not masquerade as a Relay effect.
    """
    run_cfg = cfg(8901, OUT / "template", updates=1)
    env = l0.make_env(run_cfg, episode_seed, training=False)
    relay_id = next(i for i, typ in enumerate(env.config.blue_types) if typ.role == ROLE_RELAY)
    original_failed = env._is_comm_failed
    env._is_comm_failed = lambda agent_id: bool(original_failed(agent_id) or agent_id == relay_id)  # type: ignore[method-assign]
    env.reset()
    max_blue_error = max_red_error = 0.0
    for step, action in enumerate(actions):
        _obs, _share, _graph, _reward, dones, info = env.step(action)
        reference = reference_states[step]
        max_blue_error = max(max_blue_error, float(np.max(np.abs(env.blue_pos - reference["blue_pos"]))))
        max_red_error = max(max_red_error, float(np.max(np.abs(env.red_pos - reference["red_pos"]))))
        if bool(np.all(dones)):
            return {"episode_seed": episode_seed, "max_blue_position_error": max_blue_error,
                    "max_target_position_error": max_red_error, "same_terminal_outcome": int(l0.outcome(info) == reference["outcome"]),
                    "same_horizon": int(step + 1 == len(actions))}
    raise RuntimeError("replay did not terminate with reference action sequence")


def _summarize(rows: list[dict[str, object]]) -> dict[str, object]:
    pair_rows = [r for r in rows if r["sender"] != -1]
    cache_rows = [r for r in rows if r["sender"] == -1]
    def rate(predicate) -> float:
        selected = [r for r in pair_rows if predicate(r)]
        return float(np.mean([r["physical_link_available"] for r in selected])) if selected else 0.0
    def count(predicate, key: str) -> int:
        return int(sum(int(bool(r.get(key))) for r in pair_rows if predicate(r)))
    relay_out = lambda r: bool(r["sender_is_relay"])
    scout_to_relay = lambda r: r["sender_role"] == "SCOUT" and bool(r["receiver_is_relay"])
    relay_to_attacker = lambda r: bool(r["sender_is_relay"]) and r["receiver_role"] == "ATTACKER"
    attacker_direct_from_scout = lambda r: r["sender_role"] == "SCOUT" and r["receiver_role"] == "ATTACKER"
    path_with_relay = int(sum(int(bool(r.get("target_cache_path_contains_relay"))) for r in cache_rows))
    # Provenance-erasure counterfactual: remove exactly Relay-origin sender
    # evidence and target claims that traversed Relay, leaving every other
    # delivered packet untouched.  If none exist, legal actor C information is
    # mathematically invariant to disabling Relay outbound communication.
    relay_legal_evidence = count(relay_out, "sender_packet_present")
    relay_fresh_target_evidence = count(relay_out, "sender_packet_fresh_target_claim")
    return {
        "pair_step_records": len(pair_rows),
        "physical_link_rate": {
            "scout_to_relay": rate(scout_to_relay), "relay_to_attacker": rate(relay_to_attacker),
            "scout_to_attacker_direct": rate(attacker_direct_from_scout),
        },
        "actual_delivered_status_packet_records": {
            "scout_to_relay": count(scout_to_relay, "sender_packet_present"),
            "relay_to_attacker": count(relay_to_attacker, "sender_packet_present"),
            "scout_to_attacker_direct": count(attacker_direct_from_scout, "sender_packet_present"),
        },
        "fresh_target_claim_records": {
            "scout_to_relay": count(scout_to_relay, "sender_packet_fresh_target_claim"),
            "relay_to_attacker": count(relay_to_attacker, "sender_packet_fresh_target_claim"),
            "scout_to_attacker_direct": count(attacker_direct_from_scout, "sender_packet_fresh_target_claim"),
        },
        "target_cache_paths_containing_relay": path_with_relay,
        "relay_origin_legal_status_records": relay_legal_evidence,
        "relay_origin_fresh_target_claim_records": relay_fresh_target_evidence,
        "provenance_erasure_changes_legal_information": bool(relay_legal_evidence or relay_fresh_target_evidence or path_with_relay),
    }


def main() -> None:
    if OUT.exists() and any(OUT.iterdir()):
        raise FileExistsError(f"refusing to overwrite audit output: {OUT}")
    OUT.mkdir(parents=True, exist_ok=True)
    all_rows: list[dict[str, object]] = []
    replay = []
    for seed in SEEDS:
        rows, actions, states = _run_reference(seed)
        all_rows.extend(rows)
        replay.append(_verify_physical_replay(seed, actions, states))
    with (OUT / "path_records.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = sorted({key for row in all_rows for key in row})
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader(); writer.writerows(all_rows)
    summary = _summarize(all_rows)
    physics_invariant = all(r["max_blue_position_error"] == 0.0 and r["max_target_position_error"] == 0.0 and r["same_terminal_outcome"] and r["same_horizon"] for r in replay)
    relay_path_exists = bool(summary["provenance_erasure_changes_legal_information"])
    payload = {
        "protocol": PROTOCOL, "performance_use_prohibited": True, "episode_seeds": list(SEEDS),
        "frozen_l4_conditions": {"communication_range_scale": 0.5, "communication_dropout_prob": 0.3, "message_delay_steps": 8},
        "summary": summary, "fixed_action_physical_replay": replay,
        "physical_dynamics_invariant_when_relay_communication_disabled": physics_invariant,
        "verdict": "RELAY_PATH_IDENTIFIED__TASK_PROTOCOL_CHANGE_REQUIRES_SEPARATE_AUTHORIZATION" if relay_path_exists else "L5_BLOCKED__RELAY_CAUSAL_ROLE_NOT_IDENTIFIED",
        "interpretation": "No L5 training is authorized by this audit. A relay failure is identifiable only when erasing legal Relay-origin evidence changes at least one recipient information set.",
    }
    (OUT / "COMMUNICATION_PATH_IDENTIFIABILITY_AUDIT.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
