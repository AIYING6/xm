# train_mappo_3d_formal_v1_5.py
# Formal MAPPO baseline entrypoint for v1.5 (fairness protocol:
# docs/MAPPO_BASELINE_FAIRNESS_PROTOCOL.md, tag mappo-fairness-freeze-v1.5.0).
#
# - Same 3D strict-sensing environment as v1.5 Full (env params inherited via
#   RIGMAPPOConfig + make_envs; NO manual re-typing of environment defaults).
# - Shared actor + role one-hot (identity/role observation ONLY; no failure
#   ground-truth, no graph relations, no EA-RG modules).
# - Centralized critic over share_obs.
# - Budget aligned with Full: num_envs 8 x rollout_steps 128 x 977 updates.
# - BC warm-start via --init-checkpoint (STRICT load; missing/extra keys fail).
# - Snapshots 100..977 + durable training_state (update/optimizers/RNG/
#   env_steps/config-SHA/commit/BC-SHA) + exact resume.
from __future__ import annotations

import argparse
import csv
import hashlib
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.distributions import Categorical

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo import RIGMAPPOConfig  # noqa: E402
from algorithms.ri_gmappo.simple_ri_gmappo import make_envs, set_seed  # noqa: E402


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

@dataclass
class MAPPO3DConfig:
    # environment (mirrors RIGMAPPOConfig env fields; make_envs consumes it)
    env: RIGMAPPOConfig
    # MAPPO canonical hyper-parameters (frozen before formal training)
    actor_lr: float = 3e-4
    critic_lr: float = 3e-4
    gamma: float = 0.99
    gae_lambda: float = 0.95
    clip_coef: float = 0.2
    entropy_coef: float = 0.01
    value_coef: float = 0.5
    max_grad_norm: float = 0.5
    target_kl: float | None = None
    ppo_epochs: int = 4
    minibatch_size: int = 512
    # evaluation during training (monitoring only; formal eval uses 641939)
    eval_interval: int = 100
    eval_episodes: int = 5
    eval_base_seed: int | None = None
    # checkpointing / init / resume
    save_interval: int = 100
    save_snapshots: bool = True
    init_checkpoint: str | None = None
    resume: str | None = None
    update_offset: int = 0
    append_log: bool = False
    # provenance
    code_commit: str = "mappo-baseline-v1.5"  # filled at freeze
    # runtime
    device: str = "cpu"
    out_dir: str = "results/mappo_3d"


class MLP(nn.Module):
    def __init__(self, in_dim: int, out_dim: int, hidden_dim: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, out_dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class MAPPOAgent3D(nn.Module):
    """Shared actor + role one-hot + centralized critic.

    State-dict keys are ONLY 'actor.*' and 'critic.*' -> provably no graph /
    gate / EA-RG modules (asserted in the effective-config audit).
    """

    def __init__(self, obs_dim: int, role_dim: int, share_obs_dim: int, action_dim: int, hidden_dim: int):
        super().__init__()
        self.actor = MLP(obs_dim + role_dim, action_dim, hidden_dim)
        self.critic = MLP(share_obs_dim, 1, hidden_dim)
        self.role_dim = role_dim

    def get_action_and_value(self, obs, share_obs, action=None, deterministic=False):
        logits = self.actor(obs)
        dist = Categorical(logits=logits)
        if action is None:
            action = torch.argmax(logits, dim=-1) if deterministic else dist.sample()
        log_prob = dist.log_prob(action)
        entropy = dist.entropy()
        value = self.critic(share_obs).squeeze(-1)
        return action, log_prob, entropy, value


# ---------------------------------------------------------------------------
# checkpoint persistence (MAPPO-specific durable state)
# ---------------------------------------------------------------------------

def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def save_mappo_state(
    path: Path,
    agent: nn.Module,
    actor_opt: optim.Optimizer,
    critic_opt: optim.Optimizer,
    update: int,
    env_steps: int,
    seed: int,
    effective_config_sha256: str,
    code_commit: str,
    bc_checkpoint: str | None,
    bc_sha256: str | None,
    rng_state: dict,
) -> None:
    payload = {
        "model_state": agent.state_dict(),
        "actor_optimizer_state": actor_opt.state_dict(),
        "critic_optimizer_state": critic_opt.state_dict(),
        "update": int(update),
        "env_steps": int(env_steps),
        "seed": int(seed),
        "effective_config_sha256": effective_config_sha256,
        "code_commit": code_commit,
        "bc_checkpoint": bc_checkpoint,
        "bc_sha256": bc_sha256,
        "rng_state": rng_state,
    }
    torch.save(payload, path)


def load_mappo_state(path: Path, agent: nn.Module, actor_opt: optim.Optimizer, critic_opt: optim.Optimizer, device: torch.device) -> dict:
    payload = torch.load(path, map_location=device, weights_only=False)
    # STRICT model load: missing/extra keys must fail (BC & resume integrity)
    agent.load_state_dict(payload["model_state"])
    actor_opt.load_state_dict(payload["actor_optimizer_state"])
    critic_opt.load_state_dict(payload["critic_optimizer_state"])
    return payload


def capture_rng_state() -> dict:
    return {
        "python": random.getstate(),
        "numpy": np.random.get_state(),
        "torch": torch.get_rng_state().clone(),
        "cuda": torch.cuda.get_rng_state_all() if torch.cuda.is_available() else [],
    }


def restore_rng_state(state: dict) -> None:
    random.setstate(state["python"])
    np.random.set_state(state["numpy"])
    torch.set_rng_state(state["torch"])
    if torch.cuda.is_available() and state.get("cuda"):
        torch.cuda.set_rng_state_all(state["cuda"])


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> MAPPO3DConfig:
    parser = argparse.ArgumentParser()
    # ---- environment (inherited from the v1.5 Full frozen config) ----
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--num-envs", type=int, default=8)
    parser.add_argument("--rollout-steps", type=int, default=128)
    parser.add_argument("--updates", type=int, default=977)
    parser.add_argument("--hidden-dim", type=int, default=64)
    parser.add_argument("--target-policy", type=str, default="straight")
    parser.add_argument("--strict-target-sensing", action="store_true")
    parser.add_argument("--agent-target-info-bottleneck", action="store_true")
    parser.add_argument("--target-prior-position", type=float, nargs=3, default=(10_000.0, 0.0, 5_000.0))
    parser.add_argument("--max-target-message-age-steps", type=int, default=80)
    parser.add_argument("--min-target-confidence", type=float, default=0.2)
    parser.add_argument("--communication-dropout-prob", type=float, default=0.30)
    parser.add_argument("--message-delay-steps", type=int, default=2)
    parser.add_argument("--radar-dropout-prob", type=float, default=0.0)
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
    # ---- MAPPO canonical hyper-parameters (frozen) ----
    parser.add_argument("--actor-lr", type=float, default=3e-4)
    parser.add_argument("--critic-lr", type=float, default=3e-4)
    parser.add_argument("--gamma", type=float, default=0.99)
    parser.add_argument("--gae-lambda", type=float, default=0.95)
    parser.add_argument("--clip-coef", type=float, default=0.2)
    parser.add_argument("--entropy-coef", type=float, default=0.01)
    parser.add_argument("--value-coef", type=float, default=0.5)
    parser.add_argument("--max-grad-norm", type=float, default=0.5)
    parser.add_argument("--target-kl", type=float, default=None)
    parser.add_argument("--ppo-epochs", type=int, default=4)
    parser.add_argument("--minibatch-size", type=int, default=512)
    parser.add_argument("--eval-interval", type=int, default=100)
    parser.add_argument("--eval-episodes", type=int, default=5)
    parser.add_argument("--eval-base-seed", type=int, default=None)
    # ---- runtime / checkpoint ----
    parser.add_argument("--device", type=str, default="cpu")
    parser.add_argument("--out-dir", type=str, default=str(ROOT / "results" / "mappo_3d"))
    parser.add_argument("--save-interval", type=int, default=100)
    parser.add_argument("--save-snapshots", action="store_true")
    parser.add_argument("--init-checkpoint", type=str, default=None)
    parser.add_argument("--resume", type=str, default=None)
    parser.add_argument("--update-offset", type=int, default=0)
    parser.add_argument("--append-log", action="store_true")
    parser.add_argument("--code-commit", type=str, default="mappo-baseline-v1.5")
    args = parser.parse_args()

    env_cfg = RIGMAPPOConfig(
        seed=args.seed,
        env_name="3d_intercept",
        num_envs=args.num_envs,
        rollout_steps=args.rollout_steps,
        updates=args.updates,
        hidden_dim=args.hidden_dim,
        target_policy=args.target_policy,
        target_speed=1.0,  # unused for 3d straight policy
        communication_radius=1000.0,
        strict_target_sensing=args.strict_target_sensing,
        agent_target_info_bottleneck=args.agent_target_info_bottleneck,
        target_prior_position=tuple(args.target_prior_position),
        max_target_message_age_steps=args.max_target_message_age_steps,
        min_target_confidence=args.min_target_confidence,
        communication_dropout_prob=args.communication_dropout_prob,
        message_delay_steps=args.message_delay_steps,
        radar_dropout_prob=args.radar_dropout_prob,
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
    return MAPPO3DConfig(
        env=env_cfg,
        actor_lr=args.actor_lr,
        critic_lr=args.critic_lr,
        gamma=args.gamma,
        gae_lambda=args.gae_lambda,
        clip_coef=args.clip_coef,
        entropy_coef=args.entropy_coef,
        value_coef=args.value_coef,
        max_grad_norm=args.max_grad_norm,
        target_kl=args.target_kl,
        ppo_epochs=args.ppo_epochs,
        minibatch_size=args.minibatch_size,
        eval_interval=args.eval_interval,
        eval_episodes=args.eval_episodes,
        eval_base_seed=args.eval_base_seed,
        save_interval=args.save_interval,
        save_snapshots=args.save_snapshots,
        init_checkpoint=args.init_checkpoint,
        resume=args.resume,
        update_offset=args.update_offset,
        append_log=args.append_log,
        code_commit=args.code_commit,
        device=args.device,
        out_dir=args.out_dir,
    )


def snapshot_nodes(save_interval: int, total_updates: int) -> list[int]:
    """Checkpoint updates persisted as named snapshots (e.g. 100,200,...,900,977)."""
    nodes = [u for u in range(save_interval, total_updates + 1, save_interval)]
    if not nodes or nodes[-1] != total_updates:
        nodes.append(total_updates)
    return nodes


def effective_config_sha256(cfg: MAPPO3DConfig) -> str:
    # updates is a run-control parameter (the resume target differs from the
    # initial target); it must NOT enter the frozen config identity. num_envs /
    # rollout_steps / hidden_dim (sampling budget + architecture) DO.
    import dataclasses
    env = dataclasses.asdict(cfg.env)
    env.pop("updates", None)
    payload = {
        "env": env,
        "actor_lr": cfg.actor_lr, "critic_lr": cfg.critic_lr, "gamma": cfg.gamma,
        "gae_lambda": cfg.gae_lambda, "clip_coef": cfg.clip_coef, "entropy_coef": cfg.entropy_coef,
        "value_coef": cfg.value_coef, "max_grad_norm": cfg.max_grad_norm, "target_kl": cfg.target_kl,
        "ppo_epochs": cfg.ppo_epochs, "minibatch_size": cfg.minibatch_size,
        "num_envs": cfg.env.num_envs, "rollout_steps": cfg.env.rollout_steps,
        "hidden_dim": cfg.env.hidden_dim,
    }
    return hashlib.sha256(repr(payload).encode()).hexdigest().upper()


# ---------------------------------------------------------------------------
# rollout / GAE / update (canonical MAPPO on the 3D env)
# ---------------------------------------------------------------------------

def role_onehot(role: np.ndarray, num_roles: int) -> np.ndarray:
    """role: (num_envs, num_agents) -> one-hot (num_envs, num_agents, num_roles)."""
    r = np.asarray(role, dtype=np.int64)
    out = np.zeros((*r.shape, num_roles), dtype=np.float32)
    out[np.arange(r.shape[0])[:, None], np.arange(r.shape[1])[None, :], r] = 1.0
    return out


def collect_rollout(agent, envs, obs, share_obs, role, cfg: MAPPO3DConfig, device) -> dict:
    num_agents = envs[0].num_agents
    num_roles = agent.role_dim
    obs_buf, share_buf, role_buf, action_buf, logp_buf, reward_buf, done_buf, value_buf = [], [], [], [], [], [], [], []
    for _ in range(cfg.env.rollout_steps):
        ro = role_onehot(role, num_roles)
        flat_obs = torch.as_tensor(obs, dtype=torch.float32, device=device).reshape(cfg.env.num_envs * num_agents, -1)
        flat_ro = torch.as_tensor(ro, dtype=torch.float32, device=device).reshape(cfg.env.num_envs * num_agents, -1)
        flat_share = torch.as_tensor(share_obs, dtype=torch.float32, device=device).reshape(cfg.env.num_envs * num_agents, -1)
        actor_in = torch.cat([flat_obs, flat_ro], dim=-1)
        with torch.no_grad():
            actions, logp, _, values = agent.get_action_and_value(actor_in, flat_share)
        actions_np = actions.cpu().numpy().reshape(cfg.env.num_envs, num_agents)
        values_np = values.cpu().numpy().reshape(cfg.env.num_envs, num_agents)
        logp_np = logp.cpu().numpy().reshape(cfg.env.num_envs, num_agents)
        next_obs, next_share, next_role, rewards, dones = [], [], [], [], []
        for e, env in enumerate(envs):
            o, s, g, r, d, _ = env.step(actions_np[e])
            if np.all(d):
                o, s, g = env.reset()
            next_obs.append(o)
            next_share.append(s)
            next_role.append(np.asarray(g["role"], dtype=np.int64)[: env.num_agents])
            # env step returns rewards/dones shaped (num_agents, 1); flatten
            rewards.append(np.asarray(r, dtype=np.float32).reshape(env.num_agents))
            dones.append(np.asarray(d, dtype=np.float32).reshape(env.num_agents))
        obs_buf.append(obs.copy())
        share_buf.append(share_obs.copy())
        role_buf.append(role.copy())
        action_buf.append(actions_np.copy())
        logp_buf.append(logp_np.copy())
        value_buf.append(values_np.copy())
        reward_buf.append(np.stack(rewards))
        done_buf.append(np.stack(dones))
        obs = np.stack(next_obs)
        share_obs = np.stack(next_share)
        role = np.stack(next_role)
    with torch.no_grad():
        next_share_flat = torch.as_tensor(share_obs, dtype=torch.float32, device=device).reshape(cfg.env.num_envs * num_agents, -1)
        next_values = agent.critic(next_share_flat).squeeze(-1).cpu().numpy().reshape(cfg.env.num_envs, num_agents)
    rewards_np = np.asarray(reward_buf, dtype=np.float32)
    dones_np = np.asarray(done_buf, dtype=np.float32)
    values_np = np.asarray(value_buf, dtype=np.float32)
    advantages, returns = compute_gae(rewards_np, dones_np, values_np, next_values, cfg.gamma, cfg.gae_lambda)
    return {
        "obs": np.asarray(obs_buf, dtype=np.float32),
        "share_obs": np.asarray(share_buf, dtype=np.float32),
        "role": np.asarray(role_buf, dtype=np.int64),
        "actions": np.asarray(action_buf, dtype=np.int64),
        "logp": np.asarray(logp_buf, dtype=np.float32),
        "values": values_np,
        "rewards": rewards_np,
        "dones": dones_np,
        "advantages": advantages,
        "returns": returns,
        "next_obs": obs,
        "next_share_obs": share_obs,
        "next_role": role,
    }


def compute_gae(rewards, dones, values, next_values, gamma, gae_lambda):
    advantages = np.zeros_like(rewards, dtype=np.float32)
    last_gae = np.zeros_like(next_values, dtype=np.float32)
    for t in reversed(range(rewards.shape[0])):
        next_nonterminal = 1.0 - dones[t]
        next_value = next_values if t == rewards.shape[0] - 1 else values[t + 1]
        delta = rewards[t] + gamma * next_value * next_nonterminal - values[t]
        last_gae = delta + gamma * gae_lambda * next_nonterminal * last_gae
        advantages[t] = last_gae
    returns = advantages + values
    return advantages, returns


def update_policy(agent, actor_opt, critic_opt, batch, cfg: MAPPO3DConfig, device) -> dict:
    num_agents = batch["actions"].shape[2]
    num_samples = cfg.env.rollout_steps * cfg.env.num_envs * num_agents
    num_roles = agent.role_dim
    obs = torch.as_tensor(batch["obs"].reshape(num_samples, -1), dtype=torch.float32, device=device)
    role = role_onehot(batch["role"].reshape(cfg.env.rollout_steps, cfg.env.num_envs, num_agents), num_roles)
    ro = torch.as_tensor(role.reshape(num_samples, -1), dtype=torch.float32, device=device)
    share_obs = torch.as_tensor(batch["share_obs"].reshape(num_samples, -1), dtype=torch.float32, device=device)
    actions = torch.as_tensor(batch["actions"].reshape(num_samples), dtype=torch.long, device=device)
    old_logp = torch.as_tensor(batch["logp"].reshape(num_samples), dtype=torch.float32, device=device)
    advantages = torch.as_tensor(batch["advantages"].reshape(num_samples), dtype=torch.float32, device=device)
    returns = torch.as_tensor(batch["returns"].reshape(num_samples), dtype=torch.float32, device=device)
    advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)
    actor_in = torch.cat([obs, ro], dim=-1)

    losses, policy_losses, value_losses, entropies, kls, clip_fracs, grad_norms = [], [], [], [], [], [], []
    indices = np.arange(num_samples)
    for _ in range(cfg.ppo_epochs):
        np.random.shuffle(indices)
        for start in range(0, num_samples, cfg.minibatch_size):
            mb = indices[start : start + cfg.minibatch_size]
            _, new_logp, entropy, values = agent.get_action_and_value(actor_in[mb], share_obs[mb], actions[mb])
            log_ratio = new_logp - old_logp[mb]
            ratio = log_ratio.exp()
            pg_loss1 = -advantages[mb] * ratio
            pg_loss2 = -advantages[mb] * torch.clamp(ratio, 1.0 - cfg.clip_coef, 1.0 + cfg.clip_coef)
            policy_loss = torch.max(pg_loss1, pg_loss2).mean()
            value_loss = 0.5 * (returns[mb] - values).pow(2).mean()
            entropy_loss = entropy.mean()
            loss = policy_loss + cfg.value_coef * value_loss - cfg.entropy_coef * entropy_loss
            actor_opt.zero_grad()
            critic_opt.zero_grad()
            loss.backward()
            # record the real total gradient norm (returned by clip_grad_norm_)
            grad_norm = float(nn.utils.clip_grad_norm_(agent.parameters(), cfg.max_grad_norm).item())
            actor_opt.step()
            critic_opt.step()
            with torch.no_grad():
                approx_kl = ((ratio - 1.0) - log_ratio).mean().item()
                clip_fraction = (torch.abs(ratio - 1.0) > cfg.clip_coef).float().mean().item()
            losses.append(float(loss.detach().cpu()))
            policy_losses.append(float(policy_loss.detach().cpu()))
            value_losses.append(float(value_loss.detach().cpu()))
            entropies.append(float(entropy_loss.detach().cpu()))
            kls.append(approx_kl)
            clip_fracs.append(clip_fraction)
            grad_norms.append(grad_norm)
    return {
        "loss": float(np.mean(losses)),
        "policy_loss": float(np.mean(policy_losses)),
        "value_loss": float(np.mean(value_losses)),
        "entropy": float(np.mean(entropies)),
        "approx_kl": float(np.mean(kls)),
        "clip_fraction": float(np.mean(clip_fracs)),
        "grad_norm": float(np.mean(grad_norms)),
    }


def eval_policy(agent, cfg: MAPPO3DConfig, base_seed: int) -> dict:
    device = torch.device(cfg.device)
    num_agents = None
    records = []
    agent.eval()
    with torch.no_grad():
        for ep in range(cfg.eval_episodes):
            from algorithms.ri_gmappo.simple_ri_gmappo import make_env
            env = make_env(cfg.env, base_seed + ep, training=False)
            obs, share_obs, graph = env.reset()
            num_agents = env.num_agents
            role = np.asarray(graph["role"], dtype=np.int64)[: num_agents]
            num_roles = agent.role_dim
            for _ in range(env.config.max_steps):
                ro = role_onehot(role.reshape(1, -1), num_roles).reshape(1, num_agents, -1)
                obs_t = torch.as_tensor(obs, dtype=torch.float32, device=device).reshape(1, num_agents, -1)
                ro_t = torch.as_tensor(ro, dtype=torch.float32, device=device).reshape(1, num_agents, -1)
                share_t = torch.as_tensor(share_obs, dtype=torch.float32, device=device).reshape(1, num_agents, -1)
                actions, _, _, _ = agent.get_action_and_value(torch.cat([obs_t, ro_t], dim=-1).reshape(1 * num_agents, -1), share_t.reshape(1 * num_agents, -1), deterministic=True)
                obs, share_obs, graph, _, dones, info = env.step(actions.cpu().numpy())
                if np.all(dones):
                    records.append(info)
                    break
    agent.train()
    if not records:
        return {"eval_success_rate": 0.0, "eval_collision_rate": 0.0, "eval_timeout_rate": 0.0,
                "eval_avg_steps": 0.0, "eval_avg_distance": 0.0}
    return {
        "eval_success_rate": float(np.mean([r["success"] for r in records])),
        "eval_collision_rate": float(np.mean([r["collision"] for r in records])),
        "eval_timeout_rate": float(np.mean([r["timeout"] for r in records])),
        "eval_avg_steps": float(np.mean([r["step"] for r in records])),
        "eval_avg_distance": float(np.mean([r["mean_range"] for r in records])),
    }


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def strict_bc_load(agent: nn.Module, path: str, device: torch.device) -> str:
    """STRICT BC load: missing or extra keys raise (no silent skip)."""
    payload = torch.load(path, map_location=device, weights_only=False)
    model_state = payload.get("model_state", payload)
    if not isinstance(model_state, dict):
        raise ValueError(f"BC checkpoint {path} has no model state")
    current = agent.state_dict()
    missing = [k for k in model_state if k not in current]
    extra = [k for k in current if k not in model_state]
    wrong_shape = [k for k in model_state if k in current and current[k].shape != model_state[k].shape]
    if missing or extra or wrong_shape:
        raise RuntimeError(
            f"STRICT BC load FAILED: missing={missing} extra={extra} wrong_shape={wrong_shape}"
        )
    agent.load_state_dict(model_state)
    return _sha256(Path(path))


def truncate_log_to(log_path: Path, update: int) -> None:
    """Keep log rows 1..update; safe truncation of rows ahead of durable state."""
    if not log_path.exists():
        return
    with log_path.open("r", encoding="utf-8", newline="") as f:
        lines = f.readlines()
    if len(lines) < 2:
        return
    header = lines[0]
    rows = []
    for line in lines[1:]:
        if line.strip():
            upd = line.split(",")[0]
            if upd.isdigit() and int(upd) <= update:
                rows.append(line)
    with log_path.open("w", encoding="utf-8", newline="") as f:
        f.write(header)
        f.writelines(rows)


def train(cfg: MAPPO3DConfig) -> Path:
    set_seed(cfg.env.seed)
    device = torch.device(cfg.device)
    out_dir = Path(cfg.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    effective_sha = effective_config_sha256(cfg)
    bc_sha: str | None = None

    envs = make_envs(cfg.env)
    obs_list, share_list, role_list = [], [], []
    for env in envs:
        obs, share_obs, graph = env.reset()
        obs_list.append(obs)
        share_list.append(share_obs)
        # graph["role"] covers n_blue+n_red nodes; actor acts only on n_blue agents
        role_list.append(np.asarray(graph["role"], dtype=np.int64)[: env.num_agents])
    obs = np.stack(obs_list)
    share_obs = np.stack(share_list)
    role = np.stack(role_list)
    sample_env = envs[0]
    num_roles = max(4, int(np.max(role)) + 1)

    agent = MAPPOAgent3D(
        obs_dim=sample_env.obs_dim,
        role_dim=num_roles,
        share_obs_dim=sample_env.share_obs_dim,
        action_dim=sample_env.action_dim,
        hidden_dim=cfg.env.hidden_dim,
    ).to(device)
    actor_opt = optim.Adam(agent.actor.parameters(), lr=cfg.actor_lr, eps=1e-5)
    critic_opt = optim.Adam(agent.critic.parameters(), lr=cfg.critic_lr, eps=1e-5)

    start_update = 0
    env_steps = 0
    if cfg.init_checkpoint:
        bc_sha = strict_bc_load(agent, cfg.init_checkpoint, device)
        print(f"BC loaded strictly from {cfg.init_checkpoint} (sha {bc_sha})", flush=True)
    if cfg.resume:
        state = load_mappo_state(Path(cfg.resume), agent, actor_opt, critic_opt, device)
        start_update = int(state["update"])
        env_steps = int(state.get("env_steps", 0))
        restore_rng_state(state["rng_state"])
        print(f"resumed from {cfg.resume}: update={start_update} env_steps={env_steps}", flush=True)
        # durable state is authoritative: truncate any log rows ahead of it
        truncate_log_to(out_dir / "train_log.csv", start_update)

    log_path = out_dir / "train_log.csv"
    fieldnames = ["update", "loss", "policy_loss", "value_loss", "entropy", "approx_kl",
                  "clip_fraction", "grad_norm", "train_avg_reward", "eval_success_rate",
                  "eval_collision_rate", "eval_timeout_rate", "eval_avg_steps", "eval_avg_distance"]
    write_header = not (cfg.append_log and log_path.exists())
    mode = "a" if cfg.append_log else "w"
    with log_path.open(mode, newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        f.flush()
        for local_update in range(1, cfg.env.updates + 1):
            update = cfg.update_offset + local_update
            if update <= start_update:
                continue
            batch = collect_rollout(agent, envs, obs, share_obs, role, cfg, device)
            obs, share_obs, role = batch["next_obs"], batch["next_share_obs"], batch["next_role"]
            env_steps += cfg.env.num_envs * cfg.env.rollout_steps
            train_info = update_policy(agent, actor_opt, critic_opt, batch, cfg, device)
            row = {"update": update, **train_info, "train_avg_reward": float(batch["rewards"].mean())}
            if update % cfg.eval_interval == 0 or update == 1:
                eval_base_seed = cfg.eval_base_seed if cfg.eval_base_seed is not None else 10_000 + update * 100
                row.update(eval_policy(agent, cfg, eval_base_seed))
            else:
                for k in ("eval_success_rate", "eval_collision_rate", "eval_timeout_rate", "eval_avg_steps", "eval_avg_distance"):
                    row[k] = ""
            writer.writerow(row)
            f.flush()
            if update in snapshot_nodes(cfg.save_interval, cfg.env.updates):
                rng = capture_rng_state()
                save_mappo_state(
                    out_dir / "actor_critic_training_state_latest.pt", agent, actor_opt, critic_opt,
                    update, env_steps, cfg.env.seed, effective_sha, cfg.code_commit,
                    cfg.init_checkpoint, bc_sha, rng,
                )
                torch.save(agent.state_dict(), out_dir / "actor_critic_latest.pt")
                if cfg.save_snapshots:
                    torch.save(agent.state_dict(), out_dir / f"actor_critic_update_{update:04d}.pt")
                    save_mappo_state(
                        out_dir / f"actor_critic_training_state_update_{update:04d}.pt", agent, actor_opt, critic_opt,
                        update, env_steps, cfg.env.seed, effective_sha, cfg.code_commit,
                        cfg.init_checkpoint, bc_sha, rng,
                    )
    return log_path


def main() -> None:
    cfg = parse_args()
    print(f"effective config sha256: {effective_config_sha256(cfg)}", flush=True)
    print(f"budget: {cfg.env.num_envs} envs x {cfg.env.rollout_steps} steps x {cfg.env.updates} updates "
          f"= {cfg.env.num_envs * cfg.env.rollout_steps * cfg.env.updates} env steps", flush=True)
    log_path = train(cfg)
    print(f"training log: {log_path}")


if __name__ == "__main__":
    main()
