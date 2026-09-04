"""C3 same-rollout correctness audit for chronological TATG actor replay."""

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
from algorithms.ri_gmappo.tatg_sequence_ppo import clipped_actor_objective, replay_tatg_actor_sequence
from scripts.audit_tatg_mappo_c15_actor_integration import base_actor, synthetic_actor_inputs
from envs import RELATION_COMMUNICATION, RELATION_TASK_SUPPORT


def _sequence_batch() -> dict[str, torch.Tensor]:
    base = synthetic_actor_inputs(batch=2)
    torch.manual_seed(107)
    rows: dict[str, list[torch.Tensor]] = {key: [] for key, value in base.items() if isinstance(value, torch.Tensor)}
    for t in range(4):
        for key, value in base.items():
            if not isinstance(value, torch.Tensor):
                continue
            row = value.clone()
            if key == "relation_adj" and t in {1, 3}:
                row[0, RELATION_COMMUNICATION, 0, 1] = 1.0
                row[0, RELATION_TASK_SUPPORT, 0, 1] = 1.0
            if key == "edge_feat" and t in {1, 3}:
                row[0, 0, 1, 15] = float(t)
            rows[key].append(row)
    result = {key: torch.stack(value) for key, value in rows.items()}
    result["actions"] = torch.tensor(
        [
            [[1, 2, 3], [4, 5, 6]],
            [[2, 3, 4], [5, 6, 7]],
            [[3, 4, 5], [6, 7, 8]],
            [[4, 5, 6], [7, 8, 9]],
        ],
        dtype=torch.long,
    )
    # Slot 0 completes after t=1; row t=2 is therefore its fresh-reset graph.
    result["dones"] = torch.tensor([[False, False], [True, False], [False, False], [False, False]])
    return result


def _replay(actor: TATGMemoryActor, batch: dict[str, torch.Tensor], state):
    return replay_tatg_actor_sequence(
        actor,
        obs=batch["obs"], node_feat=batch["node_feat"], edge_feat=batch["edge_feat"], role=batch["role"], adj=batch["adj"],
        relation_adj=batch["relation_adj"], actions=batch["actions"], dones=batch["dones"], state_before_rollout=state,
    )


def collect_checks() -> tuple[dict[str, bool], dict[str, float | int]]:
    batch = _sequence_batch()
    candidate = TATGMemoryActor(base_actor(), num_blue=3, action_dim=27, memory_kind="cetm").train()
    generic = TATGMemoryActor(base_actor(), num_blue=3, action_dim=27, memory_kind="snapshot_gru").train()
    zero_delta = TATGMemoryActor(base_actor(), num_blue=3, action_dim=27, memory_kind="cetm_zero_delta").train()
    generic.load_state_dict(candidate.state_dict())
    zero_delta.load_state_dict(candidate.state_dict())
    state = candidate.reset_memory(batch["relation_adj"][0], batch["edge_feat"][0])
    with torch.no_grad():
        collected = _replay(candidate, batch, state)
        replayed = _replay(candidate, batch, state)
    old_log_prob = collected.log_prob.detach().clone()
    advantages = torch.tensor(
        [[[0.5, -0.2, 0.1], [0.3, -0.4, 0.2]]] * 4,
        dtype=torch.float32,
    )
    candidate.zero_grad(set_to_none=True)
    fresh = _replay(candidate, batch, state)
    loss = clipped_actor_objective(fresh, old_log_prob, advantages, clip_coef=0.2, entropy_coef=0.01)
    loss.backward()
    temporal_head_grad = candidate.temporal_policy_head[0].weight.grad
    temporal_head_grad_nonzero = temporal_head_grad is not None and bool(torch.isfinite(temporal_head_grad).all()) and bool(
        temporal_head_grad.abs().sum() > 0
    )

    # A deterministic synthetic optimizer step makes the initially zero memory
    # columns active. The second gradient probe then verifies the GRUCell is on
    # the PPO graph; this is not environment training or checkpoint selection.
    optimizer = torch.optim.SGD(candidate.parameters(), lr=0.01)
    optimizer.step()
    candidate.zero_grad(set_to_none=True)
    second = _replay(candidate, batch, state)
    second_loss = clipped_actor_objective(second, old_log_prob, advantages, clip_coef=0.2, entropy_coef=0.01)
    second_loss.backward()
    memory_grad = candidate.topology_memory.cell.weight_ih.grad
    memory_grad_nonzero = memory_grad is not None and bool(torch.isfinite(memory_grad).all()) and bool(
        memory_grad.abs().sum() > 0
    )
    with torch.no_grad():
        generic_replay = _replay(generic, batch, generic.reset_memory(batch["relation_adj"][0], batch["edge_feat"][0]))
        zero_replay = _replay(zero_delta, batch, zero_delta.reset_memory(batch["relation_adj"][0], batch["edge_feat"][0]))
    checks = {
        "chronological_replay_reproduces_collected_log_probs_exactly": torch.equal(collected.log_prob, replayed.log_prob),
        "episode_completion_resets_only_the_completed_sequence_slot": bool(
            torch.equal(replayed.states_before[2].memory[0], torch.zeros_like(replayed.states_before[2].memory[0]))
            and torch.equal(
                replayed.states_before[2].previous_action[0],
                torch.full_like(replayed.states_before[2].previous_action[0], candidate.topology_memory.neutral_action),
            )
            and torch.equal(
                replayed.states_before[2].previous_topology[0],
                candidate.reset_memory(batch["relation_adj"][2], batch["edge_feat"][2]).previous_topology[0],
            )
            and torch.equal(replayed.states_before[2].previous_action[1], batch["actions"][1, 1])
        ),
        "ordinary_clipped_ppo_actor_loss_is_finite": bool(torch.isfinite(loss) and torch.isfinite(second_loss)),
        "temporal_head_receives_first_same_rollout_gradient": temporal_head_grad_nonzero,
        "cetm_grucell_receives_gradient_after_memory_columns_activate": memory_grad_nonzero,
        "generic_and_zero_delta_controls_share_the_same_sequence_replay": generic_replay.log_prob.shape == collected.log_prob.shape
        and zero_replay.log_prob.shape == collected.log_prob.shape,
        "generic_and_zero_delta_controls_have_exact_candidate_added_capacity": candidate.added_actor_parameter_count()
        == generic.added_actor_parameter_count() == zero_delta.added_actor_parameter_count(),
        "no_environment_or_evaluation_execution": True,
    }
    return checks, {
        "synthetic_actor_optimizer_steps": 1,
        "candidate_added_actor_parameters": candidate.added_actor_parameter_count(),
        "sequence_time_steps": int(batch["actions"].shape[0]),
        "sequence_environments": int(batch["actions"].shape[1]),
    }


def render_report(result: dict[str, Any]) -> str:
    lines = [
        "# TATG-MAPPO C3 chronological same-rollout PPO audit",
        "",
        f"**Verdict:** `{result['verdict']}`.",
        "",
        "C3 replays a synthetic rollout chronologically from its stored initial CETM state. The replay exactly reproduces the collected log-probabilities before any synthetic update. The ordinary clipped PPO actor loss is finite; its first synthetic gradient reaches the added temporal head and, after that head's initially zero memory columns are activated by one deterministic synthetic optimizer step, reaches the CETM GRUCell as well.",
        "",
        "This is a local correctness test, not performance training: it creates no environment, uses no evaluation tape, stores no selected checkpoint and compares no return. Candidate CETM, generic current-snapshot GRU and zero-residual CETM share the same sequence replay and added capacity.",
        "",
        "## Checks",
        "",
    ]
    lines.extend(f"- `{name}`: `{passed}`" for name, passed in result["checks"].items())
    lines += [
        "",
        "A pass authorizes only a separately frozen rollout-runner integration and exact continuation audit. It does not authorize fresh-seed, cloud, evaluation or performance training.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("Refusing to write C3 output without --execute")
    output = Path(args.output_dir)
    if output.exists():
        raise SystemExit(f"Refusing to overwrite existing output: {output}")
    checks, details = collect_checks()
    result = {
        "protocol": "TATG-MAPPO-C3-CHRONOLOGICAL-SAME-ROLLOUT-PPO-AUDIT-V1",
        "verdict": "TATG_C3_SEQUENCE_PPO_CORRECTNESS_PASS" if all(checks.values()) else "TATG_C3_SEQUENCE_PPO_CORRECTNESS_NO_GO",
        "checks": checks,
        "audit_details": details,
        "environment_steps": 0,
        "formal_ppo_updates": 0,
        "training_started": False,
        "evaluation_started": False,
        "automatic_continuation": False,
    }
    output.mkdir(parents=True)
    (output / "TATG_C3_RESULT.json").write_bytes((json.dumps(result, indent=2) + "\n").encode("utf-8"))
    (output / "TATG_C3_REPORT.md").write_bytes(render_report(result).encode("utf-8"))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
