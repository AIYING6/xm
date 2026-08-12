"""DEVELOPMENT_ONLY Role-Gate functionality and capacity diagnostic."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.simple_ri_gmappo import RIGMAPPOAgent
from envs import UAVIntercept3DConfig, UAVIntercept3DEnv
OUT = ROOT / "results" / "development" / "role_gate_phase2ia"


def build(mode: str, seed: int):
    torch.manual_seed(seed)
    env = UAVIntercept3DEnv(UAVIntercept3DConfig(seed=seed))
    obs, share, graph = env.reset()
    agent = RIGMAPPOAgent(
        obs_dim=env.obs_dim, node_feat_dim=graph["node_feat"].shape[-1],
        edge_feat_dim=graph["edge_feat"].shape[-1], share_obs_dim=env.share_obs_dim,
        action_dim=env.action_dim, num_agents=env.num_agents, hidden_dim=32,
        role_dim=8, intent_dim=8, graph_encoder="multi_relation", num_roles=5,
        use_intent_context=False, role_gate_mode=mode,
    )
    return env, agent, obs, share, graph


def forward(agent, obs, share, graph):
    logits, attention, _, _ = agent.actor(
        torch.as_tensor(obs[None], dtype=torch.float32),
        torch.as_tensor(graph["node_feat"][None], dtype=torch.float32),
        torch.as_tensor(graph["edge_feat"][None], dtype=torch.float32),
        torch.as_tensor(graph["role"][None], dtype=torch.long),
        torch.as_tensor(graph["adj"][None], dtype=torch.float32),
        relation_adj=torch.as_tensor(graph["relation_adj"][None], dtype=torch.float32),
        num_agents=agent.num_agents,
        intent_label=torch.as_tensor(graph["intent_label"][None], dtype=torch.long),
        detach_intent=False, oracle_intent=False,
        return_chain_aux=True,
    )
    return logits, attention


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for mode in ("none", "shared", "relation_conditioned"):
        for seed in (101, 202, 303):
            env, agent, obs, share, graph = build(mode, seed)
            params = sum(p.numel() for p in agent.parameters() if p.requires_grad)
            gate_params = [p for n, p in agent.named_parameters() if "role_pair_gate" in n]
            before = forward(agent, obs, share, graph)[0]
            loss = before.square().mean()
            loss.backward()
            grad_norm = math.sqrt(sum(float(p.grad.detach().square().sum()) for p in gate_params if p.grad is not None))
            active = [m for m in agent.modules() if getattr(m, "role_pair_gate", None) is not None]
            intervention_on = intervention_off = False
            if active and mode != "none":
                layer = active[0]
                with torch.no_grad():
                    original = layer.role_pair_gate.weight.detach().clone()
                    layer.role_pair_gate.weight.fill_(20.0)
                on = forward(agent, obs, share, graph)[0]
                with torch.no_grad():
                    layer.role_pair_gate.weight.fill_(-20.0)
                off = forward(agent, obs, share, graph)[0]
                intervention_on = float((on - before).abs().max())
                intervention_off = float((off - before).abs().max())
                with torch.no_grad():
                    layer.role_pair_gate.weight.copy_(original)
            effective_prior = 1.0 if mode == "none" else 0.5
            if mode != "none" and gate_params:
                effective_prior = float(torch.sigmoid(gate_params[0].detach()).mean())
            rows.append({
                "artifact_class": "DEVELOPMENT_ONLY",
                "mode": mode, "seed": seed, "trainable_params": params,
                "gate_param_count": sum(p.numel() for p in gate_params),
                "gate_grad_norm": grad_norm,
                "effective_initial_gate_mean": effective_prior,
                "force_one_max_logit_delta": intervention_on,
                "force_zero_max_logit_delta": intervention_off,
            })
    (OUT / "role_gate_diagnostic.json").write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    print(OUT / "role_gate_diagnostic.json")


if __name__ == "__main__":
    main()
