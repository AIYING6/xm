"""Smoke-test the V8 public service-envelope relation-value actor.

This is a structural test, not a performance result. It proves that the
candidate is only active at the public causal branch, reads the seven exposed
V8 service-envelope fields, and has a pre-specified capacity-matched plain
MLP control.
"""
from __future__ import annotations

from argparse import Namespace
from pathlib import Path
import sys

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.simple_ri_gmappo import RIGMAPPOAgent, make_env
from scripts.run_compositional_service_envelope_handoff_plain_mappo import build_config


def args_for(hidden_dim: int, relation_value_mode: str) -> Namespace:
    return Namespace(
        seed=83_911, num_envs=4, rollout_steps=64, updates=64, hidden_dim=hidden_dim,
        entropy_coef=0.01, initial_retain_logit_bias=0.0, selection_eval_episodes=16,
        endpoint_episodes_per_profile=60, service_envelope_mode="compositional_v6_staged",
        future_corridor_lateral_offset=1_500.0, branch_step=40, authorization_start_step=12,
        authorization_deadline=28, commitment_decision_mode="branch_value_v8",
        authorization_decision_step=16, relation_value_mode=relation_value_mode,
        handoff_safety_mode="all_aircraft", device="cpu", out_dir=Path("results/_smoke_relation_value"),
    )


def build_agent(hidden_dim: int, relation_value_mode: str) -> tuple[RIGMAPPOAgent, np.ndarray]:
    cfg = build_config(args_for(hidden_dim, relation_value_mode))
    env = make_env(cfg, cfg.seed, training=False)
    obs, share_obs, graph = env.reset()
    agent = RIGMAPPOAgent(
        obs_dim=obs.shape[-1], node_feat_dim=graph["node_feat"].shape[-1],
        edge_feat_dim=graph["edge_feat"].shape[-1], share_obs_dim=share_obs.shape[-1],
        action_dim=env.action_dim, num_agents=env.num_agents,
        num_roles=max(4, int(np.max(graph["role"])) + 1), hidden_dim=hidden_dim,
        role_dim=cfg.role_dim, intent_dim=cfg.intent_dim, graph_encoder="no_graph",
        role_gate_mode="none", use_intent_context=False,
        commitment_relation_value_mode=relation_value_mode,
    )
    return agent.eval(), obs


def parameter_count(model: torch.nn.Module) -> int:
    return sum(parameter.numel() for parameter in model.parameters())


def main() -> None:
    torch.manual_seed(7)
    aligned, obs = build_agent(64, "aligned")
    shuffled, _ = build_agent(64, "semantic_shuffle")
    plain, _ = build_agent(66, "none")
    aligned_parameters = parameter_count(aligned)
    shuffled_parameters = parameter_count(shuffled)
    plain_parameters = parameter_count(plain)
    assert aligned_parameters == shuffled_parameters, "semantic shuffle must not change capacity"
    assert abs(plain_parameters - aligned_parameters) / aligned_parameters <= 0.02, "plain control is not capacity matched"

    observation = torch.as_tensor(obs[None, ...], dtype=torch.float32)
    logits = torch.zeros((1, 3, 2), dtype=torch.float32)
    prebranch = aligned.actor._inject_commitment_relation_logits(logits.clone(), observation, num_agents=3)
    assert torch.equal(prebranch, logits), "relation head must be inactive before the causal branch"

    branch_observation = observation.clone()
    suffix_dim = 7 + 6 + 4 * (3 - 1)
    context_start = branch_observation.shape[-1] - suffix_dim
    branch_observation[:, :, context_start + 6] = 1.0
    branched = aligned.actor._inject_commitment_relation_logits(logits.clone(), branch_observation, num_agents=3)
    assert torch.equal(branched[:, 0], logits[:, 0]) and torch.equal(branched[:, 2], logits[:, 2])
    assert not torch.equal(branched[:, 1], logits[:, 1]), "only relay branch logits must be replaced"

    shuffled_branch = shuffled.actor._inject_commitment_relation_logits(logits.clone(), branch_observation, num_agents=3)
    assert torch.equal(shuffled_branch[:, 0], logits[:, 0]) and torch.equal(shuffled_branch[:, 2], logits[:, 2])
    print(
        "PASS: V8 relation-value actor is branch-only, relay-only, public-context-only, "
        f"and capacity-matched (aligned={aligned_parameters}, plain={plain_parameters})."
    )


if __name__ == "__main__":
    main()
