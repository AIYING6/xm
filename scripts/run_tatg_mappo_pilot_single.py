"""Frozen four-arm TATG-MAPPO pilot execution interface.

This runner deliberately separates collection/training from evaluation.  It
contains the only permitted cloud-side training implementation for the frozen
three-seed pilot, but refuses to run unless ``--execute`` is supplied.  The
offline development tape is not imported here.
"""

from __future__ import annotations

import argparse
import copy
import csv
import json
import math
import random
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch.nn.utils import clip_grad_norm_

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.simple_ri_gmappo import (  # noqa: E402
    RIGMAPPOAgent,
    RIGMAPPOConfig,
    compute_gae,
    make_envs,
    set_seed,
    stack_graphs,
    train_ri_gmappo,
)
from algorithms.ri_gmappo.tatg_outer_rollout import (  # noqa: E402
    TATGActorCriticSystem,
    collect_tatg_utr_rollout,
    make_tatg_optimizer,
)
from algorithms.ri_gmappo.tatg_sequence_ppo import clipped_actor_objective  # noqa: E402
from algorithms.ri_gmappo.tatg_sequence_runner import TATGSequenceActorRunner  # noqa: E402
from algorithms.ri_gmappo.tcr_topology_sampler import FixedStratifiedTopologySampler  # noqa: E402


PROTOCOL = "TATG-MAPPO-FRESH-SEED-PILOT-TRAINING-V1"
BASELINE_ARM = "utr_snapshot_sg"
TEMPORAL_ARMS = {
    "tatg_cetm_utr": "cetm",
    "tatg_snapshot_gru_utr": "snapshot_gru",
    "tatg_zero_residual_utr": "cetm_zero_delta",
}
ALL_ARMS = (BASELINE_ARM, *TEMPORAL_ARMS)
FROZEN_SEEDS = (75011, 75012, 75013)
NUM_ENVS = 4
ROLLOUT_STEPS = 64
UPDATES = 3907
STEPS_PER_TRAJECTORY = NUM_ENVS * ROLLOUT_STEPS * UPDATES


def pilot_config(arm: str, seed: int, output_root: str | Path, *, updates: int = UPDATES) -> RIGMAPPOConfig:
    """Return the exact, shared training configuration for one frozen arm."""

    if arm not in ALL_ARMS:
        raise ValueError(f"unknown pilot arm: {arm}")
    if int(seed) not in FROZEN_SEEDS:
        raise ValueError(f"seed is outside the frozen pilot namespace: {seed}")
    output = Path(output_root) / "runs" / arm / f"seed{int(seed)}"
    return RIGMAPPOConfig(
        env_name="3d_intercept",
        seed=int(seed),
        num_envs=NUM_ENVS,
        rollout_steps=ROLLOUT_STEPS,
        updates=int(updates),
        hidden_dim=128,
        role_dim=8,
        intent_dim=8,
        graph_encoder="single",
        lr=3e-4,
        gamma=0.99,
        gae_lambda=0.95,
        clip_coef=0.2,
        entropy_coef=0.01,
        value_coef=0.5,
        ppo_epochs=4,
        minibatch_graphs=NUM_ENVS * ROLLOUT_STEPS,
        max_grad_norm=0.5,
        strict_target_sensing=True,
        agent_target_info_bottleneck=True,
        relay_dependent_task=True,
        device="cuda" if torch.cuda.is_available() else "cpu",
        fixed_stratified_topology_sampler=True,
        fixed_stratified_topology_sampler_seed=int(seed),
        drtp_sampler_mode="none",
        actor_gradient_mode="standard",
        evaluation_enabled=False,
        runtime_state_checkpointing=True,
        runtime_state_save_interval=int(updates),
        milestone_updates={976: "250k", 1953: "500k", 3907: "1m"},
        out_dir=str(output),
        save_interval=int(updates),
        save_snapshots=False,
    )


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_bytes((json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8"))


def _manifest(arm: str, seed: int, cfg: RIGMAPPOConfig, *, status: str) -> dict[str, Any]:
    return {
        "protocol": PROTOCOL,
        "arm": arm,
        "seed": int(seed),
        "status": status,
        "fixed_utr": True,
        "num_envs": NUM_ENVS,
        "rollout_steps": ROLLOUT_STEPS,
        "updates": int(cfg.updates),
        "environment_steps": int(cfg.num_envs * cfg.rollout_steps * cfg.updates),
        "evaluation_started": False,
        "checkpoint_selection": "fixed_endpoint_only",
        "temporal_memory_kind": TEMPORAL_ARMS.get(arm),
        "config": asdict(cfg),
    }


def _build_snapshot(graph_obs: dict[str, np.ndarray], obs: np.ndarray, share_obs: np.ndarray, env: Any, cfg: RIGMAPPOConfig) -> RIGMAPPOAgent:
    return RIGMAPPOAgent(
        obs_dim=int(obs.shape[-1]),
        node_feat_dim=int(graph_obs["node_feat"].shape[-1]),
        edge_feat_dim=int(graph_obs["edge_feat"].shape[-1]),
        share_obs_dim=int(share_obs.shape[-1]),
        action_dim=int(env.action_dim),
        # The 3D environment exposes its blue-agent count through the common
        # ``num_agents`` interface.  Never reach into a 2D-only ``num_blue``
        # convenience attribute here.
        num_agents=int(env.num_agents),
        num_roles=max(4, int(np.max(graph_obs["role"])) + 1),
        hidden_dim=cfg.hidden_dim,
        role_dim=cfg.role_dim,
        intent_dim=cfg.intent_dim,
        graph_encoder=cfg.graph_encoder,
        graph_message_ablation=cfg.graph_message_ablation,
        graph_input_ablation=cfg.graph_input_ablation,
        use_intent_context=False,
        role_gate_prior_strength=cfg.role_gate_prior_strength,
        multi_relation_global_residual_weight=cfg.multi_relation_global_residual_weight,
        role_gate_mode=cfg.role_gate_mode,
    )


def _next_values(system: TATGActorCriticSystem, batch: dict[str, Any], device: torch.device) -> np.ndarray:
    with torch.no_grad():
        values = system.critic_value(
            torch.as_tensor(batch["next_share_obs"], dtype=torch.float32, device=device),
            torch.as_tensor(batch["next_graph_obs"]["role"], dtype=torch.long, device=device),
        )
    return values.cpu().numpy()


def _update_temporal(system: TATGActorCriticSystem, runner: TATGSequenceActorRunner, optimizer: torch.optim.Optimizer, batch: dict[str, Any], cfg: RIGMAPPOConfig, device: torch.device) -> dict[str, float]:
    """Run ordinary clipped PPO with actor replay kept in [time, environment]."""

    next_values = _next_values(system, batch, device)
    advantages, returns = compute_gae(
        batch["rewards"], batch["dones"].astype(np.float32), batch["values"], next_values, cfg.gamma, cfg.gae_lambda
    )
    tensors = {
        key: torch.as_tensor(batch[key], dtype=(torch.long if key in {"role", "actions"} else torch.float32), device=device)
        for key in ("obs", "node_feat", "edge_feat", "role", "adj", "relation_adj", "actions", "logp", "share_obs")
    }
    dones = torch.as_tensor(batch["dones"], dtype=torch.bool, device=device)
    advantages_t = torch.as_tensor(advantages, dtype=torch.float32, device=device)
    advantages_t = (advantages_t - advantages_t.mean()) / (advantages_t.std() + 1e-8)
    returns_t = torch.as_tensor(returns, dtype=torch.float32, device=device)
    policy_losses: list[float] = []
    value_losses: list[float] = []
    entropies: list[float] = []
    kls: list[float] = []
    clip_fractions: list[float] = []
    grad_norms: list[float] = []
    for _ in range(cfg.ppo_epochs):
        replay = runner.replay_rollout(
            obs=tensors["obs"], node_feat=tensors["node_feat"], edge_feat=tensors["edge_feat"], role=tensors["role"],
            adj=tensors["adj"], relation_adj=tensors["relation_adj"], actions=tensors["actions"], dones=dones,
            state_before_rollout=batch["tatg_state_before_rollout"],
        )
        actor_loss = clipped_actor_objective(replay, tensors["logp"], advantages_t, cfg.clip_coef, cfg.entropy_coef)
        time_steps, environments, agents = tensors["actions"].shape
        critic_values = system.critic_value(
            tensors["share_obs"].reshape(time_steps * environments, agents, -1),
            tensors["role"].reshape(time_steps * environments, *tensors["role"].shape[2:]),
        ).reshape(time_steps, environments, agents)
        value_loss = 0.5 * (returns_t - critic_values).pow(2).mean()
        loss = actor_loss + cfg.value_coef * value_loss
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        grad_norm = float(clip_grad_norm_(list(system.trainable_parameters()), cfg.max_grad_norm).detach().cpu())
        optimizer.step()
        with torch.no_grad():
            log_ratio = replay.log_prob - tensors["logp"]
            ratio = log_ratio.exp()
            kls.append(float(((ratio - 1.0) - log_ratio).mean().cpu()))
            clip_fractions.append(float(((ratio - 1.0).abs() > cfg.clip_coef).float().mean().cpu()))
        policy_losses.append(float(actor_loss.detach().cpu()))
        value_losses.append(float(value_loss.detach().cpu()))
        entropies.append(float(replay.entropy.mean().detach().cpu()))
        grad_norms.append(grad_norm)
    metrics = {
        "policy_loss": float(np.mean(policy_losses)), "value_loss": float(np.mean(value_losses)),
        "entropy": float(np.mean(entropies)), "approx_kl": float(np.mean(kls)),
        "clip_fraction": float(np.mean(clip_fractions)), "grad_norm": float(np.mean(grad_norms)),
    }
    if not all(math.isfinite(value) for value in metrics.values()):
        raise FloatingPointError(f"non-finite temporal PPO metric: {metrics}")
    return metrics


def _save_temporal_runtime(path: Path, system: TATGActorCriticSystem, optimizer: torch.optim.Optimizer, runner: TATGSequenceActorRunner, envs: list[Any], obs: np.ndarray, share_obs: np.ndarray, graph_obs: dict[str, np.ndarray], action_generator: torch.Generator, sampler: FixedStratifiedTopologySampler, episode_counts: list[int], update: int) -> None:
    torch.save({
        "format": "tatg_pilot_runtime_state_v1", "update": int(update),
        "system_state": system.state_dict(), "optimizer_state": optimizer.state_dict(),
        "tatg_actor_runtime_state": runner.rollout_start_state_dict(),
        "environment_states": [env.runtime_state_dict() for env in envs],
        "obs": copy.deepcopy(obs), "share_obs": copy.deepcopy(share_obs), "graph_obs": copy.deepcopy(graph_obs),
        "action_generator_state": action_generator.get_state(), "sampler_state": sampler.state_dict(),
        "episode_counts": [int(value) for value in episode_counts],
        "rng_state": {"python": random.getstate(), "numpy": np.random.get_state(), "torch_cpu": torch.get_rng_state(), "torch_cuda": torch.cuda.get_rng_state_all() if torch.cuda.is_available() else None},
    }, path)


def train_temporal_arm(arm: str, seed: int, output_root: str | Path) -> Path:
    if arm not in TEMPORAL_ARMS:
        raise ValueError("temporal training requires a temporal pilot arm")
    cfg = pilot_config(arm, seed, output_root)
    output = Path(cfg.out_dir)
    if output.exists():
        raise FileExistsError(f"refusing to overwrite pilot trajectory: {output}")
    output.mkdir(parents=True)
    _write_json(output / "run_manifest.json", _manifest(arm, seed, cfg, status="running"))
    set_seed(cfg.seed)
    device = torch.device(cfg.device)
    envs = make_envs(cfg)
    sampler = FixedStratifiedTopologySampler(seed=cfg.fixed_stratified_topology_sampler_seed or seed, num_envs=cfg.num_envs)
    episode_counts = [0 for _ in envs]
    initial_graphs = []
    obs_rows, share_rows = [], []
    for index, env in enumerate(envs):
        sampler.apply(env, sampler.select(0, index, episode_counts[index]))
        obs, share_obs, graph = env.reset()
        obs_rows.append(obs); share_rows.append(share_obs); initial_graphs.append(graph)
    obs, share_obs, graph_obs = np.stack(obs_rows), np.stack(share_rows), stack_graphs(initial_graphs)
    snapshot = _build_snapshot(graph_obs, obs, share_obs, envs[0], cfg).to(device)
    system = TATGActorCriticSystem(snapshot, memory_kind=TEMPORAL_ARMS[arm]).to(device)
    optimizer = make_tatg_optimizer(system, cfg.lr)
    runner = TATGSequenceActorRunner(
        system.temporal_actor,
        torch.as_tensor(graph_obs["relation_adj"], dtype=torch.float32, device=device),
        torch.as_tensor(graph_obs["edge_feat"], dtype=torch.float32, device=device),
    )
    action_generator = torch.Generator(device=device.type).manual_seed(int(seed) + 104729)
    log_path = output / "train_log.csv"
    with log_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=("update", "train_avg_reward", "policy_loss", "value_loss", "entropy", "approx_kl", "clip_fraction", "grad_norm"))
        writer.writeheader()
        for update in range(1, cfg.updates + 1):
            def apply_next_selection(env_index: int, env: Any, *, current_update: int = update) -> None:
                episode_counts[env_index] += 1
                sampler.apply(env, sampler.select(current_update, env_index, episode_counts[env_index]))
            batch = collect_tatg_utr_rollout(
                system, runner, envs, obs, share_obs, graph_obs, rollout_steps=cfg.rollout_steps, device=device,
                action_generator=action_generator, on_before_reset=apply_next_selection,
            )
            metrics = _update_temporal(system, runner, optimizer, batch, cfg, device)
            obs, share_obs, graph_obs = batch["next_obs"], batch["next_share_obs"], batch["next_graph_obs"]
            writer.writerow({"update": update, "train_avg_reward": float(batch["rewards"].mean()), **metrics})
            stream.flush()
            milestone = (cfg.milestone_updates or {}).get(update)
            if milestone is not None:
                torch.save(system.state_dict(), output / f"actor_critic_milestone_{milestone}.pt")
                _save_temporal_runtime(output / f"actor_critic_runtime_state_milestone_{milestone}.pt", system, optimizer, runner, envs, obs, share_obs, graph_obs, action_generator, sampler, episode_counts, update)
    torch.save(system.state_dict(), output / "actor_critic_latest.pt")
    _save_temporal_runtime(output / "actor_critic_runtime_state_latest.pt", system, optimizer, runner, envs, obs, share_obs, graph_obs, action_generator, sampler, episode_counts, cfg.updates)
    _write_json(output / "run_manifest.json", _manifest(arm, seed, cfg, status="completed"))
    return output


def train_one(arm: str, seed: int, output_root: str | Path) -> Path:
    cfg = pilot_config(arm, seed, output_root)
    if arm == BASELINE_ARM:
        output = Path(cfg.out_dir)
        if output.exists():
            raise FileExistsError(f"refusing to overwrite pilot trajectory: {output}")
        output.mkdir(parents=True)
        _write_json(output / "run_manifest.json", _manifest(arm, seed, cfg, status="running"))
        train_ri_gmappo(cfg)
        _write_json(output / "run_manifest.json", _manifest(arm, seed, cfg, status="completed"))
        return output
    return train_temporal_arm(arm, seed, output_root)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("preflight", "train"))
    parser.add_argument("--arm", choices=ALL_ARMS)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if args.command == "preflight":
        print(json.dumps({"protocol": PROTOCOL, "verdict": "TATG_PILOT_P2_RUNNER_IMPLEMENTED", "training_started": False, "evaluation_started": False, "arms": list(ALL_ARMS), "layout": {"num_envs": NUM_ENVS, "rollout_steps": ROLLOUT_STEPS, "updates": UPDATES}}, indent=2))
        return
    if not args.execute:
        raise SystemExit("refusing to train without --execute")
    if args.arm is None or args.seed is None:
        raise SystemExit("train requires --arm and --seed")
    train_one(args.arm, args.seed, args.output_root)


if __name__ == "__main__":
    main()
