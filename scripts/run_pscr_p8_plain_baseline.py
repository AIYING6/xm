"""Minimal fixed-capacity MAPPO learnability baseline for frozen P8.

This runner is intentionally a *task gate*, not a comparison with a new
method.  It uses only the public P8 actor observations and the matching
non-privileged centralized critic state.  A successful run establishes that
the physical task is neither globally infeasible nor trivially saturated.
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from pathlib import Path
from typing import Any

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from algorithms.pscr_p8_plain_mappo import PSCRP8PlainMAPPO
from envs.pscr_search_prefix_env import P8SearchPrefixConfig, PSCRSearchPrefixEnv


PROTOCOL = "PSCR-P8-PLAIN-MAPPO-LEARNABILITY-V1"
RELIABILITY_BANDS = (0.1, 0.9)


def seed_all(seed: int) -> torch.Generator:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    generator = torch.Generator(device="cpu")
    generator.manual_seed(seed)
    return generator


def make_env(seed: int, reliability: float | None = None) -> PSCRSearchPrefixEnv:
    choices = RELIABILITY_BANDS if reliability is None else (reliability,)
    return PSCRSearchPrefixEnv(P8SearchPrefixConfig(seed=seed, forecast_reliability_choices=choices))


def stack(envs: list[PSCRSearchPrefixEnv]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    return (
        np.stack([env.actor_observation() for env in envs]),
        np.stack([env.critic_observation() for env in envs]),
        np.stack([env.graph_observation()["action_masks"] for env in envs]),
    )


def deterministic_action(agent: PSCRP8PlainMAPPO, env: PSCRSearchPrefixEnv) -> np.ndarray:
    obs = torch.as_tensor(env.actor_observation()[None], dtype=torch.float32)
    masks = torch.as_tensor(env.graph_observation()["action_masks"][None], dtype=torch.float32)
    with torch.no_grad():
        return torch.argmax(agent.action_distribution(obs, masks).logits, dim=-1).squeeze(0).numpy().astype(np.int64)


def evaluate(agent: PSCRP8PlainMAPPO, seed: int, repeats: int = 32) -> tuple[list[dict[str, Any]], dict[str, float]]:
    rng = np.random.default_rng(seed)
    rows: list[dict[str, Any]] = []
    for reliability in RELIABILITY_BANDS:
        for episode in range(repeats):
            env = make_env(int(rng.integers(0, 2**31 - 1)), reliability)
            env.reset()
            total = 0.0
            while not env.done:
                _, _, _, reward, _, _ = env.step(deterministic_action(agent, env))
                total += float(reward.mean())
            rows.append({"reliability": reliability, "episode": episode, "return": total, **env.terminal_summary()})
    summary: dict[str, float] = {"episodes": float(len(rows))}
    fields = ("return", "weighted_service_value", "primary_completed", "future_completed", "future_localized", "energy_used", "reconfiguration_events")
    for reliability in RELIABILITY_BANDS:
        subset = [row for row in rows if float(row["reliability"]) == reliability]
        for field in fields:
            summary[f"r{reliability}_{field}"] = float(np.mean([float(row[field]) for row in subset]))
    return rows, summary


def train(seed: int, updates: int, parallel_envs: int, output: Path) -> None:
    generator = seed_all(seed)
    agent = PSCRP8PlainMAPPO()
    optimizer = torch.optim.Adam(agent.parameters(), lr=3e-4)
    rng = np.random.default_rng(seed + 37)
    envs = [make_env(int(rng.integers(0, 2**31 - 1))) for _ in range(parallel_envs)]
    gamma, lam, clip, epochs, rollout_steps = 0.99, 0.95, 0.2, 4, 64
    fields = ("update", "train_reward", "policy_loss", "value_loss", "r0.1_return", "r0.9_return", "r0.1_service", "r0.9_service")
    with (output / "train_log.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for update in range(1, updates + 1):
            records = []
            for _ in range(rollout_steps):
                obs, critic, masks = stack(envs)
                obs_t, critic_t, masks_t = (torch.as_tensor(obs, dtype=torch.float32), torch.as_tensor(critic, dtype=torch.float32), torch.as_tensor(masks, dtype=torch.float32))
                with torch.no_grad():
                    distribution = agent.action_distribution(obs_t, masks_t)
                    actions = torch.multinomial(distribution.probs.reshape(-1, distribution.probs.shape[-1]), 1, generator=generator).reshape(distribution.probs.shape[:-1])
                    logp = distribution.log_prob(actions).sum(dim=-1)
                    values = agent.value(critic_t)
                rewards, dones = [], []
                for index, env in enumerate(envs):
                    _, _, _, reward, done, _ = env.step(actions[index].numpy())
                    rewards.append(float(reward.mean()))
                    dones.append(float(done[0, 0]))
                    if done[0, 0]:
                        envs[index] = make_env(int(rng.integers(0, 2**31 - 1)))
                records.append((obs, critic, masks, actions.numpy(), logp.numpy(), values.numpy(), np.asarray(rewards), np.asarray(dones)))
            _, final_critic, _ = stack(envs)
            with torch.no_grad():
                next_values = agent.value(torch.as_tensor(final_critic, dtype=torch.float32)).numpy()
            advantages = np.zeros((rollout_steps, parallel_envs), dtype=np.float32)
            returns = np.zeros((rollout_steps, parallel_envs), dtype=np.float32)
            gae = np.zeros(parallel_envs, dtype=np.float32)
            for step in reversed(range(rollout_steps)):
                values, rewards, dones = records[step][5], records[step][6], records[step][7]
                following = next_values if step == rollout_steps - 1 else records[step + 1][5]
                delta = rewards + gamma * (1.0 - dones) * following - values
                gae = delta + gamma * lam * (1.0 - dones) * gae
                advantages[step], returns[step] = gae, gae + values
            flat_obs = torch.as_tensor(np.concatenate([row[0] for row in records]), dtype=torch.float32)
            flat_critic = torch.as_tensor(np.concatenate([row[1] for row in records]), dtype=torch.float32)
            flat_masks = torch.as_tensor(np.concatenate([row[2] for row in records]), dtype=torch.float32)
            flat_actions = torch.as_tensor(np.concatenate([row[3] for row in records]), dtype=torch.int64)
            old_logp = torch.as_tensor(np.concatenate([row[4] for row in records]), dtype=torch.float32)
            flat_adv = torch.as_tensor(advantages.reshape(-1), dtype=torch.float32)
            flat_adv = (flat_adv - flat_adv.mean()) / (flat_adv.std() + 1e-8)
            flat_returns = torch.as_tensor(returns.reshape(-1), dtype=torch.float32)
            policy_loss = value_loss = 0.0
            for _ in range(epochs):
                distribution = agent.action_distribution(flat_obs, flat_masks)
                ratio = torch.exp(distribution.log_prob(flat_actions).sum(dim=-1) - old_logp)
                policy = -torch.minimum(ratio * flat_adv, torch.clamp(ratio, 1.0 - clip, 1.0 + clip) * flat_adv).mean()
                value = torch.nn.functional.mse_loss(agent.value(flat_critic), flat_returns)
                loss = policy + 0.5 * value - 0.01 * distribution.entropy().mean()
                optimizer.zero_grad(); loss.backward(); torch.nn.utils.clip_grad_norm_(agent.parameters(), 0.5); optimizer.step()
                policy_loss, value_loss = float(policy.detach()), float(value.detach())
            validation = evaluate(agent, seed + update, repeats=8)[1] if update % 32 == 0 or update == updates else {}
            writer.writerow({
                "update": update, "train_reward": float(np.mean([row[6].mean() for row in records])), "policy_loss": policy_loss, "value_loss": value_loss,
                "r0.1_return": validation.get("r0.1_return", ""), "r0.9_return": validation.get("r0.9_return", ""),
                "r0.1_service": validation.get("r0.1_weighted_service_value", ""), "r0.9_service": validation.get("r0.9_weighted_service_value", ""),
            })
            handle.flush()
    torch.save({"protocol": PROTOCOL, "seed": seed, "updates": updates, "state_dict": agent.state_dict()}, output / "endpoint.pt")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("train", "evaluate"))
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--updates", type=int, default=256)
    parser.add_argument("--parallel-envs", type=int, default=8)
    parser.add_argument("--checkpoint", type=Path)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("refusing without --execute")
    if args.output_root.exists():
        raise FileExistsError(f"refusing to overwrite {args.output_root}")
    args.output_root.mkdir(parents=True)
    if args.mode == "train":
        train(args.seed, args.updates, args.parallel_envs, args.output_root)
        return
    if args.checkpoint is None:
        raise ValueError("evaluate requires --checkpoint")
    payload = torch.load(args.checkpoint, map_location="cpu", weights_only=True)
    if payload.get("protocol") != PROTOCOL:
        raise ValueError("unexpected checkpoint")
    agent = PSCRP8PlainMAPPO(); agent.load_state_dict(payload["state_dict"])
    rows, summary = evaluate(agent, args.seed)
    with (args.output_root / "episode_metrics.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys()); writer.writeheader(); writer.writerows(rows)
    (args.output_root / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
