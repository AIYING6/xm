"""Run one frozen RACG C1 source-state mechanism audit without evaluation."""
from __future__ import annotations

import argparse
import copy
import json
from dataclasses import replace
from pathlib import Path
import sys

import numpy as np
import torch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.racg_ppo import racg_update_policy  # noqa: E402
from algorithms.ri_gmappo.simple_ri_gmappo import collect_rollout, make_envs, make_optimizer, set_seed, stack_graphs  # noqa: E402
from algorithms.ri_gmappo.tgtr_ppo import evaluate_actor_change, ordinary_full_batch_update, synchronize_module_optimizer_state  # noqa: E402
from algorithms.ri_gmappo.tgtr_topology_sampler import SynchronizedTopologyGroupSampler  # noqa: E402
from scripts.run_tgtr_ppo_c1_same_rollout import (  # noqa: E402
    batch_sha256, clone_branch, make_agent, parameter_displacement, sha256_file, sha256_object, source_config,
)


def run(seed: int, source_root: Path, output_root: Path, freeze: dict, device_name: str) -> Path:
    if seed not in freeze["source"]["training_seeds"]:
        raise ValueError("seed is outside the frozen RACG C1 source set")
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
    manifest_path = root / "RACG_C1_SOURCE_RESULT.json"
    manifest = {"protocol": freeze["protocol"], "seed": seed, "status": "running"}
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    try:
        set_seed(cfg.seed)
        sampler = SynchronizedTopologyGroupSampler(cfg.seed, cfg.num_envs)
        envs = make_envs(cfg)
        selections, rows, obs_list, share_list, graph_list = [], [], [], [], []
        for index, env in enumerate(envs):
            selection = sampler.select(0, index, 0)
            sampler.apply(env, selection)
            selections.append(selection)
            rows.append(sampler.selection_row(0, index, 0, selection))
            obs, share_obs, graph = env.reset()
            obs_list.append(obs)
            share_list.append(share_obs)
            graph_list.append(graph)
        obs, share_obs, graph_obs = np.stack(obs_list), np.stack(share_list), stack_graphs(graph_list)
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
        group_counts = {group: int(np.sum(np.asarray(batch["condition_group"]) == group)) for group in freeze["candidate"]["groups"]}
        split_counts = {
            f"{group}_{split}": int(np.sum((np.asarray(batch["condition_group"]) == group) & (np.asarray(batch["condition_split"]) == split)))
            for group in freeze["candidate"]["groups"] for split in ("design", "certificate")
        }

        ordinary, ordinary_optimizer = clone_branch(agent, optimizer, cfg, envs, graph_obs, device)
        racg, racg_optimizer = clone_branch(agent, optimizer, cfg, envs, graph_obs, device)
        ordinary_info = ordinary_full_batch_update(ordinary, ordinary_optimizer, batch, cfg, device)
        ordinary_metrics = evaluate_actor_change(ordinary, batch, source_actor_state, cfg, device)
        racg_info = racg_update_policy(racg, racg_optimizer, batch, cfg, device, freeze["candidate"])
        synchronize_module_optimizer_state(racg.critic, ordinary.critic, racg_optimizer, ordinary_optimizer)
        racg_metrics = evaluate_actor_change(racg, batch, source_actor_state, cfg, device)
        critic_exact = sha256_object(ordinary.critic.state_dict()) == sha256_object(racg.critic.state_dict())
        finite = all(torch.isfinite(value).all().item() for value in racg.state_dict().values())
        manifest.update({
            "status": "completed",
            "source_manifest_sha256": sha256_file(source_manifest),
            "source_runtime_sha256": sha256_file(source_runtime),
            "batch_sha256": batch_sha256(batch),
            "group_counts": group_counts,
            "split_counts": split_counts,
            "sampler_manifest": sampler.manifest(),
            "ordinary": {
                **ordinary_info, "metrics": ordinary_metrics,
                "actor_displacement_l2": parameter_displacement(ordinary.actor, source_actor_state),
                "critic_displacement_l2": parameter_displacement(ordinary.critic, source_critic_state),
            },
            "racg": {
                **racg_info, "metrics": racg_metrics,
                "actor_displacement_l2": parameter_displacement(racg.actor, source_actor_state),
                "critic_displacement_l2": parameter_displacement(racg.critic, source_critic_state),
            },
            "critic_state_exact_vs_ordinary": critic_exact,
            "all_racg_parameters_finite": finite,
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
    parser.add_argument("--freeze", type=Path, default=ROOT / "configs" / "racg_ppo_c1_freeze.json")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("--execute is required by the frozen RACG C1 contract")
    freeze = json.loads(args.freeze.read_text(encoding="utf-8"))
    result = run(args.seed, args.source_root, args.output_root, freeze, args.device)
    print(json.dumps({"status": "RACG_C1_SOURCE_COMPLETE", "result": str(result)}, indent=2))


if __name__ == "__main__":
    main()
