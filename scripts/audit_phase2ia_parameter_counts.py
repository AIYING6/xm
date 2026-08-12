"""Compute final architecture parameter counts without training."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.simple_ri_gmappo import RIGMAPPOAgent
from envs import UAVIntercept3DConfig, UAVIntercept3DEnv


def count(agent: RIGMAPPOAgent) -> dict[str, int]:
    by_name = {name: param.numel() for name, param in agent.named_parameters() if param.requires_grad}
    return {
        "total": sum(by_name.values()),
        "actor": sum(v for k, v in by_name.items() if k.startswith("actor.")),
        "critic": sum(v for k, v in by_name.items() if k.startswith("critic.")),
        "gate": sum(v for k, v in by_name.items() if "role_pair_gate" in k),
        "global_residual": sum(v for k, v in by_name.items() if "global_layer" in k or ".fuse" in k),
    }


def make(env, encoder: str, hidden: int, residual: float = 1.0) -> RIGMAPPOAgent:
    _, _, graph = env.reset()
    return RIGMAPPOAgent(
        env.obs_dim, graph["node_feat"].shape[-1], graph["edge_feat"].shape[-1],
        env.share_obs_dim, env.action_dim, env.num_agents, 5, hidden, 8, 8,
        graph_encoder=encoder, use_intent_context=False,
        role_gate_mode="relation_conditioned", multi_relation_global_residual_weight=residual,
    )


def main() -> None:
    env = UAVIntercept3DEnv(UAVIntercept3DConfig(seed=101))
    full = count(make(env, "multi_relation", 64))
    ordinary = count(make(env, "single", 64))
    mappo = count(make(env, "no_graph", 64))
    no_union = count(make(env, "multi_relation", 64, 0.0))
    choices = []
    for width in range(64, 193):
        candidate = count(make(env, "single", width))
        choices.append((abs(candidate["total"] - full["total"]), width, candidate))
    _, matched_width, matched = min(choices, key=lambda x: x[0])
    out = {
        "full": {"hidden_dim": 64, **full},
        "mappo": {"hidden_dim": 64, **mappo},
        "ordinary_single_graph": {"hidden_dim": 64, **ordinary},
        "parameter_matched_single_graph": {"hidden_dim": matched_width, **matched,
            "relative_difference": abs(matched["total"] - full["total"]) / full["total"]},
        "full_no_union_residual": {"hidden_dim": 64, **no_union},
    }
    path = ROOT / "results" / "development" / "role_gate_phase2ia" / "parameter_counts.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(path)


if __name__ == "__main__":
    main()
