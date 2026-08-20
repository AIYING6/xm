from pathlib import Path

import torch

from algorithms.ri_gmappo.simple_ri_gmappo import RIGMAPPOAgent
from scripts.telemetry_native_t0 import F0, NOMINAL, make_env
from scripts.telemetry_native_t1 import (
    MATCHED_SG_PARAMETER_COUNT,
    build_matched_sg_agent,
    deterministic_checkpoint_policy,
    write_checkpoint_evidence_bundle,
)


def write_untrained_matched_sg_checkpoint(path: Path) -> None:
    env = make_env(0, NOMINAL)
    _, share_obs, graph = env.reset()
    torch.manual_seed(2201)
    agent = RIGMAPPOAgent(
        obs_dim=env.obs_dim,
        node_feat_dim=graph["node_feat"].shape[-1],
        edge_feat_dim=graph["edge_feat"].shape[-1],
        share_obs_dim=share_obs.shape[-1],
        action_dim=env.action_dim,
        num_agents=env.num_agents,
        num_roles=max(4, int(graph["role"].max()) + 1),
        hidden_dim=115,
        role_dim=8,
        intent_dim=8,
        graph_encoder="single",
        role_gate_mode="none",
        use_intent_context=False,
    )
    assert sum(parameter.numel() for parameter in agent.parameters()) == MATCHED_SG_PARAMETER_COUNT
    torch.save(agent.state_dict(), path)


def test_checkpoint_adapter_is_deterministic_and_telemetry_native(tmp_path):
    checkpoint = tmp_path / "untrained_matched_sg.pt"
    write_untrained_matched_sg_checkpoint(checkpoint)
    agent = build_matched_sg_agent(checkpoint, construction_seed=2201)
    policy = deterministic_checkpoint_policy(agent)
    env = make_env(910000, NOMINAL)
    obs, share_obs, graph = env.reset()
    assert policy(obs, share_obs, graph).tolist() == policy(obs, share_obs, graph).tolist()

    out = tmp_path / "native_checkpoint_eval"
    manifest = write_checkpoint_evidence_bundle(
        out, checkpoint, construction_seed=2201, plans=[(910000, NOMINAL), (910001, F0)]
    )
    assert manifest["source_closure_pass"] is True
    assert manifest["historical_aggregate_reuse"] is False
    assert manifest["matched_sg_parameter_count"] == MATCHED_SG_PARAMETER_COUNT
    assert (out / "raw_step_telemetry.jsonl").exists()
    assert (out / "episode_aggregates.jsonl").exists()
