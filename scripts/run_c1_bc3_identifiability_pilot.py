"""Run one frozen arm of the short C1 BC3 identifiability pilot.

The runner is intentionally separate from C1 G1.  It never reads teammate
levels into an actor tensor.  The only additional BC3 signal is the legal
posterior defined in :mod:`algorithms.c1_bc3_mappo`.
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
from algorithms.c1_bc3_mappo import C1PilotMAPPO, update_capability_posterior
from envs.c1_lbf_masked_adapter import C1LBFConfig, C1MaskedLBFAdapter

PROTOCOL = "C1-BC3-IDENTIFIABILITY-PILOT-V1"
ARMS = ("ff_mappo", "recurrent_mappo", "bc3_mappo", "shuffled_bc3_mappo")
SEEDS = (91111, 91112, 91113)
OBS_DIM, CRITIC_DIM, ACTION_DIM, AGENTS = 12, 22, 6, 2


@dataclass(frozen=True)
class Settings:
    updates: int = 128
    parallel_envs: int = 16
    rollout_steps: int = 24
    horizon: int = 16
    endpoint_episodes: int = 256


def seed_all(seed: int) -> torch.Generator:
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    generator = torch.Generator(device="cpu"); generator.manual_seed(seed)
    return generator


def build_env(seed: int, horizon: int) -> C1MaskedLBFAdapter:
    env = C1MaskedLBFAdapter(C1LBFConfig(seed=seed, horizon=horizon, emit_public_joint_load_receipt=True))
    actor, critic, masks = env.reset()
    if actor.shape != (AGENTS, OBS_DIM) or critic.shape != (AGENTS, CRITIC_DIM) or masks.shape != (AGENTS, ACTION_DIM):
        raise RuntimeError("unexpected C1 pilot interface; refusing to train")
    return env


def stack(envs: list[C1MaskedLBFAdapter]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    return (
        np.stack([env.actor_observation() for env in envs]),
        np.stack([env.critic_observation() for env in envs]),
        np.stack([env.action_masks() for env in envs]),
    )


def _shuffle_posterior(posterior: torch.Tensor) -> torch.Tensor:
    """Deterministic across-environment permutation; does not add information."""
    return torch.roll(posterior, shifts=1, dims=0)


def _next_posterior(
    posterior: torch.Tensor,
    *,
    receipt: np.ndarray,
    rewards: np.ndarray,
    arm: str,
) -> torch.Tensor:
    if arm not in {"bc3_mappo", "shuffled_bc3_mappo"}:
        return posterior
    receipt_t = torch.as_tensor(np.repeat(receipt[:, None], AGENTS, axis=1), dtype=torch.float32)
    reward_t = torch.as_tensor(np.repeat(rewards[:, None], AGENTS, axis=1), dtype=torch.float32)
    value = update_capability_posterior(posterior, joint_load_receipt=receipt_t, public_team_reward=reward_t)
    return _shuffle_posterior(value) if arm == "shuffled_bc3_mappo" else value


def endpoint(
    agent: C1PilotMAPPO, arm: str, seed: int, settings: Settings
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, float]]:
    rng = np.random.default_rng(seed)
    rows: list[dict[str, Any]] = []
    traces: list[dict[str, Any]] = []
    agent.eval()
    with torch.no_grad():
        for episode in range(settings.endpoint_episodes):
            env = build_env(int(rng.integers(0, 2**31 - 1)), settings.horizon)
            memory = agent.initial_memory(1, AGENTS, device="cpu") if agent.uses_memory else None
            posterior = torch.full((1, AGENTS), 0.5, dtype=torch.float32)
            team_return = 0.0; receipts = 0; failed_receipts = 0; posterior_after_failure: list[float] = []
            post_failure: dict[str, float] | None = None
            step = 0
            while True:
                actor, _, masks = stack([env])
                dist, next_memory = agent.action_distribution(
                    torch.as_tensor(actor, dtype=torch.float32), torch.as_tensor(masks, dtype=torch.float32),
                    memory=memory, posterior=posterior if agent.uses_posterior else None,
                )
                actions = torch.argmax(dist.logits, dim=-1).squeeze(0).numpy().astype(np.int64)
                if post_failure is not None:
                    traces.append({
                        "episode": episode,
                        "failure_step": int(post_failure["failure_step"]),
                        "response_step": step,
                        "posterior_before": post_failure["posterior_before"],
                        "posterior_after": float(posterior.mean()),
                        "response_action_agent0": int(actions[0]),
                        "response_action_agent1": int(actions[1]),
                        "response_is_joint_load": float(bool(np.all(actions == env._load_action_id))),
                    })
                    post_failure = None
                _, _, _, reward, done, info = env.step(actions)
                team_reward = float(np.mean(reward)); team_return += team_reward
                receipt = np.asarray([info["public_joint_load_receipt"]], dtype=np.float32)
                if receipt[0] > 0.5:
                    receipts += 1
                    if team_reward <= 0.0:
                        failed_receipts += 1
                posterior_before = float(posterior.mean())
                posterior = _next_posterior(posterior, receipt=receipt, rewards=np.asarray([team_reward]), arm=arm)
                if receipt[0] > 0.5 and team_reward <= 0.0 and agent.uses_posterior:
                    posterior_after_failure.append(float(posterior.mean()))
                    post_failure = {"failure_step": float(step), "posterior_before": posterior_before}
                memory = next_memory
                if bool(done.all()):
                    rows.append({"episode": episode, "team_return": team_return, "joint_load_receipts": receipts,
                                 "failed_joint_load_receipts": failed_receipts,
                                 "mean_posterior_after_failure": float(np.mean(posterior_after_failure)) if posterior_after_failure else "",
                                 **info})
                    break
                step += 1
    agent.train()
    complete = np.asarray([float(row["completed_foods"]) for row in rows])
    summary = {"episodes": len(rows), "mean_return": float(np.mean([row["team_return"] for row in rows])),
               "mean_completed_foods": float(complete.mean()), "full_completion_rate": float(np.mean([row["completed_all"] for row in rows])),
               "timeout_rate": float(np.mean([row["timeout"] for row in rows])),
               "mean_joint_load_receipts": float(np.mean([row["joint_load_receipts"] for row in rows])),
               "mean_failed_joint_load_receipts": float(np.mean([row["failed_joint_load_receipts"] for row in rows]))}
    return rows, traces, summary


def train(arm: str, seed: int, out: Path, settings: Settings) -> None:
    generator = seed_all(seed); rng = np.random.default_rng(seed + 29)
    envs = [build_env(int(rng.integers(0, 2**31 - 1)), settings.horizon) for _ in range(settings.parallel_envs)]
    agent = C1PilotMAPPO(obs_dim=OBS_DIM, critic_dim=CRITIC_DIM, action_dim=ACTION_DIM, arm=arm)
    optimizer = torch.optim.Adam(agent.parameters(), lr=3e-4)
    memory = agent.initial_memory(settings.parallel_envs, AGENTS, device="cpu") if agent.uses_memory else None
    posterior = torch.full((settings.parallel_envs, AGENTS), 0.5, dtype=torch.float32)
    fields = ("update", "train_reward", "policy_loss", "value_loss", "mean_posterior", "validation_completed_foods", "validation_timeout_rate")
    with (out / "train_log.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader()
        for update in range(1, settings.updates + 1):
            records = []
            for _ in range(settings.rollout_steps):
                actor, critic, masks = stack(envs)
                actor_t = torch.as_tensor(actor, dtype=torch.float32); critic_t = torch.as_tensor(critic, dtype=torch.float32); masks_t = torch.as_tensor(masks, dtype=torch.float32)
                with torch.no_grad():
                    dist, next_memory = agent.action_distribution(actor_t, masks_t, memory=memory, posterior=posterior if agent.uses_posterior else None)
                    actions_t = torch.multinomial(dist.probs.reshape(-1, ACTION_DIM), 1, generator=generator).reshape(settings.parallel_envs, AGENTS)
                    logp_t = dist.log_prob(actions_t); values_t = agent.value(critic_t).mean(dim=-1)
                rewards = np.zeros(settings.parallel_envs, dtype=np.float32); dones = np.zeros(settings.parallel_envs, dtype=np.float32); receipts = np.zeros(settings.parallel_envs, dtype=np.float32)
                for index, env in enumerate(envs):
                    _, _, _, reward, done, info = env.step(actions_t[index].numpy())
                    rewards[index] = float(np.mean(reward)); dones[index] = float(done[0]); receipts[index] = float(info["public_joint_load_receipt"])
                    if bool(done.all()):
                        envs[index] = build_env(int(rng.integers(0, 2**31 - 1)), settings.horizon)
                records.append((actor, critic, masks, actions_t.numpy(), logp_t.numpy(), values_t.numpy(), rewards, dones,
                                None if memory is None else memory.detach().numpy(), posterior.numpy().copy()))
                posterior = _next_posterior(posterior, receipt=receipts, rewards=rewards, arm=arm)
                if next_memory is not None:
                    memory = next_memory.detach(); memory[dones > 0.5] = 0.0
                posterior[dones > 0.5] = 0.5
            _, next_critic, _ = stack(envs)
            with torch.no_grad(): bootstrap = agent.value(torch.as_tensor(next_critic, dtype=torch.float32)).mean(dim=-1).numpy()
            advantages = np.zeros((settings.rollout_steps, settings.parallel_envs), dtype=np.float32); returns = np.zeros_like(advantages); gae = np.zeros(settings.parallel_envs, dtype=np.float32)
            for index in reversed(range(settings.rollout_steps)):
                following = bootstrap if index == settings.rollout_steps - 1 else records[index + 1][5]
                delta = records[index][6] + 0.99 * (1.0 - records[index][7]) * following - records[index][5]
                gae = delta + 0.99 * 0.95 * (1.0 - records[index][7]) * gae; advantages[index] = gae; returns[index] = gae + records[index][5]
            flat_actor = torch.as_tensor(np.concatenate([r[0] for r in records]), dtype=torch.float32); flat_critic = torch.as_tensor(np.concatenate([r[1] for r in records]), dtype=torch.float32); flat_masks = torch.as_tensor(np.concatenate([r[2] for r in records]), dtype=torch.float32)
            flat_actions = torch.as_tensor(np.concatenate([r[3] for r in records]), dtype=torch.int64); old_logp = torch.as_tensor(np.concatenate([r[4] for r in records]), dtype=torch.float32)
            flat_memory = None if not agent.uses_memory else torch.as_tensor(np.concatenate([r[8] for r in records]), dtype=torch.float32)
            flat_posterior = torch.as_tensor(np.concatenate([r[9] for r in records]), dtype=torch.float32)
            actor_adv = torch.as_tensor(np.repeat(advantages[..., None], AGENTS, axis=2).reshape(-1, AGENTS), dtype=torch.float32); actor_adv = (actor_adv - actor_adv.mean()) / (actor_adv.std() + 1e-8)
            value_returns = torch.as_tensor(np.repeat(returns[..., None], AGENTS, axis=2).reshape(-1), dtype=torch.float32)
            for _ in range(4):
                dist, _ = agent.action_distribution(flat_actor, flat_masks, memory=flat_memory, posterior=flat_posterior if agent.uses_posterior else None)
                ratio = torch.exp(dist.log_prob(flat_actions) - old_logp); actor_loss = -torch.minimum(ratio * actor_adv, torch.clamp(ratio, 0.8, 1.2) * actor_adv).mean(); critic_loss = torch.nn.functional.mse_loss(agent.value(flat_critic).reshape(-1), value_returns)
                loss = actor_loss + 0.5 * critic_loss - 0.01 * dist.entropy().mean(); optimizer.zero_grad(); loss.backward(); torch.nn.utils.clip_grad_norm_(agent.parameters(), 0.5); optimizer.step()
            validation: dict[str, float] = {}
            if update % 32 == 0 or update == settings.updates:
                _, _, validation = endpoint(agent, arm, 93_000 + seed + update, Settings(endpoint_episodes=64))
            writer.writerow({"update": update, "train_reward": float(np.mean([r[6].mean() for r in records])), "policy_loss": float(actor_loss.detach()), "value_loss": float(critic_loss.detach()), "mean_posterior": float(posterior.mean()), "validation_completed_foods": validation.get("mean_completed_foods", ""), "validation_timeout_rate": validation.get("timeout_rate", "")}); handle.flush()
    torch.save({"protocol": PROTOCOL, "arm": arm, "seed": seed, "settings": settings.__dict__, "state_dict": agent.state_dict()}, out / "endpoint.pt")


def load_agent(path: Path) -> tuple[C1PilotMAPPO, str]:
    payload = torch.load(path, map_location="cpu", weights_only=True)
    if payload.get("protocol") != PROTOCOL: raise ValueError("unexpected checkpoint protocol")
    arm = str(payload["arm"]); agent = C1PilotMAPPO(obs_dim=OBS_DIM, critic_dim=CRITIC_DIM, action_dim=ACTION_DIM, arm=arm); agent.load_state_dict(payload["state_dict"]); return agent, arm


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("mode", choices=("train", "evaluate")); parser.add_argument("--arm", choices=ARMS); parser.add_argument("--seed", type=int, required=True); parser.add_argument("--output", type=Path, required=True); parser.add_argument("--checkpoint", type=Path); parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute: raise SystemExit("refusing to run without --execute")
    if args.output.exists(): raise FileExistsError(f"refusing to overwrite {args.output}")
    args.output.mkdir(parents=True)
    if args.mode == "train":
        if args.arm is None or args.seed not in SEEDS: raise ValueError("arm and frozen seed required for training")
        train(args.arm, args.seed, args.output, Settings()); return
    if args.checkpoint is None: raise ValueError("--checkpoint is required")
    agent, arm = load_agent(args.checkpoint); rows, traces, summary = endpoint(agent, arm, args.seed, Settings())
    with (args.output / "episode_metrics.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys()); writer.writeheader(); writer.writerows(rows)
    with (args.output / "post_failure_action_trace.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = ("episode", "failure_step", "response_step", "posterior_before", "posterior_after", "response_action_agent0", "response_action_agent1", "response_is_joint_load")
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader(); writer.writerows(traces)
    (args.output / "summary.json").write_text(json.dumps({"protocol": PROTOCOL, "arm": arm, **summary}, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__": main()
