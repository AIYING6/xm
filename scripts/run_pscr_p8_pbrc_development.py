"""Capacity-matched PPO runner for P8 PBRC and its frozen controls.

Only the first step of the environment's public commitment lock is a policy
decision.  Subsequent locked actions are executed by the environment but are
excluded from PPO's policy loss, preventing duplicated gradients for an
action that cannot affect the trajectory.
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
from algorithms.pscr_p8_pbrc_mappo import PSCRPBRCRoleCommitmentMAPPO
from envs.pscr_search_prefix_env import P8SearchPrefixConfig, PSCRSearchPrefixEnv


PROTOCOL = "PSCR-P8-PBRC-DEVELOPMENT-V1"
ARMS = ("plain", "plan_no_reliability", "permuted_pbrc", "pbrc")
RELIABILITIES = (0.1, 0.9)


def seed_all(seed: int) -> torch.Generator:
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    generator = torch.Generator(device="cpu"); generator.manual_seed(seed)
    return generator


def make_env(seed: int, reliability: float | None = None) -> PSCRSearchPrefixEnv:
    choices = RELIABILITIES if reliability is None else (reliability,)
    return PSCRSearchPrefixEnv(P8SearchPrefixConfig(seed=seed, forecast_reliability_choices=choices))


def stack(envs: list[PSCRSearchPrefixEnv]) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    graph = [env.graph_observation() for env in envs]
    due = np.asarray([env._commitment_active() and env._committed_intents is None for env in envs], dtype=bool)
    locked = np.asarray([env._commitment_active() and env._committed_intents is not None for env in envs], dtype=bool)
    return (np.stack([env.actor_observation() for env in envs]), np.stack([env.critic_observation() for env in envs]),
            np.stack([item["action_masks"] for item in graph]), np.stack([item["team_public_context"] for item in graph]), due, locked)


def choose(agent: PSCRPBRCRoleCommitmentMAPPO, obs: np.ndarray, masks: np.ndarray, context: np.ndarray, due: np.ndarray, locked: np.ndarray, envs: list[PSCRSearchPrefixEnv], arm: str, *, generator: torch.Generator | None) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Return applied actions, old logp, plan labels, and policy-active flags."""
    batch = len(envs)
    actions = np.zeros((batch, envs[0].num_agents), dtype=np.int64)
    logp = np.zeros(batch, dtype=np.float32)
    plans = np.full(batch, -1, dtype=np.int64)
    active = ~locked
    normal = active.copy()
    if arm != "plain":
        normal &= ~due
    with torch.no_grad():
        if np.any(normal):
            distribution = agent.action_distribution(torch.as_tensor(obs[normal], dtype=torch.float32), torch.as_tensor(masks[normal], dtype=torch.float32))
            selected = torch.argmax(distribution.logits, dim=-1) if generator is None else torch.multinomial(distribution.probs.reshape(-1, distribution.probs.shape[-1]), 1, generator=generator).reshape(distribution.probs.shape[:-1])
            actions[normal] = selected.numpy()
            logp[normal] = distribution.log_prob(selected).sum(dim=-1).numpy()
        if arm != "plain" and np.any(due):
            adjusted = agent.transform_context(torch.as_tensor(context[due], dtype=torch.float32), arm)
            distribution = agent.plan_distribution(adjusted)
            selected = torch.argmax(distribution.logits, dim=-1) if generator is None else torch.multinomial(distribution.probs, 1, generator=generator).squeeze(-1)
            plans[due] = selected.numpy()
            actions[due] = agent.plan_actions(selected).numpy()
            logp[due] = distribution.log_prob(selected).numpy()
    for index in np.flatnonzero(locked):
        actions[index] = envs[index]._committed_intents.copy()
    return actions, logp, plans, active


def evaluate(agent: PSCRPBRCRoleCommitmentMAPPO, arm: str, seed: int, repeats: int = 64) -> tuple[list[dict[str, Any]], dict[str, float]]:
    rng = np.random.default_rng(seed); rows: list[dict[str, Any]] = []
    for reliability in RELIABILITIES:
        for episode in range(repeats):
            env = make_env(int(rng.integers(0, 2**31 - 1)), reliability); env.reset(); total = 0.0; commitment_plan = -1
            while not env.done:
                obs, _, masks, context, due, locked = stack([env])
                actions, _, plans, _ = choose(agent, obs, masks, context, due, locked, [env], arm, generator=None)
                if plans[0] >= 0: commitment_plan = int(plans[0])
                _, _, _, reward, _, _ = env.step(actions[0]); total += float(reward.mean())
            rows.append({"reliability": reliability, "episode": episode, "return": total, "commit_stage_plan": float(commitment_plan == 1), **env.terminal_summary()})
    summary: dict[str, float] = {"episodes": float(len(rows))}
    for reliability in RELIABILITIES:
        subset = [row for row in rows if float(row["reliability"]) == reliability]
        for field in ("return", "weighted_service_value", "primary_completed", "future_completed", "future_localized", "energy_used", "commit_stage_plan"):
            summary[f"r{reliability}_{field}"] = float(np.mean([float(row[field]) for row in subset]))
    return rows, summary


def train(arm: str, seed: int, updates: int, parallel_envs: int, output: Path) -> None:
    generator = seed_all(seed); agent = PSCRPBRCRoleCommitmentMAPPO(); optimizer = torch.optim.Adam(agent.parameters(), lr=3e-4)
    rng = np.random.default_rng(seed + 37); envs = [make_env(int(rng.integers(0, 2**31 - 1))) for _ in range(parallel_envs)]
    gamma, lam, clip, epochs, rollout_steps = 0.99, 0.95, 0.2, 4, 64
    fields = ("update", "train_reward", "policy_loss", "value_loss", "active_decision_fraction", "r0.1_service", "r0.9_service", "r0.1_stage", "r0.9_stage")
    with (output / "train_log.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader()
        for update in range(1, updates + 1):
            records = []
            for _ in range(rollout_steps):
                obs, critic, masks, context, due, locked = stack(envs)
                actions, logp, plans, active = choose(agent, obs, masks, context, due, locked, envs, arm, generator=generator)
                with torch.no_grad(): values = agent.value(torch.as_tensor(critic, dtype=torch.float32)).numpy()
                rewards, dones = [], []
                for index, env in enumerate(envs):
                    _, _, _, reward, done, _ = env.step(actions[index]); rewards.append(float(reward.mean())); dones.append(float(done[0, 0]))
                    if done[0, 0]: envs[index] = make_env(int(rng.integers(0, 2**31 - 1)))
                records.append((obs, critic, masks, context, actions, logp, plans, active, values, np.asarray(rewards), np.asarray(dones)))
            _, final_critic, _, _, _, _ = stack(envs)
            with torch.no_grad(): next_values = agent.value(torch.as_tensor(final_critic, dtype=torch.float32)).numpy()
            advantages = np.zeros((rollout_steps, parallel_envs), dtype=np.float32); returns = np.zeros_like(advantages); gae = np.zeros(parallel_envs, dtype=np.float32)
            for step in reversed(range(rollout_steps)):
                values, rewards, dones = records[step][8], records[step][9], records[step][10]
                following = next_values if step == rollout_steps - 1 else records[step + 1][8]
                delta = rewards + gamma * (1.0 - dones) * following - values; gae = delta + gamma * lam * (1.0 - dones) * gae
                advantages[step], returns[step] = gae, gae + values
            flat_obs = torch.as_tensor(np.concatenate([row[0] for row in records]), dtype=torch.float32); flat_critic = torch.as_tensor(np.concatenate([row[1] for row in records]), dtype=torch.float32)
            flat_masks = torch.as_tensor(np.concatenate([row[2] for row in records]), dtype=torch.float32); flat_context = torch.as_tensor(np.concatenate([row[3] for row in records]), dtype=torch.float32)
            flat_actions = torch.as_tensor(np.concatenate([row[4] for row in records]), dtype=torch.long); old_logp = torch.as_tensor(np.concatenate([row[5] for row in records]), dtype=torch.float32)
            flat_plans = torch.as_tensor(np.concatenate([row[6] for row in records]), dtype=torch.long); active = torch.as_tensor(np.concatenate([row[7] for row in records]), dtype=torch.bool)
            advantage = torch.as_tensor(advantages.reshape(-1), dtype=torch.float32); advantage = (advantage - advantage.mean()) / (advantage.std() + 1e-8)
            ret = torch.as_tensor(returns.reshape(-1), dtype=torch.float32); decision = flat_plans >= 0; normal = active & ~decision
            policy_loss = value_loss = 0.0
            for _ in range(epochs):
                new_logp = torch.zeros_like(old_logp); entropy = torch.zeros_like(old_logp)
                if bool(normal.any()):
                    distribution = agent.action_distribution(flat_obs[normal], flat_masks[normal]); new_logp[normal] = distribution.log_prob(flat_actions[normal]).sum(dim=-1); entropy[normal] = distribution.entropy().mean(dim=-1)
                if bool(decision.any()):
                    distribution = agent.plan_distribution(agent.transform_context(flat_context[decision], arm)); new_logp[decision] = distribution.log_prob(flat_plans[decision]); entropy[decision] = distribution.entropy()
                ratio = torch.exp(new_logp[active] - old_logp[active]); adv = advantage[active]
                policy = -torch.minimum(ratio * adv, torch.clamp(ratio, 1.0 - clip, 1.0 + clip) * adv).mean()
                value = torch.nn.functional.mse_loss(agent.value(flat_critic), ret); loss = policy + 0.5 * value - 0.01 * entropy[active].mean()
                optimizer.zero_grad(); loss.backward(); torch.nn.utils.clip_grad_norm_(agent.parameters(), 0.5); optimizer.step(); policy_loss, value_loss = float(policy.detach()), float(value.detach())
            validation = evaluate(agent, arm, seed + update, repeats=8)[1] if update % 32 == 0 or update == updates else {}
            writer.writerow({"update": update, "train_reward": float(np.mean([row[9].mean() for row in records])), "policy_loss": policy_loss, "value_loss": value_loss, "active_decision_fraction": float(active.float().mean()), "r0.1_service": validation.get("r0.1_weighted_service_value", ""), "r0.9_service": validation.get("r0.9_weighted_service_value", ""), "r0.1_stage": validation.get("r0.1_commit_stage_plan", ""), "r0.9_stage": validation.get("r0.9_commit_stage_plan", "")}); handle.flush()
    torch.save({"protocol": PROTOCOL, "arm": arm, "seed": seed, "updates": updates, "state_dict": agent.state_dict()}, output / "endpoint.pt")


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("mode", choices=("train", "evaluate")); parser.add_argument("--arm", choices=ARMS, required=True); parser.add_argument("--seed", type=int, required=True); parser.add_argument("--updates", type=int, default=256); parser.add_argument("--parallel-envs", type=int, default=8); parser.add_argument("--checkpoint", type=Path); parser.add_argument("--output-root", type=Path, required=True); parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute: raise SystemExit("refusing without --execute")
    if args.output_root.exists(): raise FileExistsError(f"refusing to overwrite {args.output_root}")
    args.output_root.mkdir(parents=True)
    if args.mode == "train": train(args.arm, args.seed, args.updates, args.parallel_envs, args.output_root); return
    if args.checkpoint is None: raise ValueError("evaluate requires --checkpoint")
    payload = torch.load(args.checkpoint, map_location="cpu", weights_only=True)
    if payload.get("protocol") != PROTOCOL or payload.get("arm") != args.arm: raise ValueError("unexpected checkpoint")
    agent = PSCRPBRCRoleCommitmentMAPPO(); agent.load_state_dict(payload["state_dict"]); rows, summary = evaluate(agent, args.arm, args.seed)
    with (args.output_root / "episode_metrics.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys()); writer.writeheader(); writer.writerows(rows)
    (args.output_root / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8"); print(json.dumps(summary, indent=2))


if __name__ == "__main__": main()
