"""Freeze checks and one-update integration smoke for RSG-TC.

This script is intentionally not a development-training launcher. It verifies
the frozen contract and runs only one tiny update per candidate to validate the
existing MAPPO training path with the new encoder.
"""
from __future__ import annotations

import hashlib
import inspect
import json
import math
import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.simple_ri_gmappo import (  # noqa: E402
    RIGMAPPOAgent,
    RIGMAPPOConfig,
    RSG_TC_EDGE_FEATURE_INDICES,
    RSG_TC_RELATION_COUNT,
    load_matching_state_dict,
    make_env,
    stack_graphs,
    train_ri_gmappo,
)
from algorithms.ri_gmappo import simple_ri_gmappo as model_module  # noqa: E402


PROTOCOL = "PHASE-RSG-TC-0-V1"
SMOKE_SEED = 1501
DEV_SEEDS = (1501, 1502, 1503)
TAPE_START = 340000
TAPE_EPISODES = 100
METHODS = {
    "matched_single_graph": {"graph_encoder": "single", "hidden_dim": 115},
    "rsg_tc": {"graph_encoder": "rsg_tc", "hidden_dim": 114},
}
SMOKE_ROOT = ROOT / "results/development/phase_rsg_tc0_smoke"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_env(seed: int):
    cfg = RIGMAPPOConfig(
        env_name="3d_intercept", seed=seed, strict_target_sensing=True,
        agent_target_info_bottleneck=True, relay_dependent_task=True,
        business_grounded_geometry=True, communication_range_scale=1.0,
        failed_blue_agent=1, node_failure_start_step=44,
        node_failure_duration_steps=80, device="cpu",
    )
    return make_env(cfg, seed, training=False)


def make_agent(method: dict[str, object], seed: int, device: str = "cpu") -> tuple[RIGMAPPOAgent, object, dict]:
    env = build_env(seed)
    obs, share, graph = env.reset()
    agent = RIGMAPPOAgent(
        obs_dim=env.obs_dim, node_feat_dim=graph["node_feat"].shape[-1],
        edge_feat_dim=graph["edge_feat"].shape[-1], share_obs_dim=share.shape[-1],
        action_dim=env.action_dim, num_agents=env.num_agents,
        num_roles=max(4, int(np.max(graph["role"])) + 1),
        hidden_dim=int(method["hidden_dim"]), role_dim=8, intent_dim=8,
        graph_encoder=str(method["graph_encoder"]), role_gate_mode="none",
        use_intent_context=False,
    ).to(device)
    return agent, env, {"obs": obs, "share": share, "graph": graph}


def parameter_count(agent: torch.nn.Module) -> int:
    return sum(parameter.numel() for parameter in agent.parameters())


def contract_checks() -> dict[str, object]:
    checks: dict[str, object] = {}
    checks["development_seeds_noncanonical"] = all(seed not in range(5) for seed in DEV_SEEDS)
    checks["shared_tape_frozen"] = TAPE_START == 340000 and TAPE_EPISODES == 100
    checks["relation_multihot_count"] = RSG_TC_RELATION_COUNT == 3
    checks["edge_feature_indices_frozen"] = RSG_TC_EDGE_FEATURE_INDICES == (3, 11, 12, 13, 15, 16)
    layer_source = inspect.getsource(model_module.TopologyConditionedGraphAttentionLayer)
    checks["forbidden_global_route_inputs_absent"] = not any(
        token in layer_source.lower()
        for token in ("shortest_path", "ground_truth_route", "failure_label", "full_graph_connectivity")
    )
    checks["multihot_uses_relation_permutation"] = "relation_adj.permute" in layer_source and "argmax" not in layer_source

    agents = {}
    for method_name, spec in METHODS.items():
        agent, env, state = make_agent(spec, SMOKE_SEED)
        agents[method_name] = (agent, env, state)
        checks[f"{method_name}_parameter_count"] = parameter_count(agent)
        if method_name == "rsg_tc":
            zero_layers = []
            for layer in (agent.actor.rsg_tc_gat1, agent.actor.rsg_tc_gat2):
                zero_layers.append(float(layer.relation_bias[-1].weight.abs().max().item()) == 0.0)
            checks["zero_bias_initialization"] = all(zero_layers)
            graph = state["graph"]
            packed = stack_graphs([graph])
            relation = torch.as_tensor(packed["relation_adj"], dtype=torch.float32)
            checks["relation_adj_shape"] = tuple(relation.shape) == (1, 3, graph["node_feat"].shape[0], graph["node_feat"].shape[0])
            # A simultaneous P+C edge is legal in the schema; the encoder must
            # receive both bits rather than an argmax category.
            checks["multihot_overlap_representable"] = (
                agent.actor.rsg_tc_gat1.relation_bias[0].in_features
                == RSG_TC_RELATION_COUNT + len(RSG_TC_EDGE_FEATURE_INDICES)
            )
            try:
                agent.actor(
                    torch.as_tensor(state["obs"][None], dtype=torch.float32),
                    torch.as_tensor(packed["node_feat"], dtype=torch.float32),
                    torch.as_tensor(packed["edge_feat"], dtype=torch.float32),
                    torch.as_tensor(packed["role"], dtype=torch.long),
                    torch.as_tensor(packed["adj"], dtype=torch.float32), env.num_agents,
                    relation_adj=None, return_chain_aux=True,
                )
            except ValueError:
                checks["relation_required_for_rsg_tc"] = True
            else:
                checks["relation_required_for_rsg_tc"] = False

    sg_count = checks["matched_single_graph_parameter_count"]
    rsg_count = checks["rsg_tc_parameter_count"]
    checks["parameter_match_under_1_percent"] = abs(rsg_count - sg_count) / rsg_count <= 0.01
    checks["parameter_match_relative_difference"] = abs(rsg_count - sg_count) / rsg_count
    checks["all_contract_checks"] = all(value for key, value in checks.items() if key not in {"matched_single_graph_parameter_count", "rsg_tc_parameter_count", "parameter_match_relative_difference"})
    return checks


def one_update_smoke(output_root: Path) -> dict[str, object]:
    output_root.mkdir(parents=True, exist_ok=True)
    results = {}
    for method_name, spec in METHODS.items():
        out_dir = output_root / method_name
        if out_dir.exists() and any(out_dir.iterdir()):
            raise FileExistsError(f"refusing to overwrite smoke output: {out_dir}")
        cfg = RIGMAPPOConfig(
            env_name="3d_intercept", seed=SMOKE_SEED, num_envs=2, rollout_steps=8,
            updates=1, hidden_dim=int(spec["hidden_dim"]), role_dim=8, intent_dim=8,
            graph_encoder=str(spec["graph_encoder"]), role_gate_mode="none",
            target_policy="straight", strict_target_sensing=True,
            agent_target_info_bottleneck=True, relay_dependent_task=True,
            business_grounded_geometry=True, communication_range_scale=1.0,
            communication_dropout_prob=0.0, message_delay_steps=0,
            radar_dropout_prob=0.0, min_success_step=1000,
            failed_blue_agent=1, node_failure_start_step=44,
            node_failure_duration_steps=80, evaluation_enabled=False,
            save_interval=1, save_snapshots=False, out_dir=str(out_dir),
            device="cuda" if torch.cuda.is_available() else "cpu",
        )
        train_ri_gmappo(cfg)
        checkpoint = out_dir / "actor_critic_latest.pt"
        log = out_dir / "train_log.csv"
        if not checkpoint.exists() or not log.exists():
            raise FileNotFoundError(f"missing smoke artifact for {method_name}")
        results[method_name] = {
            "checkpoint": str(checkpoint), "checkpoint_sha256": sha256(checkpoint),
            "train_log": str(log), "train_log_sha256": sha256(log),
            "finite_checkpoint_bytes": checkpoint.stat().st_size > 0,
        }
    return results


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--checks-only", action="store_true")
    args = parser.parse_args()
    checks = contract_checks()
    if not checks["all_contract_checks"]:
        raise SystemExit(json.dumps({"protocol": PROTOCOL, "checks": checks}, indent=2))
    if args.checks_only:
        print(json.dumps({"protocol": PROTOCOL, "checks": checks, "status": "PASS"}, indent=2))
        return
    smoke = one_update_smoke(SMOKE_ROOT)
    result = {
        "protocol": PROTOCOL, "formal_training_started": False,
        "one_update_integration_smoke": True, "formal_training_authorized": False,
        "checks": checks, "smoke": smoke, "status": "PASS",
    }
    (SMOKE_ROOT / "RSG_TC0_CONTRACT_RESULT.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
