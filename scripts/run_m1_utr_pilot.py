"""M1 short-budget learnability runner for the plain MAPPO baseline.

No FUM mechanism is loaded here.  The runner has an explicit ``--execute``
guard and refuses to overwrite an output directory.
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
from algorithms.m1_utr_ppo import M1UTRPPO
from envs.freshness_uncertainty_monitoring_env import M1_SCENARIOS, FreshnessUncertaintyMonitoringEnv, MonitoringScenario


def seed_all(seed: int) -> torch.Generator:
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    generator = torch.Generator(device="cpu"); generator.manual_seed(seed)
    return generator


class ScenarioCursor:
    def __init__(self, seed: int):
        self.rng = np.random.default_rng(seed)
        self.index = 0

    def next(self) -> FreshnessUncertaintyMonitoringEnv:
        scenario = M1_SCENARIOS[self.index % len(M1_SCENARIOS)]
        self.index += 1
        return FreshnessUncertaintyMonitoringEnv(scenario, seed=int(self.rng.integers(0, 2**31 - 1)))


def stack_envs(envs: list[FreshnessUncertaintyMonitoringEnv]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    obs = np.stack([env.actor_observation() for env in envs])
    critic = np.stack([env.critic_observation() for env in envs])
    masks = np.stack([env.graph_observation()["action_masks"] for env in envs])
    return obs, critic, masks


def action_from_agent(agent: M1UTRPPO, env: FreshnessUncertaintyMonitoringEnv, *, stochastic: bool, generator: torch.Generator | None = None) -> np.ndarray:
    obs = torch.as_tensor(env.actor_observation()[None], dtype=torch.float32)
    masks = torch.as_tensor(env.graph_observation()["action_masks"][None], dtype=torch.float32)
    with torch.no_grad():
        dist = agent.action_distribution(obs, masks)
        if stochastic:
            actions = torch.multinomial(dist.probs.reshape(-1, dist.probs.shape[-1]), 1, generator=generator).reshape(1, -1)
        else:
            actions = torch.argmax(dist.logits, dim=-1)
    return actions.squeeze(0).cpu().numpy().astype(np.int64)


def evaluate(agent: M1UTRPPO | None, seed: int, *, random_legal: bool = False, repeats: int = 12) -> tuple[list[dict[str, Any]], dict[str, float]]:
    rng = np.random.default_rng(seed)
    rows: list[dict[str, Any]] = []
    for scenario in M1_SCENARIOS:
        for repeat in range(repeats):
            env = FreshnessUncertaintyMonitoringEnv(scenario, seed=int(rng.integers(0, 2**31 - 1)))
            env.reset(); total_reward = 0.0
            while not env.done:
                if random_legal:
                    masks = env.graph_observation()["action_masks"]
                    actions = np.asarray([rng.choice(np.flatnonzero(masks[a])) for a in range(env.num_agents)], dtype=np.int64)
                else:
                    actions = action_from_agent(agent, env, stochastic=False)
                _, _, _, reward, _, _ = env.step(actions)
                total_reward += float(reward.mean())
            summary = env.terminal_summary()
            rows.append({"scenario": scenario.name, "repeat": repeat, "return": total_reward, **summary})
    numeric = lambda key: float(np.mean([float(row[key]) for row in rows]))
    return rows, {
        "episodes": float(len(rows)),
        "mean_return": numeric("return"),
        "mean_evaluation_mse": numeric("evaluation_mse"),
        "mean_max_information_age": numeric("max_information_age"),
        "mean_missed_events": numeric("missed_events"),
        "mean_duplicate_sensing": numeric("duplicate_sensing"),
        "mean_distance": numeric("distance"),
    }


def train(seed: int, updates: int, parallel_envs: int, out: Path) -> None:
    generator = seed_all(seed)
    agent = M1UTRPPO(); optimizer = torch.optim.Adam(agent.parameters(), lr=3e-4)
    cursor = ScenarioCursor(seed + 19)
    envs = [cursor.next() for _ in range(parallel_envs)]
    gamma, gae_lambda, clip, epochs, rollout_steps = 0.99, 0.95, 0.2, 4, 12
    fields = ("update", "train_reward", "policy_loss", "value_loss", "validation_return", "validation_mse", "validation_max_age")
    with (out / "train_log.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader()
        for update in range(1, updates + 1):
            records = []
            for _ in range(rollout_steps):
                obs, critic, masks = stack_envs(envs)
                obs_t = torch.as_tensor(obs, dtype=torch.float32); critic_t = torch.as_tensor(critic, dtype=torch.float32)
                masks_t = torch.as_tensor(masks, dtype=torch.float32)
                with torch.no_grad():
                    dist = agent.action_distribution(obs_t, masks_t)
                    actions_t = torch.multinomial(dist.probs.reshape(-1, dist.probs.shape[-1]), 1, generator=generator).reshape(dist.probs.shape[:-1])
                    logp_t = dist.log_prob(actions_t).sum(dim=-1); value_t = agent.value(critic_t)
                rewards, dones = [], []
                for index, env in enumerate(envs):
                    _, _, _, reward, done, _ = env.step(actions_t[index].cpu().numpy())
                    rewards.append(float(reward.mean())); dones.append(float(done[0, 0]))
                    if done[0, 0]: envs[index] = cursor.next()
                records.append((obs, critic, masks, actions_t.cpu().numpy(), logp_t.cpu().numpy(), value_t.cpu().numpy(), np.asarray(rewards), np.asarray(dones)))
            _, final_critic, _ = stack_envs(envs)
            with torch.no_grad(): next_value = agent.value(torch.as_tensor(final_critic, dtype=torch.float32)).cpu().numpy()
            advantages = np.zeros((rollout_steps, parallel_envs), dtype=np.float32); returns = np.zeros_like(advantages); gae = np.zeros(parallel_envs, dtype=np.float32)
            for step in reversed(range(rollout_steps)):
                values, rewards, dones = records[step][5], records[step][6], records[step][7]
                following = next_value if step == rollout_steps - 1 else records[step + 1][5]
                delta = rewards + gamma * (1.0 - dones) * following - values
                gae = delta + gamma * gae_lambda * (1.0 - dones) * gae
                advantages[step] = gae; returns[step] = gae + values
            flat_obs = torch.as_tensor(np.concatenate([row[0] for row in records]), dtype=torch.float32)
            flat_critic = torch.as_tensor(np.concatenate([row[1] for row in records]), dtype=torch.float32)
            flat_masks = torch.as_tensor(np.concatenate([row[2] for row in records]), dtype=torch.float32)
            flat_actions = torch.as_tensor(np.concatenate([row[3] for row in records]), dtype=torch.int64)
            old_logp = torch.as_tensor(np.concatenate([row[4] for row in records]), dtype=torch.float32)
            flat_adv = torch.as_tensor(advantages.reshape(-1), dtype=torch.float32); flat_adv = (flat_adv - flat_adv.mean()) / (flat_adv.std() + 1e-8)
            flat_returns = torch.as_tensor(returns.reshape(-1), dtype=torch.float32)
            policy_loss = value_loss = 0.0
            for _ in range(epochs):
                dist = agent.action_distribution(flat_obs, flat_masks)
                logp = dist.log_prob(flat_actions).sum(dim=-1); ratio = torch.exp(logp - old_logp)
                actor_loss = -torch.minimum(ratio * flat_adv, torch.clamp(ratio, 1.0 - clip, 1.0 + clip) * flat_adv).mean()
                critic_loss = torch.nn.functional.mse_loss(agent.value(flat_critic), flat_returns)
                loss = actor_loss + 0.5 * critic_loss - 0.01 * dist.entropy().mean()
                optimizer.zero_grad(); loss.backward(); torch.nn.utils.clip_grad_norm_(agent.parameters(), 0.5); optimizer.step()
                policy_loss, value_loss = float(actor_loss.detach()), float(critic_loss.detach())
            if update % 16 == 0 or update == updates:
                _, validation = evaluate(agent, seed + update)
            else:
                validation = {"mean_return": "", "mean_evaluation_mse": "", "mean_max_information_age": ""}
            writer.writerow({"update": update, "train_reward": float(np.mean([row[6].mean() for row in records])), "policy_loss": policy_loss, "value_loss": value_loss, "validation_return": validation["mean_return"], "validation_mse": validation["mean_evaluation_mse"], "validation_max_age": validation["mean_max_information_age"]})
            handle.flush()
    torch.save({"protocol": "M1-UTR-MAPPO-PILOT-V1", "seed": seed, "state_dict": agent.state_dict()}, out / "endpoint.pt")


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("mode", choices=("train", "evaluate", "random-evaluate"))
    parser.add_argument("--seed", type=int, required=True); parser.add_argument("--updates", type=int, default=128); parser.add_argument("--parallel-envs", type=int, default=12)
    parser.add_argument("--checkpoint", type=Path); parser.add_argument("--output-root", type=Path, required=True); parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute: raise SystemExit("refusing to run without --execute")
    if args.output_root.exists(): raise FileExistsError(f"refusing to overwrite {args.output_root}")
    args.output_root.mkdir(parents=True)
    if args.mode == "train":
        train(args.seed, args.updates, args.parallel_envs, args.output_root); return
    if args.mode == "random-evaluate": rows, summary = evaluate(None, args.seed, random_legal=True)
    else:
        if args.checkpoint is None: raise ValueError("evaluate requires --checkpoint")
        payload = torch.load(args.checkpoint, map_location="cpu", weights_only=True)
        if payload.get("protocol") != "M1-UTR-MAPPO-PILOT-V1": raise ValueError("unexpected M1 checkpoint")
        agent = M1UTRPPO(); agent.load_state_dict(payload["state_dict"]); agent.eval(); rows, summary = evaluate(agent, args.seed)
    with (args.output_root / "episode_metrics.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys()); writer.writeheader(); writer.writerows(rows)
    (args.output_root / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
