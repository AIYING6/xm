"""Engineering-only Phase 2I-A2 smoke with no performance measurements."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.simple_ri_gmappo import RIGMAPPOAgent
from envs import UAVIntercept3DConfig, UAVIntercept3DEnv


def main() -> None:
    seed = 909
    torch.manual_seed(seed)
    env = UAVIntercept3DEnv(UAVIntercept3DConfig(seed=seed))
    obs, share_obs, graph = env.reset()
    agent = RIGMAPPOAgent(
        obs_dim=env.obs_dim, node_feat_dim=graph["node_feat"].shape[-1], edge_feat_dim=graph["edge_feat"].shape[-1],
        share_obs_dim=share_obs.shape[-1], action_dim=env.action_dim, num_agents=env.num_agents,
        num_roles=5, hidden_dim=16, role_dim=4, intent_dim=4, graph_encoder="multi_relation",
        role_gate_mode="relation_conditioned", role_gate_prior_strength=0.4, use_intent_context=False,
    )
    logits, _, _, _ = agent.actor(
        torch.as_tensor(obs[None], dtype=torch.float32), torch.as_tensor(graph["node_feat"][None], dtype=torch.float32),
        torch.as_tensor(graph["edge_feat"][None], dtype=torch.float32), torch.as_tensor(graph["role"][None], dtype=torch.long),
        torch.as_tensor(graph["adj"][None], dtype=torch.float32), env.num_agents,
        relation_adj=torch.as_tensor(graph["relation_adj"][None], dtype=torch.float32), return_chain_aux=True,
    )
    logits.square().mean().backward()
    gates = [p for n, p in agent.named_parameters() if "role_pair_gate" in n]
    payload = {"artifact_class": "ENGINEERING_SMOKE_ONLY", "seed": seed, "pass": bool(torch.isfinite(logits).all()), "gate_parameter_count": sum(p.numel() for p in gates), "gate_has_gradient": any(p.grad is not None for p in gates)}
    out = ROOT / "results" / "development" / "phase2ia2" / "suppressed_smoke.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print("suppressed engineering smoke: PASS" if payload["pass"] and payload["gate_has_gradient"] else "suppressed engineering smoke: FAIL")


if __name__ == "__main__":
    main()
