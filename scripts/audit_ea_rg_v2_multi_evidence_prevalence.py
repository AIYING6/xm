"""Read-only EA-RG v2 R0 multi-evidence prevalence and schema audit.

This is not an EA-RG implementation and does not train a policy.  It replays
the two frozen strict-contract L4 MAPPO checkpoints and asks whether the
current task actually presents the proposed method with multiple, legal target
evidence replicas before attack-range acquisition.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from envs.uav_intercept_3d_env import ROLE_ATTACKER, ROLE_INTERCEPTOR
from scripts import run_l4_corrected_contract_requalification as l4r
from scripts import run_new_project_l0_single_interceptor as l0


OUT = ROOT / "results" / "ea_rg_v2_r0_multi_evidence_prevalence_v3"
CHECKPOINT_ROOT = ROOT / "results" / "l4_corrected_contract_requalification"
TRAIN_SEEDS = (8901, 8902)
EPISODE_SEEDS = tuple(range(890_000, 890_032))
PROTOCOL = "EA_RG_V2_R0_MULTI_EVIDENCE_PREVALENCE_AUDIT_V1"

# Frozen before inspecting this audit's output.  Twenty percent is deliberately
# conservative: a relation-specific main mechanism needs to occur in a
# material fraction of the pre-acquisition decision process, not in a handful
# of unusual states.
MIN_STATE_PREVALENCE = 0.20
MIN_EPISODE_PREVALENCE = 0.20
CONFIDENCE_DIFFERENCE = 0.05


def _fresh_packet(env, packet: dict[str, object] | None) -> bool:
    if packet is None or float(packet.get("validity", 0.0)) <= 0.5:
        return False
    generation = int(packet.get("target_generation_step", -1))
    return (
        generation >= 0
        and float(packet.get("target_confidence", 0.0)) >= float(env.config.min_target_confidence)
        and env.step_count - generation <= int(env.config.max_target_message_age_steps)
    )


def _replicas(env, recipient: int) -> list[dict[str, object]]:
    """Return all target claims legally visible now, without changing env state.

    The local cache is one selected cache entry.  Sender status packets are
    independent delivered copies.  Their missing origin/path fields are
    deliberately recorded as ``None`` rather than reconstructed from truth.
    """
    result: list[dict[str, object]] = []
    if env._has_fresh_target_cache(recipient):
        result.append(
            {
                "replica_kind": "selected_cache",
                "immediate_sender": int(recipient),
                "origin_source": int(env.target_cache_source[recipient]),
                "delivery_path": list(env.target_cache_path[recipient]),
                "age": int(env._local_target_cache_age(recipient)),
                "confidence": float(env.target_cache_confidence[recipient]),
            }
        )
    for sender, packet in sorted(env.sender_packet_cache[recipient].items()):
        if _fresh_packet(env, packet):
            result.append(
                {
                    "replica_kind": "sender_status_packet",
                    "immediate_sender": int(sender),
                    # Sender status packets contain target values, age and
                    # confidence, but the existing schema does not carry
                    # original target source or delivery path.
                    "origin_source": None,
                    "delivery_path": None,
                    "age": int(env.step_count - int(packet["target_generation_step"])),
                    "confidence": float(packet["target_confidence"]),
                }
            )
    return result


def _step_record(env, train_seed: int, episode_seed: int, attacker: int) -> dict[str, object]:
    copies = _replicas(env, attacker)
    ages = [int(copy["age"]) for copy in copies]
    confidences = [float(copy["confidence"]) for copy in copies]
    immediate_senders = {int(copy["immediate_sender"]) for copy in copies}
    return {
        "training_seed": train_seed,
        "episode_seed": episode_seed,
        "step": int(env.step_count),
        "legal_replica_count": len(copies),
        "multi_replica": int(len(copies) >= 2),
        "different_immediate_sender": int(len(immediate_senders) >= 2),
        "age_difference_at_least_one_step": int(len(ages) >= 2 and max(ages) - min(ages) >= 1),
        "confidence_difference_at_least_005": int(len(confidences) >= 2 and max(confidences) - min(confidences) >= CONFIDENCE_DIFFERENCE - 1e-8),
        "sender_status_packet_replica_count": sum(copy["replica_kind"] == "sender_status_packet" for copy in copies),
        "replicas": json.dumps(copies, sort_keys=True),
    }


def _replay(train_seed: int) -> tuple[list[dict[str, object]], str]:
    checkpoint = CHECKPOINT_ROOT / f"l4_corrected_contract_seed{train_seed}" / "actor_critic_latest.pt"
    if not checkpoint.exists():
        raise FileNotFoundError(checkpoint)
    checkpoint_hash = hashlib.sha256(checkpoint.read_bytes()).hexdigest()
    cfg = l4r.cfg(train_seed, OUT / "template", updates=1)
    agent = l0.load_agent(cfg, checkpoint)
    records: list[dict[str, object]] = []
    for episode_seed in EPISODE_SEEDS:
        env = l0.make_env(cfg, episode_seed, training=False)
        obs, share, graph = env.reset()
        attacker = next(i for i, typ in enumerate(env.config.blue_types) if typ.role in {ROLE_ATTACKER, ROLE_INTERCEPTOR})
        before_range = True
        while True:
            action = np.asarray(l0.agent_actions(agent, obs, share, graph), dtype=np.float32).reshape(env.num_agents, 3)
            for i, typ in enumerate(env.config.blue_types):
                if typ.role not in {ROLE_ATTACKER, ROLE_INTERCEPTOR}:
                    action[i, 2] = -1.0
            obs, share, graph, _reward, dones, _info = env.step(action)
            # Recording is evaluator-only.  It defines the pre-acquisition
            # window and is never returned to the actor.
            if before_range:
                records.append(_step_record(env, train_seed, episode_seed, attacker))
            before_range = before_range and not bool(
                np.linalg.norm(env.red_pos[0] - env.blue_pos[attacker]) <= env.config.blue_types[attacker].attack_range_max
            )
            if bool(np.all(dones)):
                break
    return records, checkpoint_hash


def _rate(rows: list[dict[str, object]], field: str) -> float:
    return float(np.mean([int(row[field]) for row in rows])) if rows else 0.0


def _summary(records: list[dict[str, object]]) -> dict[str, object]:
    by_seed = []
    for seed in TRAIN_SEEDS:
        rows = [row for row in records if int(row["training_seed"]) == seed]
        episodes = sorted({int(row["episode_seed"]) for row in rows})
        multi_episodes = {
            int(row["episode_seed"]) for row in rows if int(row["multi_replica"])
        }
        by_seed.append(
            {
                "training_seed": seed,
                "pre_acquisition_decision_states": len(rows),
                "multi_replica_state_rate": _rate(rows, "multi_replica"),
                "multi_replica_episode_rate": len(multi_episodes) / len(episodes) if episodes else 0.0,
                "different_immediate_sender_state_rate": _rate(rows, "different_immediate_sender"),
                "age_difference_state_rate": _rate(rows, "age_difference_at_least_one_step"),
                "confidence_difference_state_rate": _rate(rows, "confidence_difference_at_least_005"),
                "sender_status_packet_replica_states": int(sum(int(row["sender_status_packet_replica_count"]) > 0 for row in rows)),
            }
        )
    prevalence = all(
        row["multi_replica_state_rate"] >= MIN_STATE_PREVALENCE
        and row["multi_replica_episode_rate"] >= MIN_EPISODE_PREVALENCE
        for row in by_seed
    )
    return {
        "per_training_seed": by_seed,
        "pre_frozen_gate": {
            "minimum_multi_replica_state_rate": MIN_STATE_PREVALENCE,
            "minimum_multi_replica_episode_rate": MIN_EPISODE_PREVALENCE,
            "pass": prevalence,
        },
        # This is a static schema property, not a rate over observed rows.
        # A run with no sender packets must never turn a missing payload field
        # into a vacuous 100% schema pass.
        "current_packet_schema_supports_full_origin_and_delivery_path_per_replica": False,
    }


def self_test() -> None:
    class Config:
        min_target_confidence = 0.2
        max_target_message_age_steps = 4
    class Env:
        config = Config()
        step_count = 10
    env = Env()
    assert _fresh_packet(env, {"validity": 1.0, "target_generation_step": 6, "target_confidence": 0.2})
    assert not _fresh_packet(env, {"validity": 1.0, "target_generation_step": 5, "target_confidence": 1.0})
    assert not _fresh_packet(env, {"validity": 1.0, "target_generation_step": 6, "target_confidence": 0.19})
    print("EA_RG_V2_R0_MULTI_EVIDENCE_STATIC_TEST: PASS (3 tests)")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    if OUT.exists() and any(OUT.iterdir()):
        raise FileExistsError(f"refusing to overwrite R0 audit output: {OUT}")
    OUT.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, object]] = []
    hashes: dict[str, str] = {}
    for seed in TRAIN_SEEDS:
        run_records, checkpoint_hash = _replay(seed)
        records.extend(run_records)
        hashes[str(seed)] = checkpoint_hash
    with (OUT / "pre_acquisition_evidence_replica_records.csv").open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0])); writer.writeheader(); writer.writerows(records)
    summary = _summary(records)
    payload = {
        "protocol": PROTOCOL,
        "performance_use_prohibited": True,
        "frozen_checkpoint_hashes": hashes,
        "episode_seeds": list(EPISODE_SEEDS),
        "summary": summary,
        "schema_finding": "Sender-status target claims omit original target source and delivery path. Immediate sender is present, but full provenance/path is not recoverable from the legal packet itself.",
        "verdict": "R0_NO_GO__EA_RG_V2_ALGORITHM_LINE_CLOSED" if not summary["pre_frozen_gate"]["pass"] else "R0_PARTIAL__SCIENTIFIC_PROBLEM_VALID_BUT_MECHANISM_NOT_DISTINCT",
    }
    (OUT / "EA_RG_V2_R0_MULTI_EVIDENCE_MANIFEST.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
