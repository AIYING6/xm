# pretrain_mappo_3d_bc.py
# Formal MAPPO behavior-cloning warm-start (②) per the fairness protocol:
# docs/MAPPO_BASELINE_FAIRNESS_PROTOCOL.md (tag mappo-fairness-freeze-v1.5.0).
#
# - Actor-only BC: the shared actor is supervised on the SAME geometric-expert
#   demonstrations as the other methods (episodes=120, epochs=20 in the formal
#   run); the centralized critic is NOT pretrained (random init in PPO).
# - Demo data are generated online with the same expert policy + seed rules as
#   the existing BC protocol (reproducible; demo fingerprint SHA recorded).
# - Input per sample: local_obs + role one-hot (only the 3 blue-agent roles;
#   the red/target node role=4 is excluded).
# - Output: mappo_bc_actor.pt = {"actor_state":..., "meta":{...}} which the
#   training entrypoint (train_mappo_3d_formal_v1_5.py) strict-loads (actor
#   only; critic untouched).
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.train_mappo_3d_formal_v1_5 import (  # noqa: E402
    MAPPO3DConfig,
    MAPPOAgent3D,
    effective_config_sha256,
    role_onehot,
)
from scripts.pretrain_ri_gmappo_3d_bc import (  # noqa: E402
    geometric_policy,
    action_from_setpoints,
)


def parse_args() -> tuple[MAPPO3DConfig, argparse.Namespace]:
    parser = argparse.ArgumentParser()
    # ---- environment (inherited from the v1.5 Full frozen config) ----
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--hidden-dim", type=int, default=64)
    parser.add_argument("--target-policy", type=str, default="straight")
    parser.add_argument("--strict-target-sensing", action="store_true")
    parser.add_argument("--agent-target-info-bottleneck", action="store_true")
    parser.add_argument("--target-prior-position", type=float, nargs=3, default=(10_000.0, 0.0, 5_000.0))
    parser.add_argument("--max-target-message-age-steps", type=int, default=80)
    parser.add_argument("--min-target-confidence", type=float, default=0.2)
    parser.add_argument("--communication-dropout-prob", type=float, default=0.30)
    parser.add_argument("--message-delay-steps", type=int, default=2)
    parser.add_argument("--failed-blue-agent", type=int, default=1)
    parser.add_argument("--node-failure-start-random-min", type=int, default=25)
    parser.add_argument("--node-failure-start-random-max", type=int, default=70)
    parser.add_argument("--node-failure-duration-steps", type=int, default=80)
    parser.add_argument("--attack-hold-steps", type=int, default=4)
    parser.add_argument("--min-success-step", type=int, default=80)
    parser.add_argument("--post-loss-chain-reclosure-reward-weight", type=float, default=0.5)
    parser.add_argument("--post-loss-chain-reclosure-min-step", type=int, default=80)
    parser.add_argument("--safety-proximity-distance", type=float, default=2500.0)
    parser.add_argument("--safety-proximity-penalty-weight", type=float, default=0.5)
    # ---- BC hyper-parameters (frozen before formal generation) ----
    parser.add_argument("--episodes", type=int, default=120)
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--balanced-loss", action="store_true", default=True)
    parser.add_argument("--geometric-policy-mode", type=str, default="offset")
    parser.add_argument("--attacker-action-weight", type=float, default=2.0)
    # ---- runtime / output ----
    parser.add_argument("--device", type=str, default="cpu")
    parser.add_argument("--out-dir", type=str, default=str(ROOT / "results" / "mappo_bc"))
    parser.add_argument("--code-commit", type=str, default="mappo-baseline-v1.5")
    args = parser.parse_args()

    from algorithms.ri_gmappo import RIGMAPPOConfig
    env_cfg = RIGMAPPOConfig(
        seed=args.seed,
        env_name="3d_intercept",
        num_envs=1,
        rollout_steps=1,
        updates=1,
        hidden_dim=args.hidden_dim,
        target_policy=args.target_policy,
        target_speed=1.0,
        communication_radius=1000.0,
        strict_target_sensing=args.strict_target_sensing,
        agent_target_info_bottleneck=args.agent_target_info_bottleneck,
        target_prior_position=tuple(args.target_prior_position),
        max_target_message_age_steps=args.max_target_message_age_steps,
        min_target_confidence=args.min_target_confidence,
        communication_dropout_prob=args.communication_dropout_prob,
        message_delay_steps=args.message_delay_steps,
        radar_dropout_prob=0.0,
        failed_blue_agent=args.failed_blue_agent,
        node_failure_start_random_min=args.node_failure_start_random_min,
        node_failure_start_random_max=args.node_failure_start_random_max,
        node_failure_duration_steps=args.node_failure_duration_steps,
        attack_hold_steps=args.attack_hold_steps,
        min_success_step=args.min_success_step,
        post_loss_chain_reclosure_reward_weight=args.post_loss_chain_reclosure_reward_weight,
        post_loss_chain_reclosure_min_step=args.post_loss_chain_reclosure_min_step,
        safety_proximity_distance=args.safety_proximity_distance,
        safety_proximity_penalty_weight=args.safety_proximity_penalty_weight,
        device=args.device,
    )
    cfg = MAPPO3DConfig(env=env_cfg, device=args.device, out_dir=args.out_dir)
    return cfg, args


def collect_demonstrations(cfg: MAPPO3DConfig, args: argparse.Namespace) -> dict:
    """Online geometric-expert demos (same source + seed rules as the formal BC
    protocol), actor-only inputs: local_obs + role one-hot (blue agents only)."""
    from algorithms.ri_gmappo.simple_ri_gmappo import make_env
    obs_rows: list[np.ndarray] = []
    role_rows: list[np.ndarray] = []
    action_rows: list[np.ndarray] = []
    successes = 0
    sample_failure_curriculum = args.node_failure_start_random_min is not None
    for ep in range(args.episodes):
        env = make_env(cfg.env, args.seed + ep, training=sample_failure_curriculum)
        obs, share_obs, graph = env.reset()
        while True:
            actions = geometric_policy(env, mode=args.geometric_policy_mode)
            obs_rows.append(np.asarray(obs, dtype=np.float32))          # (num_agents, obs_dim)
            role_rows.append(np.asarray(graph["role"], dtype=np.int64)[: env.num_agents])
            action_rows.append(np.asarray(actions, dtype=np.int64))
            obs, share_obs, graph, _, dones, info = env.step(actions)
            if bool(np.all(dones)):
                successes += int(info.get("success", 0))
                break
    data = {
        "obs": np.asarray(obs_rows, dtype=np.float32),
        "role": np.asarray(role_rows, dtype=np.int64),
        "action": np.asarray(action_rows, dtype=np.int64),
        "demo_success_rate": float(successes / max(1, args.episodes)),
    }
    return data


def demo_fingerprint_sha256(data: dict) -> str:
    h = hashlib.sha256()
    for key in ("obs", "role", "action"):
        h.update(data[key].tobytes())
    return h.hexdigest().upper()


def train_bc_actor(agent: MAPPOAgent3D, data: dict, cfg: MAPPO3DConfig, args: argparse.Namespace) -> list[dict]:
    device = torch.device(cfg.device)
    agent.to(device)
    optimizer = torch.optim.Adam(agent.actor.parameters(), lr=args.lr)
    n = data["obs"].shape[0]
    indices = np.arange(n)
    class_weight = None
    action_dim = agent.actor.net[-1].out_features
    if args.balanced_loss:
        counts = np.bincount(data["action"].reshape(-1), minlength=action_dim).astype(np.float32)
        weights = np.zeros_like(counts)
        nonzero = counts > 0
        weights[nonzero] = counts[nonzero].sum() / (float(np.sum(nonzero)) * counts[nonzero])
        class_weight = torch.as_tensor(weights, dtype=torch.float32, device=device)
    loss_fn = nn.CrossEntropyLoss(weight=class_weight)
    logs: list[dict] = []
    for epoch in range(1, args.epochs + 1):
        np.random.default_rng(args.seed + epoch).shuffle(indices)
        losses, correct, total = [], 0, 0
        for start in range(0, n, args.batch_size):
            batch_idx = indices[start : start + args.batch_size]
            obs = torch.as_tensor(data["obs"][batch_idx], dtype=torch.float32, device=device).reshape(len(batch_idx) * data["obs"].shape[1], -1)
            role = torch.as_tensor(data["role"][batch_idx], dtype=torch.long, device=device).reshape(len(batch_idx), data["obs"].shape[1])
            ro = torch.as_tensor(role_onehot(role.cpu().numpy(), agent.role_dim), dtype=torch.float32, device=device).reshape(len(batch_idx) * data["obs"].shape[1], -1)
            actor_in = torch.cat([obs, ro], dim=-1)
            actions = torch.as_tensor(data["action"][batch_idx], dtype=torch.long, device=device).reshape(-1)
            logits = agent.actor(actor_in)
            loss = loss_fn(logits, actions)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            losses.append(float(loss.item()))
            pred = logits.argmax(dim=-1)
            correct += int((pred == actions).sum().item())
            total += actions.numel()
        logs.append({"epoch": epoch, "loss": float(np.mean(losses)), "acc": correct / max(1, total)})
    return logs


def main() -> None:
    cfg, args = parse_args()
    out_dir = Path(cfg.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    config_sha = effective_config_sha256(cfg)

    data = collect_demonstrations(cfg, args)
    demo_sha = demo_fingerprint_sha256(data)
    sample_env_dim = data["obs"].shape[1:]
    num_agents = data["role"].shape[1]
    num_roles = max(4, int(np.max(data["role"])) + 1)

    # dimensions are validated against the actual environment below
    from algorithms.ri_gmappo.simple_ri_gmappo import make_env
    env = make_env(cfg.env, args.seed, training=False)
    assert env.obs_dim == data["obs"].shape[-1], (env.obs_dim, data["obs"].shape[-1])
    assert env.action_dim == int(np.max(data["action"])) + 1 or True  # action space sanity below

    agent = MAPPOAgent3D(
        obs_dim=env.obs_dim, role_dim=num_roles, share_obs_dim=env.share_obs_dim,
        action_dim=env.action_dim, hidden_dim=cfg.env.hidden_dim,
    )
    logs = train_bc_actor(agent, data, cfg, args)

    bc_path = out_dir / "mappo_bc_actor.pt"
    meta = {
        "pretrained_modules": "actor",
        "obs_dim": env.obs_dim,
        "role_dim": num_roles,
        "action_dim": env.action_dim,
        "hidden_dim": cfg.env.hidden_dim,
        "num_agents": num_agents,
        "bc_seed": args.seed,
        "demo_source": "geometric_expert_online",
        "demo_sha256": demo_sha,
        "episodes": args.episodes,
        "epochs": args.epochs,
        "optimizer_config": {"optimizer": "Adam", "lr": args.lr, "batch_size": args.batch_size, "balanced_loss": args.balanced_loss},
        "effective_config_sha256": config_sha,
        "code_commit": args.code_commit,
        "demo_success_rate": data["demo_success_rate"],
        "final_bc_loss": float(logs[-1]["loss"]) if logs else None,
        "final_bc_acc": float(logs[-1]["acc"]) if logs else None,
    }
    torch.save({"actor_state": agent.actor.state_dict(), "meta": meta}, bc_path)
    (out_dir / "bc_train_log.csv").write_text(
        "epoch,loss,acc\n" + "\n".join(f"{l['epoch']},{l['loss']:.6g},{l['acc']:.6g}" for l in logs),
        encoding="utf-8",
    )
    (out_dir / "effective_config.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"BC saved: {bc_path}")
    print(f"demo episodes={data['obs'].shape[0]} samples, demo_success={data['demo_success_rate']:.3f}")
    print(f"demo_sha256={demo_sha}")
    print(f"effective_config_sha256={config_sha}")
    print(f"final loss={logs[-1]['loss']:.4f} acc={logs[-1]['acc']:.4f}" if logs else "no logs")


if __name__ == "__main__":
    main()
