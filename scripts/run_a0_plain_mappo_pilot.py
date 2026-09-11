"""Short learnability pilot for A0 using an unmodified plain MAPPO baseline."""
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
from algorithms.m2_commitment_ppo import M2PlainMAPPO
from envs.active_perception_tracking_env import ActivePerceptionTrackingEnv


# Deliberately distinct from the earlier plain-MAPPO learnability pilot: this
# runner uses agent-wise PPO log-probabilities so that all method arms can be
# compared under the same credit-assignment interface.
PROTOCOL = "A0-OC-MAPPO-METHOD-PILOT-V1"
MARGINAL_WEIGHT = 0.25
ARMS = ("plain", "oc", "shuffled_oc", "zero_oc")


def seed_all(seed: int) -> torch.Generator:
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    generator = torch.Generator(device="cpu"); generator.manual_seed(seed)
    return generator


def stack(envs: list[ActivePerceptionTrackingEnv]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    return (
        np.stack([env.actor_observation() for env in envs]),
        np.stack([env.critic_observation() for env in envs]),
        np.stack([env.graph_observation()["action_masks"] for env in envs]),
    )


def choose(agent: M2PlainMAPPO, env: ActivePerceptionTrackingEnv) -> np.ndarray:
    obs = torch.as_tensor(env.actor_observation()[None], dtype=torch.float32)
    masks = torch.as_tensor(env.graph_observation()["action_masks"][None], dtype=torch.float32)
    with torch.no_grad():
        return torch.argmax(agent.action_distribution(obs, masks).logits, dim=-1).squeeze(0).numpy().astype(np.int64)


def evaluate(agent: M2PlainMAPPO, seed: int, *, repeats: int = 32) -> tuple[list[dict[str, Any]], dict[str, float]]:
    rng = np.random.default_rng(seed); rows: list[dict[str, Any]] = []
    for episode in range(repeats):
        env = ActivePerceptionTrackingEnv(seed=int(rng.integers(0, 2**31 - 1)))
        env.reset(); total = 0.0
        while not env.done:
            _, _, _, reward, _, _ = env.step(choose(agent, env))
            total += float(reward.mean())
        rows.append({"episode": episode, "return": total, **env.terminal_summary()})
    metric = lambda key: float(np.mean([float(row[key]) for row in rows]))
    return rows, {
        "episodes": float(repeats), "mean_return": metric("return"),
        "mean_estimation_error": metric("mean_evaluation_estimation_error"),
        "mean_final_logdet": metric("final_public_posterior_logdet"),
        "mean_distance": metric("total_distance"),
        "mean_near_collision_steps": metric("near_collision_steps"),
        "mean_measurement_count": metric("measurement_count"),
    }


def evaluate_reference(seed: int, *, mode: str, repeats: int = 32) -> tuple[list[dict[str, Any]], dict[str, float]]:
    if mode not in {"random", "hold"}:
        raise ValueError(mode)
    rng = np.random.default_rng(seed); rows: list[dict[str, Any]] = []
    for episode in range(repeats):
        env = ActivePerceptionTrackingEnv(seed=int(rng.integers(0, 2**31 - 1)))
        env.reset(); total = 0.0
        while not env.done:
            actions = np.zeros(env.num_agents, dtype=np.int64) if mode == "hold" else rng.integers(0, env.action_dim, size=env.num_agents, dtype=np.int64)
            _, _, _, reward, _, _ = env.step(actions)
            total += float(reward.mean())
        rows.append({"episode": episode, "return": total, **env.terminal_summary()})
    metric = lambda key: float(np.mean([float(row[key]) for row in rows]))
    return rows, {
        "episodes": float(repeats), "mean_return": metric("return"),
        "mean_estimation_error": metric("mean_evaluation_estimation_error"),
        "mean_final_logdet": metric("final_public_posterior_logdet"),
        "mean_distance": metric("total_distance"),
        "mean_near_collision_steps": metric("near_collision_steps"),
        "mean_measurement_count": metric("measurement_count"),
    }


def train(seed: int, updates: int, parallel_envs: int, out: Path, *, arm: str = "plain") -> None:
    if arm not in ARMS:
        raise ValueError(arm)
    generator = seed_all(seed)
    agent = M2PlainMAPPO(obs_dim=10, critic_dim=13, hidden_dim=96, action_dim=5)
    optimizer = torch.optim.Adam(agent.parameters(), lr=3e-4)
    rng = np.random.default_rng(seed + 31)
    credit_rng = np.random.default_rng(seed + 131)
    envs = [ActivePerceptionTrackingEnv(seed=int(rng.integers(0, 2**31 - 1))) for _ in range(parallel_envs)]
    gamma, gae_lambda, clip, epochs, rollout_steps = 0.99, 0.95, 0.20, 4, 16
    fields = (
        "update", "train_reward", "policy_loss", "value_loss",
        "credit_mean", "credit_std", "credit_positive_fraction", "credit_actor_adv_correlation",
        "validation_return", "validation_error", "validation_logdet", "validation_collisions",
    )
    with (out / "train_log.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader()
        for update in range(1, updates + 1):
            records = []
            for _ in range(rollout_steps):
                obs, critic, masks = stack(envs)
                obs_t = torch.as_tensor(obs, dtype=torch.float32); critic_t = torch.as_tensor(critic, dtype=torch.float32); masks_t = torch.as_tensor(masks, dtype=torch.float32)
                with torch.no_grad():
                    distribution = agent.action_distribution(obs_t, masks_t)
                    actions_t = torch.multinomial(distribution.probs.reshape(-1, 5), 1, generator=generator).reshape(parallel_envs, 3)
                    logp_t = distribution.log_prob(actions_t); values_t = agent.value(critic_t)
                rewards, dones, credits = [], [], []
                for index, env in enumerate(envs):
                    _, _, _, reward, done, info = env.step(actions_t[index].cpu().numpy())
                    rewards.append(float(reward.mean())); dones.append(float(done[0, 0]))
                    marginal = np.asarray(info["marginal_observability_contributions"], dtype=np.float32)
                    if arm == "shuffled_oc":
                        marginal = marginal[credit_rng.permutation(env.num_agents)]
                    if arm in {"plain", "zero_oc"}:
                        marginal = np.zeros_like(marginal)
                    credits.append(marginal)
                    if done[0, 0]:
                        envs[index] = ActivePerceptionTrackingEnv(seed=int(rng.integers(0, 2**31 - 1)))
                records.append((obs, critic, masks, actions_t.cpu().numpy(), logp_t.cpu().numpy(), values_t.cpu().numpy(), np.asarray(rewards), np.asarray(dones), np.asarray(credits)))
            _, next_critic, _ = stack(envs)
            with torch.no_grad():
                bootstrap = agent.value(torch.as_tensor(next_critic, dtype=torch.float32)).cpu().numpy()
            advantages = np.zeros((rollout_steps, parallel_envs), dtype=np.float32); returns = np.zeros_like(advantages); gae = np.zeros(parallel_envs, dtype=np.float32)
            for index in reversed(range(rollout_steps)):
                values, rewards, dones = records[index][5], records[index][6], records[index][7]
                following = bootstrap if index == rollout_steps - 1 else records[index + 1][5]
                delta = rewards + gamma * (1.0 - dones) * following - values
                gae = delta + gamma * gae_lambda * (1.0 - dones) * gae
                advantages[index] = gae; returns[index] = gae + values
            flat_obs = torch.as_tensor(np.concatenate([row[0] for row in records]), dtype=torch.float32)
            flat_critic = torch.as_tensor(np.concatenate([row[1] for row in records]), dtype=torch.float32)
            flat_masks = torch.as_tensor(np.concatenate([row[2] for row in records]), dtype=torch.float32)
            flat_actions = torch.as_tensor(np.concatenate([row[3] for row in records]), dtype=torch.int64)
            old_logp = torch.as_tensor(np.concatenate([row[4] for row in records]), dtype=torch.float32)
            team_adv = advantages[..., None]
            credit = np.asarray([row[8] for row in records], dtype=np.float32)
            centered_credit = credit - credit.mean(axis=-1, keepdims=True)
            actor_adv = team_adv + MARGINAL_WEIGHT * centered_credit
            if float(credit.std()) > 0.0:
                credit_adv_correlation = float(np.corrcoef(credit.reshape(-1), actor_adv.reshape(-1))[0, 1])
            else:
                credit_adv_correlation = ""
            flat_adv = torch.as_tensor(actor_adv.reshape(-1, 3), dtype=torch.float32); flat_adv = (flat_adv - flat_adv.mean()) / (flat_adv.std() + 1e-8)
            flat_returns = torch.as_tensor(returns.reshape(-1), dtype=torch.float32)
            policy_loss = value_loss = 0.0
            for _ in range(epochs):
                distribution = agent.action_distribution(flat_obs, flat_masks)
                ratio = torch.exp(distribution.log_prob(flat_actions) - old_logp)
                actor_loss = -torch.minimum(ratio * flat_adv, torch.clamp(ratio, 1.0 - clip, 1.0 + clip) * flat_adv).mean()
                critic_loss = torch.nn.functional.mse_loss(agent.value(flat_critic), flat_returns)
                loss = actor_loss + 0.5 * critic_loss - 0.01 * distribution.entropy().mean()
                optimizer.zero_grad(); loss.backward(); torch.nn.utils.clip_grad_norm_(agent.parameters(), 0.5); optimizer.step()
                policy_loss, value_loss = float(actor_loss.detach()), float(critic_loss.detach())
            if update % 32 == 0 or update == updates:
                _, validation = evaluate(agent, seed + update, repeats=16)
            else:
                validation = {}
            writer.writerow({
                "update": update, "train_reward": float(np.mean([row[6].mean() for row in records])),
                "policy_loss": policy_loss, "value_loss": value_loss,
                "credit_mean": float(credit.mean()), "credit_std": float(credit.std()),
                "credit_positive_fraction": float((credit > 0.0).mean()),
                "credit_actor_adv_correlation": credit_adv_correlation,
                "validation_return": validation.get("mean_return", ""), "validation_error": validation.get("mean_estimation_error", ""),
                "validation_logdet": validation.get("mean_final_logdet", ""), "validation_collisions": validation.get("mean_near_collision_steps", ""),
            }); handle.flush()
    torch.save({"protocol": PROTOCOL, "arm": arm, "marginal_weight": MARGINAL_WEIGHT, "seed": seed, "state_dict": agent.state_dict()}, out / "endpoint.pt")


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("mode", choices=("train", "evaluate", "random-evaluate", "hold-evaluate")); parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--updates", type=int, default=256); parser.add_argument("--parallel-envs", type=int, default=12); parser.add_argument("--episodes", type=int, default=32); parser.add_argument("--checkpoint", type=Path); parser.add_argument("--arm", choices=ARMS, default="plain")
    parser.add_argument("--output-root", type=Path, required=True); parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute: raise SystemExit("refusing to run without --execute")
    if args.output_root.exists(): raise FileExistsError(f"refusing to overwrite {args.output_root}")
    args.output_root.mkdir(parents=True)
    if args.mode == "train": train(args.seed, args.updates, args.parallel_envs, args.output_root, arm=args.arm); return
    if args.mode == "random-evaluate":
        rows, summary = evaluate_reference(args.seed, mode="random", repeats=args.episodes)
    elif args.mode == "hold-evaluate":
        rows, summary = evaluate_reference(args.seed, mode="hold", repeats=args.episodes)
    else:
        if args.checkpoint is None: raise ValueError("evaluate requires --checkpoint")
        payload = torch.load(args.checkpoint, map_location="cpu", weights_only=True)
        if payload.get("protocol") != PROTOCOL: raise ValueError("unexpected checkpoint protocol")
        if payload.get("arm", "plain") != args.arm: raise ValueError("checkpoint and requested arm differ")
        agent = M2PlainMAPPO(obs_dim=10, critic_dim=13, hidden_dim=96, action_dim=5); agent.load_state_dict(payload["state_dict"])
        rows, summary = evaluate(agent, args.seed, repeats=args.episodes)
    with (args.output_root / "episode_metrics.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys()); writer.writeheader(); writer.writerows(rows)
    (args.output_root / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
