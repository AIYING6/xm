"""T1 checkpoint adapter for the telemetry-native evidence chain.

This module intentionally evaluates an unchanged matched Single-Graph policy.
It is not a new network or a training method: it only guarantees that a
checkpoint's deterministic actor is called through T0's legal policy boundary
and that the resulting evidence has no competing aggregate source.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Dict, Iterable

import numpy as np
import torch

from algorithms.ri_gmappo.simple_ri_gmappo import RIGMAPPOAgent, load_matching_state_dict, stack_graphs
from scripts.telemetry_native_t0 import (
    NOMINAL,
    ActionPolicy,
    FailureScenario,
    canonical_line,
    make_env,
    sha256,
    write_evidence_bundle,
)


PROTOCOL = "T1-TELEMETRY-NATIVE-CHECKPOINT-ADAPTER-V1"
MATCHED_SG_PARAMETER_COUNT = 116_728


def _template_dimensions() -> tuple[int, int, int, int, int, int, int]:
    """Read dimensions only from the frozen public actor interface."""
    env = make_env(0, NOMINAL)
    _, share_obs, graph = env.reset()
    return (
        env.obs_dim,
        int(graph["node_feat"].shape[-1]),
        int(graph["edge_feat"].shape[-1]),
        int(share_obs.shape[-1]),
        env.action_dim,
        env.num_agents,
        max(4, int(np.max(graph["role"])) + 1),
    )


def build_matched_sg_agent(checkpoint: Path, construction_seed: int, device: str = "cpu") -> RIGMAPPOAgent:
    """Load an unchanged 116,728-parameter Single-Graph checkpoint.

    `construction_seed` fixes module construction before the checkpoint is
    loaded.  It is provenance only and is not exposed to the actor.
    """
    torch.manual_seed(int(construction_seed))
    obs_dim, node_dim, edge_dim, share_dim, action_dim, num_agents, num_roles = _template_dimensions()
    agent = RIGMAPPOAgent(
        obs_dim=obs_dim,
        node_feat_dim=node_dim,
        edge_feat_dim=edge_dim,
        share_obs_dim=share_dim,
        action_dim=action_dim,
        num_agents=num_agents,
        num_roles=num_roles,
        hidden_dim=115,
        role_dim=8,
        intent_dim=8,
        graph_encoder="single",
        role_gate_mode="none",
        use_intent_context=False,
    )
    parameter_count = sum(parameter.numel() for parameter in agent.parameters())
    if parameter_count != MATCHED_SG_PARAMETER_COUNT:
        raise RuntimeError(f"matched SG parameter mismatch: {parameter_count}")
    target = torch.device(device)
    agent.to(target)
    load_matching_state_dict(agent, str(checkpoint), target)
    agent.eval()
    return agent


def deterministic_checkpoint_policy(agent: RIGMAPPOAgent) -> ActionPolicy:
    """Return a deterministic actor callback accepting only T0 legal inputs."""
    device = next(agent.parameters()).device

    def policy(obs: np.ndarray, share_obs: np.ndarray, graph: Dict[str, Any]) -> np.ndarray:
        packed = stack_graphs([graph])
        with torch.no_grad():
            actions, *_ = agent.get_action_and_value(
                torch.as_tensor(obs[None], dtype=torch.float32, device=device),
                torch.as_tensor(packed["node_feat"], dtype=torch.float32, device=device),
                torch.as_tensor(packed["edge_feat"], dtype=torch.float32, device=device),
                torch.as_tensor(packed["role"], dtype=torch.long, device=device),
                torch.as_tensor(packed["adj"], dtype=torch.float32, device=device),
                torch.as_tensor(share_obs[None], dtype=torch.float32, device=device),
                relation_adj=torch.as_tensor(packed["relation_adj"], dtype=torch.float32, device=device),
                deterministic=True,
                intent_label=torch.as_tensor(packed["intent_label"], dtype=torch.long, device=device),
            )
        return actions.squeeze(0).detach().cpu().numpy().astype(np.int64, copy=False)

    return policy


def write_checkpoint_evidence_bundle(
    output_root: Path,
    checkpoint: Path,
    construction_seed: int,
    plans: Iterable[tuple[int, FailureScenario]],
    device: str = "cpu",
) -> dict[str, Any]:
    """Evaluate a final checkpoint through the T0 sole-source writer."""
    if not checkpoint.exists() or checkpoint.stat().st_size == 0:
        raise FileNotFoundError(checkpoint)
    agent = build_matched_sg_agent(checkpoint, construction_seed, device=device)
    manifest = write_evidence_bundle(output_root, plans, deterministic_checkpoint_policy(agent))
    manifest.update({
        "checkpoint_policy_protocol": PROTOCOL,
        "checkpoint_sha256": sha256(checkpoint),
        "checkpoint_construction_seed": int(construction_seed),
        "matched_sg_parameter_count": MATCHED_SG_PARAMETER_COUNT,
        "deterministic_actor": True,
        "training_or_checkpoint_selection": "not performed by telemetry adapter",
    })
    (output_root / "manifest.json").write_text(canonical_line(manifest) + "\n", encoding="utf-8")
    return manifest
