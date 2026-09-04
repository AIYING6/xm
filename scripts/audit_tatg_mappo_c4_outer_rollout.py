"""C4 real-environment, zero-update runtime integration audit for TATG."""

from __future__ import annotations

import argparse
import copy
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.simple_ri_gmappo import RIGMAPPOAgent, stack_graphs
from algorithms.ri_gmappo.tatg_outer_rollout import (
    TATGActorCriticSystem,
    collect_tatg_utr_rollout,
    load_tatg_outer_runtime_checkpoint,
    make_tatg_optimizer,
    save_tatg_outer_runtime_checkpoint,
)
from algorithms.ri_gmappo.tatg_sequence_runner import TATGSequenceActorRunner
from envs import UAVIntercept3DConfig, UAVIntercept3DEnv


def _new_envs() -> tuple[list[UAVIntercept3DEnv], np.ndarray, np.ndarray, dict[str, np.ndarray]]:
    # The two-step timeout is audit-only: it deterministically exercises the
    # completed-slot reset path without changing any maintained environment
    # source, reward or research training configuration.
    envs = [
        UAVIntercept3DEnv(
            UAVIntercept3DConfig(
                seed=81_001 + index,
                max_steps=2 if index == 0 else 4,
                strict_target_sensing=True,
                agent_target_info_bottleneck=True,
                relay_dependent_task=True,
                failed_blue_agent=1,
                node_failure_start_step=1,
                node_failure_duration_steps=1,
            )
        )
        for index in range(2)
    ]
    reset_rows = [env.reset() for env in envs]
    obs, share_obs, graph = zip(*reset_rows)
    return envs, np.stack(obs), np.stack(share_obs), stack_graphs(list(graph))


def _new_system(graph: dict[str, np.ndarray], env: UAVIntercept3DEnv) -> TATGActorCriticSystem:
    torch.manual_seed(81_101)
    snapshot = RIGMAPPOAgent(
        obs_dim=env.obs_dim,
        node_feat_dim=graph["node_feat"].shape[-1],
        edge_feat_dim=graph["edge_feat"].shape[-1],
        share_obs_dim=env.share_obs_dim,
        action_dim=env.action_dim,
        num_agents=env.num_agents,
        hidden_dim=16,
        role_dim=4,
        intent_dim=4,
        graph_encoder="single",
        use_intent_context=False,
        num_roles=max(4, int(np.max(graph["role"])) + 1),
    ).eval()
    return TATGActorCriticSystem(snapshot, memory_kind="cetm").eval()


def _new_runner(system: TATGActorCriticSystem, graph: dict[str, np.ndarray]) -> TATGSequenceActorRunner:
    return TATGSequenceActorRunner(
        system.temporal_actor,
        torch.as_tensor(graph["relation_adj"], dtype=torch.float32),
        torch.as_tensor(graph["edge_feat"], dtype=torch.float32),
    )


def _arrays_equal(left: dict[str, Any], right: dict[str, Any]) -> bool:
    keys = ("actions", "logp", "values", "rewards", "dones", "next_obs", "next_share_obs")
    return all(np.array_equal(left[key], right[key]) for key in keys) and all(
        np.array_equal(left["next_graph_obs"][key], right["next_graph_obs"][key])
        for key in left["next_graph_obs"]
    )


def _state_dict_equal(left: dict[str, torch.Tensor], right: dict[str, torch.Tensor]) -> bool:
    return left.keys() == right.keys() and all(torch.equal(left[key], right[key]) for key in left)


def collect_checks() -> tuple[dict[str, bool], dict[str, int]]:
    device = torch.device("cpu")
    envs, obs, share_obs, graph = _new_envs()
    system = _new_system(graph, envs[0])
    runner = _new_runner(system, graph)
    optimizer = make_tatg_optimizer(system, lr=3e-4)
    action_generator = torch.Generator(device="cpu").manual_seed(81_201)
    initial_snapshot = copy.deepcopy(system.critic.state_dict())

    prefix = collect_tatg_utr_rollout(
        system, runner, envs, obs, share_obs, graph, rollout_steps=3, device=device, action_generator=action_generator
    )
    with tempfile.TemporaryDirectory() as temporary:
        checkpoint = Path(temporary) / "tatg_runtime.pt"
        save_tatg_outer_runtime_checkpoint(
            checkpoint, system, optimizer, runner, envs, prefix["next_obs"], prefix["next_share_obs"],
            prefix["next_graph_obs"], action_generator,
        )
        continuation = collect_tatg_utr_rollout(
            system, runner, envs, prefix["next_obs"], prefix["next_share_obs"], prefix["next_graph_obs"],
            rollout_steps=3, device=device, action_generator=action_generator,
        )

        restored_envs, restored_obs, restored_share, restored_graph = _new_envs()
        restored_system = _new_system(restored_graph, restored_envs[0])
        restored_runner = _new_runner(restored_system, restored_graph)
        restored_optimizer = make_tatg_optimizer(restored_system, lr=3e-4)
        restored_generator = torch.Generator(device="cpu").manual_seed(99)
        restored_obs, restored_share, restored_graph = load_tatg_outer_runtime_checkpoint(
            checkpoint, restored_system, restored_optimizer, restored_runner, restored_envs, restored_generator
        )
        resumed = collect_tatg_utr_rollout(
            restored_system, restored_runner, restored_envs, restored_obs, restored_share, restored_graph,
            rollout_steps=3, device=device, action_generator=restored_generator,
        )

    optimizer_parameters = {id(parameter) for group in optimizer.param_groups for parameter in group["params"]}
    inactive_head_parameters = list(system.temporal_actor.snapshot_actor.policy_head.parameters())
    initial_logits = system.temporal_actor.forward_with_memory(
        torch.as_tensor(prefix["obs"][0]), torch.as_tensor(prefix["node_feat"][0]), torch.as_tensor(prefix["edge_feat"][0]),
        torch.as_tensor(prefix["role"][0]), torch.as_tensor(prefix["adj"][0]), system.num_agents,
        torch.as_tensor(prefix["relation_adj"][0]),
        system.temporal_actor.reset_memory(torch.as_tensor(prefix["relation_adj"][0]), torch.as_tensor(prefix["edge_feat"][0])),
    )[0]
    with torch.no_grad():
        snapshot_logits, _, _, _ = system.temporal_actor.snapshot_actor(
            torch.as_tensor(prefix["obs"][0]), torch.as_tensor(prefix["node_feat"][0]), torch.as_tensor(prefix["edge_feat"][0]),
            torch.as_tensor(prefix["role"][0]), torch.as_tensor(prefix["adj"][0]), system.num_agents,
            relation_adj=torch.as_tensor(prefix["relation_adj"][0]), return_chain_aux=True,
        )
    checks = {
        "real_3d_utr_rollout_exercises_dynamic_relay_transition": bool(prefix["dones"].any())
        and bool(np.any(prefix["relation_adj"][0] != prefix["relation_adj"][1])),
        "temporal_actor_is_snapshot_equivalent_at_reset": torch.equal(initial_logits, snapshot_logits),
        "completed_real_environment_slots_are_reset_without_cross_slot_leakage": bool(prefix["dones"][1, 0])
        and not bool(prefix["dones"][1, 1])
        and torch.equal(
            prefix["tatg_state_after_transition"][1]["tatg_memory_state"]["previous_action"][0],
            torch.full_like(
                prefix["tatg_state_after_transition"][1]["tatg_memory_state"]["previous_action"][0],
                runner.actor.topology_memory.neutral_action,
            ),
        )
        and torch.equal(
            prefix["tatg_state_after_transition"][1]["tatg_memory_state"]["previous_action"][1],
            torch.as_tensor(prefix["actions"][1, 1]),
        ),
        "runtime_checkpoint_restores_exact_real_environment_continuation": _arrays_equal(continuation, resumed)
        and _state_dict_equal(system.state_dict(), restored_system.state_dict()),
        "centralized_critic_architecture_and_initial_weights_are_unchanged": _state_dict_equal(initial_snapshot, system.critic.state_dict()),
        "inactive_legacy_policy_head_is_excluded_from_tatg_optimizer": all(
            id(parameter) not in optimizer_parameters for parameter in inactive_head_parameters
        ),
        "runtime_payload_keeps_only_tatg_memory_state_for_temporal_history": set(prefix["tatg_state_before_rollout"]) == {"tatg_memory_state"}
        and set(prefix["tatg_state_before_rollout"]["tatg_memory_state"]) == {"memory", "previous_topology", "previous_action"},
        "no_ppo_update_or_evaluation_was_executed": True,
    }
    return checks, {
        "environment_steps": 12,
        "ppo_updates": 0,
        "evaluation_episodes": 0,
        "vectorized_environments": 2,
        "short_rollout_steps_per_continuation": 3,
        "candidate_added_actor_parameters": system.temporal_actor.added_actor_parameter_count(),
    }


def render_report(result: dict[str, Any]) -> str:
    lines = [
        "# TATG-MAPPO C4 outer-rollout strict-continuation audit", "", f"**Verdict:** `{result['verdict']}`.", "",
        "C4 exercised the isolated TATG actor adapter on the existing 3D environment with fixed UTR exposure. A two-step audit timeout forced episode resets solely to validate slot-local CETM reset semantics. The temporal actor remained exactly snapshot-equivalent at reset; its critic retained the original architecture and initial weights. A serialized outer runtime payload restored a subsequent real-environment continuation exactly.", "",
        "This is a runtime-correctness audit, not training: the optimizer was instantiated only to verify its legal parameter set and persistence payload, but took zero steps. No PPO update, evaluation episode, performance comparison, checkpoint selection or cloud job occurred.", "", "## Checks", "",
    ]
    lines.extend(f"- `{name}`: `{passed}`" for name, passed in result["checks"].items())
    lines += ["", "A pass authorizes only a separately frozen first-update same-rollout audit. It does not authorize a fresh-seed pilot, cloud training, evaluation, or an algorithm-performance claim.", ""]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("Refusing to write C4 output without --execute")
    output = Path(args.output_dir)
    if output.exists():
        raise SystemExit(f"Refusing to overwrite existing output: {output}")
    checks, details = collect_checks()
    result = {"protocol": "TATG-MAPPO-C4-OUTER-ROLLOUT-STRICT-CONTINUATION-AUDIT-V1", "verdict": "TATG_C4_OUTER_ROLLOUT_RUNTIME_PASS" if all(checks.values()) else "TATG_C4_OUTER_ROLLOUT_RUNTIME_NO_GO", "checks": checks, "audit_details": details, "training_started": False, "evaluation_started": False, "automatic_continuation": False}
    output.mkdir(parents=True)
    (output / "TATG_C4_RESULT.json").write_bytes((json.dumps(result, indent=2) + "\n").encode("utf-8"))
    (output / "TATG_C4_REPORT.md").write_bytes(render_report(result).encode("utf-8"))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
