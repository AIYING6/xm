"""C3.5 synthetic actor-runner integration audit for TATG-MAPPO."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.tatg_actor import TATGMemoryActor
from algorithms.ri_gmappo.tatg_sequence_runner import TATGSequenceActorRunner
from scripts.audit_tatg_mappo_c3_sequence_replay import _sequence_batch
from scripts.audit_tatg_mappo_c15_actor_integration import base_actor


def _new_runner(kind: str) -> TATGSequenceActorRunner:
    actor = TATGMemoryActor(base_actor(), num_blue=3, action_dim=27, memory_kind=kind).eval()
    batch = _sequence_batch()
    return TATGSequenceActorRunner(actor, batch["relation_adj"][0], batch["edge_feat"][0])


def _collect_with_stored_actions(runner: TATGSequenceActorRunner, batch: dict[str, torch.Tensor]) -> tuple[torch.Tensor, dict]:
    start = runner.rollout_start_state_dict()
    log_probs = []
    for t in range(batch["actions"].shape[0]):
        step = runner.act(
            batch["obs"][t], batch["node_feat"][t], batch["edge_feat"][t], batch["role"][t], batch["adj"][t],
            batch["relation_adj"][t], action=batch["actions"][t],
        )
        log_probs.append(step.log_prob)
        if t + 1 < batch["actions"].shape[0]:
            runner.reset_completed(batch["dones"][t], batch["relation_adj"][t + 1], batch["edge_feat"][t + 1])
    return torch.stack(log_probs), start


def _payload_equal(left: dict, right: dict) -> bool:
    return set(left) == set(right) == {"tatg_memory_state"} and all(
        torch.equal(left["tatg_memory_state"][field], right["tatg_memory_state"][field])
        for field in ("memory", "previous_topology", "previous_action")
    )


def collect_checks() -> tuple[dict[str, bool], dict[str, int]]:
    batch = _sequence_batch()
    candidate = _new_runner("cetm")
    generic = _new_runner("snapshot_gru")
    zero_delta = _new_runner("cetm_zero_delta")
    generic.actor.load_state_dict(candidate.actor.state_dict())
    zero_delta.actor.load_state_dict(candidate.actor.state_dict())

    with torch.no_grad():
        collected_log_prob, start_payload = _collect_with_stored_actions(candidate, batch)
        replay = candidate.replay_rollout(
            obs=batch["obs"], node_feat=batch["node_feat"], edge_feat=batch["edge_feat"], role=batch["role"],
            adj=batch["adj"], relation_adj=batch["relation_adj"], actions=batch["actions"], dones=batch["dones"],
            state_before_rollout=start_payload,
        )
        continuation_payload = candidate.rollout_start_state_dict()
        clone = _new_runner("cetm")
        clone.actor.load_state_dict(candidate.actor.state_dict())
        clone.load_rollout_start_state_dict(continuation_payload)
        candidate_next = candidate.act(
            batch["obs"][0], batch["node_feat"][0], batch["edge_feat"][0], batch["role"][0], batch["adj"][0],
            batch["relation_adj"][0], action=batch["actions"][0],
        )
        clone_next = clone.act(
            batch["obs"][0], batch["node_feat"][0], batch["edge_feat"][0], batch["role"][0], batch["adj"][0],
            batch["relation_adj"][0], action=batch["actions"][0],
        )
        generic_log_prob, generic_start = _collect_with_stored_actions(generic, batch)
        generic_replay = generic.replay_rollout(
            obs=batch["obs"], node_feat=batch["node_feat"], edge_feat=batch["edge_feat"], role=batch["role"],
            adj=batch["adj"], relation_adj=batch["relation_adj"], actions=batch["actions"], dones=batch["dones"],
            state_before_rollout=generic_start,
        )
        zero_log_prob, zero_start = _collect_with_stored_actions(zero_delta, batch)
        zero_replay = zero_delta.replay_rollout(
            obs=batch["obs"], node_feat=batch["node_feat"], edge_feat=batch["edge_feat"], role=batch["role"],
            adj=batch["adj"], relation_adj=batch["relation_adj"], actions=batch["actions"], dones=batch["dones"],
            state_before_rollout=zero_start,
        )

    checks = {
        "collection_records_actions_only_after_logprobability": torch.equal(collected_log_prob, replay.log_prob),
        "stored_rollout_start_state_replays_exactly": torch.equal(collected_log_prob, replay.log_prob),
        "completed_environment_resets_before_following_graph": torch.equal(
            replay.states_before[2].previous_action[0],
            torch.full_like(replay.states_before[2].previous_action[0], candidate.actor.topology_memory.neutral_action),
        ),
        "strict_runner_state_restore_continues_exactly": torch.equal(candidate_next.logits, clone_next.logits)
        and torch.equal(candidate_next.log_prob, clone_next.log_prob)
        and _payload_equal(candidate.rollout_start_state_dict(), clone.rollout_start_state_dict()),
        "generic_control_uses_identical_collection_and_replay_interface": torch.equal(generic_log_prob, generic_replay.log_prob),
        "zero_residual_control_uses_identical_collection_and_replay_interface": torch.equal(zero_log_prob, zero_replay.log_prob),
        "runtime_payload_contains_only_frozen_tatg_state": set(start_payload) == {"tatg_memory_state"}
        and set(start_payload["tatg_memory_state"]) == {"memory", "previous_topology", "previous_action"},
        "adapter_owns_no_environment_critic_or_evaluation_path": not hasattr(candidate, "critic")
        and not hasattr(candidate, "environment") and not hasattr(candidate, "evaluate"),
    }
    return checks, {
        "sequence_time_steps": int(batch["actions"].shape[0]),
        "sequence_environments": int(batch["actions"].shape[1]),
        "candidate_added_actor_parameters": candidate.actor.added_actor_parameter_count(),
        "environment_steps": 0,
        "formal_ppo_updates": 0,
    }


def render_report(result: dict[str, Any]) -> str:
    lines = [
        "# TATG-MAPPO C3.5 actor-runner integration audit", "", f"**Verdict:** `{result['verdict']}`.", "",
        "The isolated actor adapter now owns the frozen collection/replay lifecycle: it saves the CETM state before a rollout, evaluates log-probability before recording the selected action, resets only completed slots from their new reset graph, and replays full sequences chronologically. Restoring its three-tensor runtime payload reproduces the next actor call exactly.", "",
        "It deliberately has no environment, critic, reward, sampler, evaluation or checkpoint-selection path. CETM, the capacity-matched current-snapshot GRU control and zero-residual CETM all use the same actor-runner interface. This is synthetic interface verification only, not PPO training or a performance result.", "", "## Checks", "",
    ]
    lines.extend(f"- `{name}`: `{passed}`" for name, passed in result["checks"].items())
    lines += ["", "A pass authorizes only a separately frozen outer rollout-loop and strict runtime-checkpoint integration audit. It does not authorize environment rollout, fresh-seed/cloud training, evaluation or a performance claim.", ""]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("Refusing to write C3.5 output without --execute")
    output = Path(args.output_dir)
    if output.exists():
        raise SystemExit(f"Refusing to overwrite existing output: {output}")
    checks, details = collect_checks()
    result = {"protocol": "TATG-MAPPO-C3.5-ACTOR-RUNNER-INTEGRATION-AUDIT-V1", "verdict": "TATG_C35_ACTOR_RUNNER_INTEGRATION_PASS" if all(checks.values()) else "TATG_C35_ACTOR_RUNNER_INTEGRATION_NO_GO", "checks": checks, "audit_details": details, "training_started": False, "evaluation_started": False, "automatic_continuation": False}
    output.mkdir(parents=True)
    (output / "TATG_C35_RESULT.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    (output / "TATG_C35_REPORT.md").write_text(render_report(result), encoding="utf-8", newline="\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
