"""Train/evaluate the plain PPO baseline for M2 forecast commitments."""
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
from envs.forecast_commitment_escort_env import (
    COMMIT_LEFT,
    COMMIT_RIGHT,
    M2_COMMITMENT_SCENARIOS,
    ForecastCommitmentEscortEnv,
    ForecastCommitmentEscortV2Env,
    ForecastCommitmentEscortV3Env,
)


PROTOCOL = "M2-PLAIN-MAPPO-BASELINE-V1"
TASKS = {
    "v1": ForecastCommitmentEscortEnv,
    "v2": ForecastCommitmentEscortV2Env,
    "v3": ForecastCommitmentEscortV3Env,
}


def seed_all(seed: int) -> torch.Generator:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    generator = torch.Generator(device="cpu")
    generator.manual_seed(seed)
    return generator


class ScenarioCursor:
    def __init__(self, seed: int, env_class=ForecastCommitmentEscortEnv):
        self.rng = np.random.default_rng(seed)
        self.index = 0
        self.env_class = env_class

    def next(self) -> ForecastCommitmentEscortEnv:
        scenario = M2_COMMITMENT_SCENARIOS[self.index % len(M2_COMMITMENT_SCENARIOS)]
        self.index += 1
        return self.env_class(scenario, seed=int(self.rng.integers(0, 2**31 - 1)))


def stack_envs(envs: list[ForecastCommitmentEscortEnv]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    return (
        np.stack([env.actor_observation() for env in envs]),
        np.stack([env.critic_observation() for env in envs]),
        np.stack([env.graph_observation()["action_masks"] for env in envs]),
    )


def deterministic_action(agent: M2PlainMAPPO, env: ForecastCommitmentEscortEnv) -> np.ndarray:
    obs = torch.as_tensor(env.actor_observation()[None], dtype=torch.float32)
    masks = torch.as_tensor(env.graph_observation()["action_masks"][None], dtype=torch.float32)
    with torch.no_grad():
        return torch.argmax(agent.action_distribution(obs, masks).logits, dim=-1).squeeze(0).numpy().astype(np.int64)


def evaluate(agent: M2PlainMAPPO, seed: int, *, repeats: int = 96, env_class=ForecastCommitmentEscortEnv) -> tuple[list[dict[str, Any]], dict[str, float]]:
    rng = np.random.default_rng(seed)
    rows: list[dict[str, Any]] = []
    for scenario in M2_COMMITMENT_SCENARIOS:
        for repeat in range(repeats):
            env = env_class(scenario, seed=int(rng.integers(0, 2**31 - 1)))
            env.reset()
            total = 0.0
            early_actions: np.ndarray | None = None
            reveal_actions: np.ndarray | None = None
            while not env.done:
                actions = deterministic_action(agent, env)
                if env.step_count == 0:
                    early_actions = actions.copy()
                if env.step_count == env.reveal_step:
                    reveal_actions = actions.copy()
                _, _, _, reward, _, _ = env.step(actions)
                total += float(reward.mean())
            branch_action = COMMIT_RIGHT if env._branch else COMMIT_LEFT
            rows.append({
                "scenario": scenario.name,
                "repeat": repeat,
                "return": total,
                "branch": int(env._branch),
                "early_directional_commit_fraction": float(np.mean(np.isin(early_actions, (COMMIT_LEFT, COMMIT_RIGHT)))),
                "early_right_commit_fraction": float(np.mean(early_actions == COMMIT_RIGHT)),
                "reveal_correct_direction_fraction": float(np.mean(reveal_actions == branch_action)),
                **env.terminal_summary(),
            })
    summary: dict[str, float] = {"episodes": float(len(rows))}
    for scenario in M2_COMMITMENT_SCENARIOS:
        subset = [row for row in rows if row["scenario"] == scenario.name]
        prefix = scenario.name
        summary[f"{prefix}_mean_return"] = float(np.mean([row["return"] for row in subset]))
        summary[f"{prefix}_early_directional_commit"] = float(np.mean([row["early_directional_commit_fraction"] for row in subset]))
        summary[f"{prefix}_early_right_commit"] = float(np.mean([row["early_right_commit_fraction"] for row in subset]))
        summary[f"{prefix}_reveal_correct_direction"] = float(np.mean([row["reveal_correct_direction_fraction"] for row in subset]))
    return rows, summary


def train(seed: int, updates: int, parallel_envs: int, out: Path, *, task_version: str = "v1") -> None:
    env_class = TASKS[task_version]
    generator = seed_all(seed)
    agent = M2PlainMAPPO()
    optimizer = torch.optim.Adam(agent.parameters(), lr=3e-4)
    cursor = ScenarioCursor(seed + 41, env_class=env_class)
    envs = [cursor.next() for _ in range(parallel_envs)]
    gamma, gae_lambda, clip, epochs, rollout_steps = 0.99, 0.95, 0.2, 4, 14
    fields = ("update", "train_reward", "policy_loss", "value_loss", "reliable_return", "ambiguous_return", "reliable_early_right", "ambiguous_early_directional", "ambiguous_reveal_correct")
    with (out / "train_log.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for update in range(1, updates + 1):
            records = []
            for _ in range(rollout_steps):
                obs, critic, masks = stack_envs(envs)
                obs_t = torch.as_tensor(obs, dtype=torch.float32)
                critic_t = torch.as_tensor(critic, dtype=torch.float32)
                masks_t = torch.as_tensor(masks, dtype=torch.float32)
                with torch.no_grad():
                    dist = agent.action_distribution(obs_t, masks_t)
                    actions_t = torch.multinomial(dist.probs.reshape(-1, dist.probs.shape[-1]), 1, generator=generator).reshape(dist.probs.shape[:-1])
                    logp_t = dist.log_prob(actions_t).sum(dim=-1)
                    value_t = agent.value(critic_t)
                rewards, dones = [], []
                for index, env in enumerate(envs):
                    _, _, _, reward, done, _ = env.step(actions_t[index].cpu().numpy())
                    rewards.append(float(reward.mean()))
                    dones.append(float(done[0, 0]))
                    if done[0, 0]:
                        envs[index] = cursor.next()
                records.append((obs, critic, masks, actions_t.cpu().numpy(), logp_t.cpu().numpy(), value_t.cpu().numpy(), np.asarray(rewards), np.asarray(dones)))
            _, final_critic, _ = stack_envs(envs)
            with torch.no_grad():
                next_value = agent.value(torch.as_tensor(final_critic, dtype=torch.float32)).cpu().numpy()
            advantages = np.zeros((rollout_steps, parallel_envs), dtype=np.float32)
            returns = np.zeros_like(advantages)
            gae = np.zeros(parallel_envs, dtype=np.float32)
            for step in reversed(range(rollout_steps)):
                values, rewards, dones = records[step][5], records[step][6], records[step][7]
                following = next_value if step == rollout_steps - 1 else records[step + 1][5]
                delta = rewards + gamma * (1.0 - dones) * following - values
                gae = delta + gamma * gae_lambda * (1.0 - dones) * gae
                advantages[step] = gae
                returns[step] = gae + values
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
                dist = agent.action_distribution(flat_obs, flat_masks)
                ratio = torch.exp(dist.log_prob(flat_actions).sum(dim=-1) - old_logp)
                policy_loss_t = -torch.minimum(ratio * flat_adv, torch.clamp(ratio, 1.0 - clip, 1.0 + clip) * flat_adv).mean()
                value_loss_t = torch.nn.functional.mse_loss(agent.value(flat_critic), flat_returns)
                loss = policy_loss_t + 0.5 * value_loss_t - 0.01 * dist.entropy().mean()
                optimizer.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(agent.parameters(), 0.5)
                optimizer.step()
                policy_loss, value_loss = float(policy_loss_t.detach()), float(value_loss_t.detach())
            if update % 32 == 0 or update == updates:
                _, validation = evaluate(agent, seed + update, repeats=24, env_class=env_class)
            else:
                validation = {}
            writer.writerow({
                "update": update,
                "train_reward": float(np.mean([row[6].mean() for row in records])),
                "policy_loss": policy_loss,
                "value_loss": value_loss,
                "reliable_return": validation.get("reliable_right_forecast_mean_return", ""),
                "ambiguous_return": validation.get("ambiguous_forecast_mean_return", ""),
                "reliable_early_right": validation.get("reliable_right_forecast_early_right_commit", ""),
                "ambiguous_early_directional": validation.get("ambiguous_forecast_early_directional_commit", ""),
                "ambiguous_reveal_correct": validation.get("ambiguous_forecast_reveal_correct_direction", ""),
            })
            handle.flush()
    torch.save({"protocol": PROTOCOL, "task_version": task_version, "seed": seed, "state_dict": agent.state_dict()}, out / "endpoint.pt")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("train", "evaluate"))
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--updates", type=int, default=256)
    parser.add_argument("--parallel-envs", type=int, default=16)
    parser.add_argument("--task-version", choices=tuple(TASKS), default="v1")
    parser.add_argument("--checkpoint", type=Path)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("refusing to run without --execute")
    if args.output_root.exists():
        raise FileExistsError(f"refusing to overwrite {args.output_root}")
    args.output_root.mkdir(parents=True)
    if args.mode == "train":
        train(args.seed, args.updates, args.parallel_envs, args.output_root, task_version=args.task_version)
        return
    if args.checkpoint is None:
        raise ValueError("evaluate requires --checkpoint")
    payload = torch.load(args.checkpoint, map_location="cpu", weights_only=True)
    if payload.get("protocol") != PROTOCOL:
        raise ValueError("unexpected checkpoint protocol")
    if payload.get("task_version", "v1") != args.task_version:
        raise ValueError("checkpoint and evaluation task versions differ")
    agent = M2PlainMAPPO()
    agent.load_state_dict(payload["state_dict"])
    rows, summary = evaluate(agent, args.seed, env_class=TASKS[args.task_version])
    with (args.output_root / "episode_metrics.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    (args.output_root / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
