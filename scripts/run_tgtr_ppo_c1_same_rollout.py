"""Run one TGTR C1 source-state mechanism audit without evaluation."""
from __future__ import annotations

import argparse
import copy
import hashlib
import io
import json
from dataclasses import fields, replace
from pathlib import Path
import sys

import numpy as np
import torch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.simple_ri_gmappo import (  # noqa: E402
    RIGMAPPOAgent,
    RIGMAPPOConfig,
    collect_rollout,
    make_envs,
    make_optimizer,
    set_seed,
    stack_graphs,
)
from algorithms.ri_gmappo.tgtr_ppo import (  # noqa: E402
    evaluate_actor_change,
    ordinary_full_batch_update,
    synchronize_module_optimizer_state,
    tgtr_update_policy,
)
from algorithms.ri_gmappo.tgtr_topology_sampler import SynchronizedTopologyGroupSampler  # noqa: E402


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_object(value) -> str:
    stream = io.BytesIO()
    torch.save(value, stream)
    return hashlib.sha256(stream.getvalue()).hexdigest()


def batch_sha256(batch: dict) -> str:
    digest = hashlib.sha256()
    for key in (
        "obs", "share_obs", "node_feat", "edge_feat", "role", "adj", "relation_adj",
        "actions", "logp", "advantages", "returns", "condition_group", "condition_split",
    ):
        value = np.ascontiguousarray(np.asarray(batch[key]))
        digest.update(key.encode("utf-8"))
        digest.update(str(value.dtype).encode("utf-8"))
        digest.update(np.asarray(value.shape, dtype=np.int64).tobytes())
        digest.update(value.tobytes())
    return digest.hexdigest()


def source_config(path: Path) -> RIGMAPPOConfig:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("status") != "completed" or payload.get("arm") != "utr_sg":
        raise RuntimeError(f"invalid TGTR C1 source manifest: {path}")
    allowed = {field.name for field in fields(RIGMAPPOConfig)}
    raw = {key: value for key, value in payload["config"].items() if key in allowed}
    return RIGMAPPOConfig(**raw)


def make_agent(cfg: RIGMAPPOConfig, envs, graph_obs: dict, device: torch.device) -> RIGMAPPOAgent:
    env = envs[0]
    agent = RIGMAPPOAgent(
        obs_dim=env.obs_dim,
        node_feat_dim=graph_obs["node_feat"].shape[-1],
        edge_feat_dim=graph_obs["edge_feat"].shape[-1],
        share_obs_dim=env.share_obs_dim,
        action_dim=env.action_dim,
        num_agents=env.num_agents,
        hidden_dim=cfg.hidden_dim,
        role_dim=cfg.role_dim,
        intent_dim=cfg.intent_dim,
        graph_encoder=cfg.graph_encoder,
        graph_message_ablation=cfg.graph_message_ablation,
        graph_input_ablation=cfg.graph_input_ablation,
        use_intent_context=cfg.env_name != "3d_intercept",
        role_gate_prior_strength=cfg.role_gate_prior_strength,
        multi_relation_global_residual_weight=cfg.multi_relation_global_residual_weight,
        role_gate_mode=cfg.role_gate_mode,
        counterfactual_critic_enabled=cfg.counterfactual_critic_enabled,
        num_roles=max(4, int(np.max(graph_obs["role"])) + 1),
    ).to(device)
    return agent


def clone_branch(agent, optimizer, cfg, envs, graph_obs, device):
    clone = make_agent(cfg, envs, graph_obs, device)
    clone.load_state_dict(copy.deepcopy(agent.state_dict()), strict=True)
    clone_optimizer = make_optimizer(clone, cfg)
    clone_optimizer.load_state_dict(copy.deepcopy(optimizer.state_dict()))
    return clone, clone_optimizer


def parameter_displacement(module, reference_state: dict) -> float:
    total = torch.zeros((), device=next(module.parameters()).device)
    with torch.no_grad():
        for name, parameter in module.named_parameters():
            total += (parameter - reference_state[name].to(parameter.device)).square().sum()
    return float(torch.sqrt(total).cpu())


def run(seed: int, source_root: Path, output_root: Path, freeze: dict, device_name: str) -> Path:
    if seed not in freeze["source"]["training_seeds"]:
        raise ValueError("seed is outside the frozen TGTR C1 source set")
    source = source_root / f"seed{seed}"
    source_manifest = source / "run_manifest.json"
    source_runtime = source / "actor_critic_runtime_state_latest.pt"
    if not source_manifest.is_file() or not source_runtime.is_file():
        raise FileNotFoundError(f"missing source state: {source}")
    cfg = source_config(source_manifest)
    device = torch.device(device_name if device_name != "auto" else ("cuda" if torch.cuda.is_available() else "cpu"))
    cfg = replace(
        cfg,
        seed=int(freeze["source"]["rollout_seed_offset"]) + seed,
        num_envs=24,
        rollout_steps=64,
        minibatch_graphs=1536,
        ppo_epochs=int(freeze["source"]["ppo_epochs"]),
        device=str(device),
        evaluation_enabled=False,
        fixed_stratified_topology_sampler=False,
        actor_gradient_mode="standard",
        drtp_sampler_mode="none",
        target_kl=None,
        policy_update_guard_mode="none",
        group_weighted_actor_enabled=False,
        group_weighted_actor_telemetry=False,
        sam_enabled=False,
        counterfactual_critic_enabled=False,
    )
    root = output_root / "runs" / f"seed{seed}"
    root.mkdir(parents=True, exist_ok=False)
    manifest_path = root / "TGTR_C1_SOURCE_RESULT.json"
    manifest = {"protocol": freeze["protocol"], "seed": seed, "status": "running"}
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    try:
        set_seed(cfg.seed)
        sampler = SynchronizedTopologyGroupSampler(cfg.seed, cfg.num_envs)
        envs = make_envs(cfg)
        selections = []
        rows = []
        obs_list, share_list, graph_list = [], [], []
        for index, env in enumerate(envs):
            selection = sampler.select(0, index, 0)
            sampler.apply(env, selection)
            selections.append(selection)
            rows.append(sampler.selection_row(0, index, 0, selection))
            obs, share_obs, graph = env.reset()
            obs_list.append(obs)
            share_list.append(share_obs)
            graph_list.append(graph)
        obs = np.stack(obs_list)
        share_obs = np.stack(share_list)
        graph_obs = stack_graphs(graph_list)
        agent = make_agent(cfg, envs, graph_obs, device)
        optimizer = make_optimizer(agent, cfg)
        runtime = torch.load(source_runtime, map_location=device, weights_only=False)
        agent.load_state_dict(runtime["model_state"], strict=True)
        optimizer.load_state_dict(runtime["optimizer_state"])
        source_actor_state = copy.deepcopy(agent.actor.state_dict())
        source_critic_state = copy.deepcopy(agent.critic.state_dict())
        batch = collect_rollout(
            agent, envs, obs, share_obs, graph_obs, cfg, device,
            episode_counts=[0] * cfg.num_envs,
            current_update=int(freeze["source"]["source_update"]) + 1,
            drtp_sampler=sampler,
            drtp_episode_returns=[0.0] * cfg.num_envs,
            drtp_selections=selections,
            drtp_rows=rows,
        )
        batch["condition_split"] = sampler.split_matrix(cfg.rollout_steps)
        paired_hash = batch_sha256(batch)
        group_counts = {
            group: int(np.sum(np.asarray(batch["condition_group"]) == group))
            for group in freeze["candidate"]["groups"]
        }
        split_counts = {
            f"{group}_{split}": int(np.sum(
                (np.asarray(batch["condition_group"]) == group)
                & (np.asarray(batch["condition_split"]) == split)
            ))
            for group in freeze["candidate"]["groups"] for split in ("design", "certificate")
        }

        ordinary, ordinary_optimizer = clone_branch(agent, optimizer, cfg, envs, graph_obs, device)
        tgtr, tgtr_optimizer = clone_branch(agent, optimizer, cfg, envs, graph_obs, device)
        ordinary_info = ordinary_full_batch_update(ordinary, ordinary_optimizer, batch, cfg, device)
        ordinary_metrics = evaluate_actor_change(ordinary, batch, source_actor_state, cfg, device)
        tgtr_info = tgtr_update_policy(tgtr, tgtr_optimizer, batch, cfg, device)
        # Actor projection must not redefine critic learning.  Commit the
        # matched ordinary critic transaction and its Adam slots exactly.
        synchronize_module_optimizer_state(
            tgtr.critic, ordinary.critic, tgtr_optimizer, ordinary_optimizer
        )
        tgtr_metrics = evaluate_actor_change(tgtr, batch, source_actor_state, cfg, device)
        critic_exact = sha256_object(ordinary.critic.state_dict()) == sha256_object(tgtr.critic.state_dict())
        finite = all(torch.isfinite(value).all().item() for value in tgtr.state_dict().values())
        manifest.update({
            "status": "completed",
            "source_manifest_sha256": sha256_file(source_manifest),
            "source_runtime_sha256": sha256_file(source_runtime),
            "batch_sha256": paired_hash,
            "group_counts": group_counts,
            "split_counts": split_counts,
            "sampler_manifest": sampler.manifest(),
            "ordinary": {
                **ordinary_info,
                "metrics": ordinary_metrics,
                "actor_displacement_l2": parameter_displacement(ordinary.actor, source_actor_state),
                "critic_displacement_l2": parameter_displacement(ordinary.critic, source_critic_state),
            },
            "tgtr": {
                **tgtr_info,
                "metrics": tgtr_metrics,
                "actor_displacement_l2": parameter_displacement(tgtr.actor, source_actor_state),
                "critic_displacement_l2": parameter_displacement(tgtr.critic, source_critic_state),
            },
            "critic_state_exact_vs_ordinary": critic_exact,
            "all_tgtr_parameters_finite": finite,
            "formal_evaluation_used": False,
            "environment_steps": 1536,
            "ppo_updates_per_branch": int(cfg.ppo_epochs),
        })
    except BaseException as exc:
        manifest.update({"status": "technical_invalid", "error": repr(exc)})
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        raise
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--freeze", type=Path, default=ROOT / "configs" / "tgtr_ppo_c1_freeze.json")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("--execute is required by the frozen C1 contract")
    freeze = json.loads(args.freeze.read_text(encoding="utf-8"))
    result = run(args.seed, args.source_root, args.output_root, freeze, args.device)
    print(json.dumps({"status": "TGTR_C1_SOURCE_COMPLETE", "result": str(result)}, indent=2))


if __name__ == "__main__":
    main()
