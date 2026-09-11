"""Frozen G1 learnability gate for C1 on public Level-Based Foraging.

This runner intentionally trains only the matched, no-posterior MAPPO
baseline.  It is an optional public-benchmark tool and must be run in the
isolated environment described in ``requirements-c1-lbf.txt``.
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from algorithms.m2_commitment_ppo import M2PlainMAPPO
from envs.c1_lbf_masked_adapter import C1LBFConfig, C1MaskedLBFAdapter

PROTOCOL = "C1-LBF-G1-MATCHED-MAPPO-V1"
TRAINING_SEEDS = (91011, 91012, 91013)
OBS_DIM, CRITIC_DIM, ACTION_DIM = 11, 22, 6


@dataclass(frozen=True)
class Settings:
    updates: int = 256
    parallel_envs: int = 16
    rollout_steps: int = 24
    horizon: int = 16
    eval_episodes: int = 128


def seed_all(seed: int) -> torch.Generator:
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    generator = torch.Generator(device="cpu"); generator.manual_seed(seed)
    return generator


def build_env(seed: int, horizon: int) -> C1MaskedLBFAdapter:
    env = C1MaskedLBFAdapter(C1LBFConfig(seed=seed, horizon=horizon))
    env.reset()
    return env


def stack(envs: list[C1MaskedLBFAdapter]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    return (
        np.stack([env.actor_observation() for env in envs]),
        np.stack([env.critic_observation() for env in envs]),
        np.stack([env.action_masks() for env in envs]),
    )


def endpoint(agent: M2PlainMAPPO, seed: int, settings: Settings, *, random_policy: bool = False) -> tuple[list[dict[str, Any]], dict[str, float]]:
    rng = np.random.default_rng(seed)
    rows: list[dict[str, Any]] = []
    agent.eval()
    with torch.no_grad():
        for episode in range(settings.eval_episodes):
            env = build_env(int(rng.integers(0, 2**31 - 1)), settings.horizon)
            team_return = 0.0
            while True:
                actor, _, masks = stack([env])
                if random_policy:
                    actions = np.asarray([
                        rng.choice(np.flatnonzero(masks[0, agent_index]))
                        for agent_index in range(2)
                    ], dtype=np.int64)
                else:
                    dist = agent.action_distribution(
                        torch.as_tensor(actor, dtype=torch.float32),
                        torch.as_tensor(masks, dtype=torch.float32),
                    )
                    actions = torch.argmax(dist.logits, dim=-1).squeeze(0).numpy().astype(np.int64)
                _, _, _, reward, done, info = env.step(actions)
                team_return += float(np.mean(reward))
                if bool(done.all()):
                    rows.append({"episode": episode, "team_return": team_return, **info})
                    break
    agent.train()
    summary = {
        "episodes": float(len(rows)),
        "mean_return": float(np.mean([row["team_return"] for row in rows])),
        "mean_completed_foods": float(np.mean([row["completed_foods"] for row in rows])),
        "full_completion_rate": float(np.mean([row["completed_all"] for row in rows])),
        "timeout_rate": float(np.mean([row["timeout"] for row in rows])),
    }
    return rows, summary


def train(seed: int, out: Path, settings: Settings) -> None:
    generator = seed_all(seed)
    rng = np.random.default_rng(seed + 17)
    envs = [build_env(int(rng.integers(0, 2**31 - 1)), settings.horizon) for _ in range(settings.parallel_envs)]
    agent = M2PlainMAPPO(obs_dim=OBS_DIM, critic_dim=CRITIC_DIM, hidden_dim=96, action_dim=ACTION_DIM)
    optimizer = torch.optim.Adam(agent.parameters(), lr=3e-4)
    fields = ("update", "train_reward", "policy_loss", "value_loss", "validation_completed_foods", "validation_timeout_rate")
    with (out / "train_log.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader()
        for update in range(1, settings.updates + 1):
            records = []
            for _ in range(settings.rollout_steps):
                actor, critic, masks = stack(envs)
                actor_t = torch.as_tensor(actor, dtype=torch.float32)
                critic_t = torch.as_tensor(critic, dtype=torch.float32)
                masks_t = torch.as_tensor(masks, dtype=torch.float32)
                with torch.no_grad():
                    distribution = agent.action_distribution(actor_t, masks_t)
                    actions_t = torch.multinomial(distribution.probs.reshape(-1, ACTION_DIM), 1, generator=generator).reshape(settings.parallel_envs, 2)
                    logp_t = distribution.log_prob(actions_t)
                    # The environment returns a team reward.  The critic is
                    # replicated per actor only to retain the shared MAPPO
                    # interface; use its mean as the team-value bootstrap.
                    values_t = agent.value(critic_t).mean(dim=-1)
                rewards, dones = [], []
                for index, env in enumerate(envs):
                    _, _, _, reward, done, _ = env.step(actions_t[index].numpy())
                    rewards.append(float(np.mean(reward))); dones.append(float(done[0]))
                    if bool(done.all()):
                        envs[index] = build_env(int(rng.integers(0, 2**31 - 1)), settings.horizon)
                records.append((actor, critic, masks, actions_t.numpy(), logp_t.numpy(), values_t.numpy(), np.asarray(rewards), np.asarray(dones)))
            _, next_critic, _ = stack(envs)
            with torch.no_grad():
                bootstrap = agent.value(torch.as_tensor(next_critic, dtype=torch.float32)).mean(dim=-1).numpy()
            advantages = np.zeros((settings.rollout_steps, settings.parallel_envs), dtype=np.float32)
            returns = np.zeros_like(advantages); gae = np.zeros(settings.parallel_envs, dtype=np.float32)
            for index in reversed(range(settings.rollout_steps)):
                following = bootstrap if index == settings.rollout_steps - 1 else records[index + 1][5]
                delta = records[index][6] + 0.99 * (1.0 - records[index][7]) * following - records[index][5]
                gae = delta + 0.99 * 0.95 * (1.0 - records[index][7]) * gae
                advantages[index] = gae; returns[index] = gae + records[index][5]
            flat_actor = torch.as_tensor(np.concatenate([r[0] for r in records]), dtype=torch.float32)
            flat_critic = torch.as_tensor(np.concatenate([r[1] for r in records]), dtype=torch.float32)
            flat_masks = torch.as_tensor(np.concatenate([r[2] for r in records]), dtype=torch.float32)
            flat_actions = torch.as_tensor(np.concatenate([r[3] for r in records]), dtype=torch.int64)
            old_logp = torch.as_tensor(np.concatenate([r[4] for r in records]), dtype=torch.float32)
            actor_adv = torch.as_tensor(np.repeat(advantages[..., None], 2, axis=2).reshape(-1, 2), dtype=torch.float32)
            actor_adv = (actor_adv - actor_adv.mean()) / (actor_adv.std() + 1e-8)
            value_returns = torch.as_tensor(
                np.repeat(returns[..., None], 2, axis=2).reshape(-1), dtype=torch.float32
            )
            policy_loss = value_loss = 0.0
            for _ in range(4):
                distribution = agent.action_distribution(flat_actor, flat_masks)
                ratio = torch.exp(distribution.log_prob(flat_actions) - old_logp)
                actor_loss = -torch.minimum(ratio * actor_adv, torch.clamp(ratio, 0.8, 1.2) * actor_adv).mean()
                critic_loss = torch.nn.functional.mse_loss(agent.value(flat_critic).reshape(-1), value_returns)
                loss = actor_loss + 0.5 * critic_loss - 0.01 * distribution.entropy().mean()
                optimizer.zero_grad(); loss.backward(); torch.nn.utils.clip_grad_norm_(agent.parameters(), 0.5); optimizer.step()
                policy_loss, value_loss = float(actor_loss.detach()), float(critic_loss.detach())
            validation: dict[str, float] = {}
            if update % 32 == 0 or update == settings.updates:
                _, validation = endpoint(agent, 92_000 + seed + update, Settings(eval_episodes=32), random_policy=False)
            writer.writerow({"update": update, "train_reward": float(np.mean([r[6].mean() for r in records])), "policy_loss": policy_loss, "value_loss": value_loss, "validation_completed_foods": validation.get("mean_completed_foods", ""), "validation_timeout_rate": validation.get("timeout_rate", "")}); handle.flush()
    torch.save({"protocol": PROTOCOL, "seed": seed, "settings": settings.__dict__, "state_dict": agent.state_dict()}, out / "endpoint.pt")


def load_agent(path: Path) -> M2PlainMAPPO:
    payload = torch.load(path, map_location="cpu", weights_only=True)
    if payload.get("protocol") != PROTOCOL: raise ValueError("unexpected checkpoint protocol")
    agent = M2PlainMAPPO(obs_dim=OBS_DIM, critic_dim=CRITIC_DIM, hidden_dim=96, action_dim=ACTION_DIM)
    agent.load_state_dict(payload["state_dict"]); return agent


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("train", "evaluate", "random")); parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True); parser.add_argument("--checkpoint", type=Path); parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute: raise SystemExit("refusing to run without --execute")
    if args.seed not in TRAINING_SEEDS and args.mode == "train": raise ValueError("seed not frozen by G1 protocol")
    if args.output.exists(): raise FileExistsError(f"refusing to overwrite {args.output}")
    args.output.mkdir(parents=True)
    settings = Settings()
    if args.mode == "train": train(args.seed, args.output, settings); return
    if args.mode == "random":
        agent = M2PlainMAPPO(obs_dim=OBS_DIM, critic_dim=CRITIC_DIM, hidden_dim=96, action_dim=ACTION_DIM)
        rows, summary = endpoint(agent, args.seed, Settings(eval_episodes=512), random_policy=True)
    else:
        if args.checkpoint is None: raise ValueError("--checkpoint is required for evaluate")
        rows, summary = endpoint(load_agent(args.checkpoint), args.seed, settings, random_policy=False)
    with (args.output / "episode_metrics.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys()); writer.writeheader(); writer.writerows(rows)
    (args.output / "summary.json").write_text(json.dumps({"protocol": PROTOCOL, **summary}, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
