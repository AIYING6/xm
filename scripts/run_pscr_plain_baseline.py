"""Train and evaluate the fixed-capacity MAPPO baseline on PSCR-v2."""
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
from algorithms.pscr_plain_mappo import PSCRPlainMAPPO
from envs.pscr_adversarial_service_env import PSCRConfig, PredictiveServiceChainReconfigurationEnv


PROTOCOL = "PSCR-PLAIN-MAPPO-BASELINE-V1"
PROFILES = ("bounded_mixture", "urgent_opposite", "routine_aligned")


def seed_all(seed: int) -> torch.Generator:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    generator = torch.Generator(device="cpu")
    generator.manual_seed(seed)
    return generator


class Cursor:
    def __init__(self, seed: int, profile: str = "bounded_mixture", *, curriculum: bool = False):
        self.rng = np.random.default_rng(seed)
        self.profile = profile
        self.curriculum = curriculum
        self.geometry_scale = 1.0
        self.future_arrival_step = 58

    def set_update(self, update: int, total_updates: int) -> None:
        if not self.curriculum:
            return
        fraction = update / total_updates
        if fraction <= 0.25:
            self.geometry_scale, self.future_arrival_step = 0.45, 105
        elif fraction <= 0.50:
            self.geometry_scale, self.future_arrival_step = 0.65, 78
        else:
            self.geometry_scale, self.future_arrival_step = 1.0, 58

    def next(self) -> PredictiveServiceChainReconfigurationEnv:
        return PredictiveServiceChainReconfigurationEnv(
            PSCRConfig(seed=int(self.rng.integers(0, 2**31 - 1)), adversary_profile=self.profile, geometry_scale=self.geometry_scale, future_arrival_step=self.future_arrival_step)
        )


def stack(envs: list[PredictiveServiceChainReconfigurationEnv]):
    return (
        np.stack([env.actor_observation() for env in envs]),
        np.stack([env.critic_observation() for env in envs]),
        np.stack([env.graph_observation()["action_masks"] for env in envs]),
    )


def deterministic_action(agent: PSCRPlainMAPPO, env: PredictiveServiceChainReconfigurationEnv) -> np.ndarray:
    obs = torch.as_tensor(env.actor_observation()[None], dtype=torch.float32)
    masks = torch.as_tensor(env.graph_observation()["action_masks"][None], dtype=torch.float32)
    with torch.no_grad():
        return torch.argmax(agent.action_distribution(obs, masks).logits, dim=-1).squeeze(0).numpy().astype(np.int64)


def evaluate(agent: PSCRPlainMAPPO, seed: int, repeats: int = 24) -> tuple[list[dict[str, Any]], dict[str, float]]:
    rng = np.random.default_rng(seed)
    rows: list[dict[str, Any]] = []
    for profile in PROFILES:
        for episode in range(repeats):
            env = PredictiveServiceChainReconfigurationEnv(PSCRConfig(seed=int(rng.integers(0, 2**31 - 1)), adversary_profile=profile))
            env.reset()
            total = 0.0
            while not env.done:
                _, _, _, reward, _, _ = env.step(deterministic_action(agent, env))
                total += float(reward.mean())
            rows.append({"profile": profile, "episode": episode, "return": total, **env.terminal_summary()})
    summary: dict[str, float] = {"episodes": float(len(rows))}
    for profile in PROFILES:
        subset = [row for row in rows if row["profile"] == profile]
        for field in ("return", "weighted_service_value", "primary_completed", "future_completed", "primary_expired", "future_expired", "energy_used", "reconfiguration_events"):
            summary[f"{profile}_{field}"] = float(np.mean([float(row[field]) for row in subset]))
    return rows, summary


def train(seed: int, updates: int, parallel_envs: int, output: Path, *, curriculum: bool = False) -> None:
    generator = seed_all(seed)
    agent = PSCRPlainMAPPO()
    optimizer = torch.optim.Adam(agent.parameters(), lr=3e-4)
    cursor = Cursor(seed + 37, curriculum=curriculum)
    cursor.set_update(1, updates)
    envs = [cursor.next() for _ in range(parallel_envs)]
    gamma, lam, clip, epochs, rollout_steps = 0.99, 0.95, 0.2, 4, 64
    fields = ("update", "train_reward", "policy_loss", "value_loss", "bounded_return", "bounded_service_value", "bounded_primary_complete", "bounded_future_complete")
    with (output / "train_log.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for update in range(1, updates + 1):
            cursor.set_update(update, updates)
            records = []
            for _ in range(rollout_steps):
                obs, critic, masks = stack(envs)
                obs_t, critic_t, masks_t = (torch.as_tensor(obs, dtype=torch.float32), torch.as_tensor(critic, dtype=torch.float32), torch.as_tensor(masks, dtype=torch.float32))
                with torch.no_grad():
                    distribution = agent.action_distribution(obs_t, masks_t)
                    action_t = torch.multinomial(distribution.probs.reshape(-1, distribution.probs.shape[-1]), 1, generator=generator).reshape(distribution.probs.shape[:-1])
                    logp_t = distribution.log_prob(action_t).sum(dim=-1)
                    value_t = agent.value(critic_t)
                rewards, dones = [], []
                for index, env in enumerate(envs):
                    _, _, _, reward, done, _ = env.step(action_t[index].numpy())
                    rewards.append(float(reward.mean()))
                    dones.append(float(done[0, 0]))
                    if done[0, 0]:
                        envs[index] = cursor.next()
                records.append((obs, critic, masks, action_t.numpy(), logp_t.numpy(), value_t.numpy(), np.asarray(rewards), np.asarray(dones)))
            _, final_critic, _ = stack(envs)
            with torch.no_grad():
                next_value = agent.value(torch.as_tensor(final_critic, dtype=torch.float32)).numpy()
            advantages, returns, gae = np.zeros((rollout_steps, parallel_envs), dtype=np.float32), np.zeros((rollout_steps, parallel_envs), dtype=np.float32), np.zeros(parallel_envs, dtype=np.float32)
            for step in reversed(range(rollout_steps)):
                values, rewards, dones = records[step][5], records[step][6], records[step][7]
                following = next_value if step == rollout_steps - 1 else records[step + 1][5]
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
                "bounded_return": validation.get("bounded_mixture_return", ""), "bounded_service_value": validation.get("bounded_mixture_weighted_service_value", ""),
                "bounded_primary_complete": validation.get("bounded_mixture_primary_completed", ""), "bounded_future_complete": validation.get("bounded_mixture_future_completed", ""),
            }); handle.flush()
    torch.save({"protocol": PROTOCOL, "seed": seed, "curriculum": curriculum, "state_dict": agent.state_dict()}, output / "endpoint.pt")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("train", "evaluate")); parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--updates", type=int, default=128); parser.add_argument("--parallel-envs", type=int, default=8); parser.add_argument("--curriculum", action="store_true")
    parser.add_argument("--checkpoint", type=Path); parser.add_argument("--output-root", type=Path, required=True); parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute: raise SystemExit("refusing without --execute")
    if args.output_root.exists(): raise FileExistsError(f"refusing to overwrite {args.output_root}")
    args.output_root.mkdir(parents=True)
    if args.mode == "train": train(args.seed, args.updates, args.parallel_envs, args.output_root, curriculum=args.curriculum); return
    if args.checkpoint is None: raise ValueError("evaluate requires --checkpoint")
    payload = torch.load(args.checkpoint, map_location="cpu", weights_only=True)
    if payload.get("protocol") != PROTOCOL: raise ValueError("unexpected checkpoint")
    agent = PSCRPlainMAPPO(); agent.load_state_dict(payload["state_dict"])
    rows, summary = evaluate(agent, args.seed)
    with (args.output_root / "episode_metrics.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys()); writer.writeheader(); writer.writerows(rows)
    (args.output_root / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__": main()
