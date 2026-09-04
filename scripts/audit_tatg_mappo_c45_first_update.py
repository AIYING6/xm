"""C4.5 first-update same-rollout audit for the isolated TATG actor path.

This is deliberately smaller than a PPO training run.  It collects one real,
fixed-UTR rollout, then performs exactly one *actor-only* clipped-PPO update
for CETM and each frozen capacity-matched control.  The critic, environment,
reward, sampler and every evaluation interface remain outside the audit.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.optim as optim

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.tatg_outer_rollout import TATGActorCriticSystem, collect_tatg_utr_rollout
from algorithms.ri_gmappo.tatg_sequence_ppo import clipped_actor_objective
from algorithms.ri_gmappo.tatg_sequence_runner import TATGSequenceActorRunner
from scripts.audit_tatg_mappo_c4_outer_rollout import _new_envs, _new_system


MEMORY_KINDS = {
    "cetm_candidate": "cetm",
    "capacity_matched_snapshot_gru_control": "snapshot_gru",
    "zero_residual_cetm_control": "cetm_zero_delta",
}


def _new_runner(system: TATGActorCriticSystem, graph: dict[str, np.ndarray]) -> TATGSequenceActorRunner:
    return TATGSequenceActorRunner(
        system.temporal_actor,
        torch.as_tensor(graph["relation_adj"], dtype=torch.float32),
        torch.as_tensor(graph["edge_feat"], dtype=torch.float32),
    )


def _actor_parameters(system: TATGActorCriticSystem) -> list[torch.nn.Parameter]:
    """The C4.5 step is actor-only; C4 already froze critic architecture."""

    return [
        parameter
        for name, parameter in system.temporal_actor.named_parameters()
        if not name.startswith("snapshot_actor.policy_head.")
    ]


def _replay(
    runner: TATGSequenceActorRunner, batch: dict[str, Any], device: torch.device
):
    return runner.replay_rollout(
        obs=torch.as_tensor(batch["obs"], dtype=torch.float32, device=device),
        node_feat=torch.as_tensor(batch["node_feat"], dtype=torch.float32, device=device),
        edge_feat=torch.as_tensor(batch["edge_feat"], dtype=torch.float32, device=device),
        role=torch.as_tensor(batch["role"], dtype=torch.long, device=device),
        adj=torch.as_tensor(batch["adj"], dtype=torch.float32, device=device),
        relation_adj=torch.as_tensor(batch["relation_adj"], dtype=torch.float32, device=device),
        actions=torch.as_tensor(batch["actions"], dtype=torch.long, device=device),
        dones=torch.as_tensor(batch["dones"], dtype=torch.bool, device=device),
        state_before_rollout=batch["tatg_state_before_rollout"],
    )


def _normalized_advantages(batch: dict[str, Any], system: TATGActorCriticSystem, device: torch.device) -> torch.Tensor:
    """Build one fixed ordinary-GAE actor target from unchanged critic values."""

    with torch.no_grad():
        next_values = system.critic_value(
            torch.as_tensor(batch["next_share_obs"], dtype=torch.float32, device=device),
            torch.as_tensor(batch["next_graph_obs"]["role"], dtype=torch.long, device=device),
        ).cpu().numpy()
    rewards = np.asarray(batch["rewards"], dtype=np.float32)
    values = np.asarray(batch["values"], dtype=np.float32)
    dones = np.asarray(batch["dones"], dtype=np.float32)[..., None]
    advantages = np.zeros_like(rewards, dtype=np.float32)
    running = np.zeros_like(next_values, dtype=np.float32)
    for step in reversed(range(rewards.shape[0])):
        continuation = 1.0 - dones[step]
        next_value = next_values if step == rewards.shape[0] - 1 else values[step + 1]
        delta = rewards[step] + 0.99 * next_value * continuation - values[step]
        running = delta + 0.99 * 0.95 * continuation * running
        advantages[step] = running
    tensor = torch.as_tensor(advantages, dtype=torch.float32, device=device)
    return (tensor - tensor.mean()) / tensor.std(unbiased=False).clamp_min(1e-6)


def _state_dict_equal(left: dict[str, torch.Tensor], right: dict[str, torch.Tensor]) -> bool:
    return left.keys() == right.keys() and all(torch.equal(left[key], right[key]) for key in left)


def _one_actor_step(
    system: TATGActorCriticSystem,
    runner: TATGSequenceActorRunner,
    batch: dict[str, Any],
    advantages: torch.Tensor,
    device: torch.device,
) -> dict[str, Any]:
    """Replay one full sequence and take exactly one legal actor optimizer step."""

    parameters = _actor_parameters(system)
    optimizer = optim.Adam(parameters, lr=3e-4)
    parameter_ids = {id(parameter) for group in optimizer.param_groups for parameter in group["params"]}
    inactive_before = copy.deepcopy(system.temporal_actor.snapshot_actor.policy_head.state_dict())
    active_before = copy.deepcopy(system.temporal_actor.temporal_policy_head.state_dict())
    critic_before = copy.deepcopy(system.critic.state_dict())

    replay = _replay(runner, batch, device)
    old_log_prob = replay.log_prob.detach().clone()
    loss = clipped_actor_objective(replay, old_log_prob, advantages, clip_coef=0.2, entropy_coef=0.01)
    optimizer.zero_grad(set_to_none=True)
    loss.backward()
    finite_gradients = all(
        parameter.grad is None or bool(torch.isfinite(parameter.grad).all()) for parameter in parameters
    )
    active_gradient = any(
        parameter.grad is not None and bool(parameter.grad.detach().abs().sum() > 0)
        for parameter in system.temporal_actor.temporal_policy_head.parameters()
    )
    optimizer.step()
    post_replay = _replay(runner, batch, device)
    inactive_parameters = list(system.temporal_actor.snapshot_actor.policy_head.parameters())
    return {
        "loss": float(loss.detach().cpu()),
        "preupdate_log_prob": old_log_prob.detach(),
        "postupdate_log_prob": post_replay.log_prob.detach(),
        "finite_loss": bool(torch.isfinite(loss)),
        "finite_gradients": finite_gradients,
        "active_temporal_head_has_gradient": active_gradient,
        "active_temporal_head_changed": not _state_dict_equal(
            active_before, system.temporal_actor.temporal_policy_head.state_dict()
        ),
        "critic_unchanged": _state_dict_equal(critic_before, system.critic.state_dict()),
        "inactive_head_unchanged": _state_dict_equal(
            inactive_before, system.temporal_actor.snapshot_actor.policy_head.state_dict()
        ),
        "inactive_head_excluded": all(id(parameter) not in parameter_ids for parameter in inactive_parameters),
        "postupdate_log_prob_finite": bool(torch.isfinite(post_replay.log_prob).all()),
    }


def collect_checks() -> tuple[dict[str, bool], dict[str, Any]]:
    device = torch.device("cpu")
    envs, obs, share_obs, graph = _new_envs()
    candidate = _new_system(graph, envs[0])
    candidate_runner = _new_runner(candidate, graph)
    generator = torch.Generator(device="cpu").manual_seed(81_301)
    batch = collect_tatg_utr_rollout(
        candidate,
        candidate_runner,
        envs,
        obs,
        share_obs,
        graph,
        rollout_steps=3,
        device=device,
        action_generator=generator,
    )
    advantages = _normalized_advantages(batch, candidate, device)
    outcomes: dict[str, dict[str, Any]] = {}
    candidate_preupdate_exact = False
    for label, memory_kind in MEMORY_KINDS.items():
        # Controls rebuild the same deterministic snapshot and alter only the
        # frozen memory class; no trained state or outcome is reused.
        system = candidate if label == "cetm_candidate" else _new_system(graph, envs[0], memory_kind=memory_kind)
        runner = candidate_runner if label == "cetm_candidate" else _new_runner(system, graph)
        outcome = _one_actor_step(system, runner, batch, advantages, device)
        outcomes[label] = outcome
        if label == "cetm_candidate":
            candidate_preupdate_exact = torch.equal(
                outcome["preupdate_log_prob"], torch.as_tensor(batch["logp"], dtype=torch.float32)
            )
    checks = {
        "candidate_preupdate_logprob_replays_exactly": candidate_preupdate_exact,
        "all_three_variants_have_finite_sequence_actor_losses_and_gradients": all(
            item["finite_loss"] and item["finite_gradients"] and item["active_temporal_head_has_gradient"]
            for item in outcomes.values()
        ),
        "each_variant_changes_an_active_temporal_actor_parameter": all(
            item["active_temporal_head_changed"] for item in outcomes.values()
        ),
        "candidate_critic_is_bitwise_unchanged": outcomes["cetm_candidate"]["critic_unchanged"],
        "inactive_copied_legacy_policy_head_is_excluded_and_unchanged": all(
            item["inactive_head_excluded"] and item["inactive_head_unchanged"] for item in outcomes.values()
        ),
        "postupdate_candidate_sequence_logprob_is_finite": outcomes["cetm_candidate"]["postupdate_log_prob_finite"],
        "no_evaluation_or_outcome_comparison": True,
    }
    details = {
        "environment_steps": int(3 * len(envs)),
        "audit_actor_optimizer_steps": len(MEMORY_KINDS),
        "formal_ppo_updates": 0,
        "evaluation_episodes": 0,
        "vectorized_environments": len(envs),
        "rollout_steps": 3,
        "variant_actor_losses": {name: item["loss"] for name, item in outcomes.items()},
        "advantages_finite": bool(torch.isfinite(advantages).all()),
        "advantages_standard_deviation": float(advantages.std(unbiased=False).cpu()),
    }
    return checks, details


def render_report(result: dict[str, Any]) -> str:
    lines = [
        "# TATG-MAPPO C4.5 first-update same-rollout audit",
        "",
        f"**Verdict:** `{result['verdict']}`.",
        "",
        "C4.5 collected one short, real fixed-UTR 3D rollout and replayed its full chronological sequence once for CETM and each frozen capacity-matched control. Each variant took exactly one actor-only ordinary clipped-PPO step. This confirms update mechanics only; it is neither a training run nor a policy-performance comparison.",
        "",
        "The candidate critic took no optimizer step and remained bitwise unchanged. The copied legacy policy head remained excluded from every audit optimizer and bitwise unchanged. The stored rollout is a fixed audit trace: control old log-probabilities are recomputed from their own legal pre-update replay, so this is not an on-policy efficacy claim for any control.",
        "",
        "## Checks",
        "",
    ]
    lines.extend(f"- `{name}`: `{passed}`" for name, passed in result["checks"].items())
    lines += [
        "",
        "A pass authorizes only a separately preregistered fresh-seed pilot contract. It does not authorize cloud training, evaluation, a return claim, selection of a checkpoint, or automatic continuation.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("Refusing to write C4.5 output without --execute")
    output = Path(args.output_dir)
    if output.exists():
        raise SystemExit(f"Refusing to overwrite existing output: {output}")
    checks, details = collect_checks()
    result = {
        "protocol": "TATG-MAPPO-C45-FIRST-UPDATE-SAME-ROLLOUT-AUDIT-V1",
        "verdict": "TATG_C45_FIRST_UPDATE_SAME_ROLLOUT_PASS" if all(checks.values()) else "TATG_C45_FIRST_UPDATE_SAME_ROLLOUT_NO_GO",
        "checks": checks,
        "audit_details": details,
        "training_started": False,
        "evaluation_started": False,
        "automatic_continuation": False,
    }
    output.mkdir(parents=True)
    (output / "TATG_C45_RESULT.json").write_bytes((json.dumps(result, indent=2) + "\n").encode("utf-8"))
    (output / "TATG_C45_REPORT.md").write_bytes(render_report(result).encode("utf-8"))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
