"""Matched RC-PSCR-MAPPO M1 runner on the frozen P4 task."""
from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from pathlib import Path

import numpy as np
import torch
from torch.nn import functional as F

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from algorithms.pscr_reliability_commitment_mappo import PSCRReliabilityCommitmentMAPPO
from envs.pscr_contingency_service_env import PSCRContingencyServiceEnv
from scripts.run_pscr_p4_baseline import P4_CONFIG
from scripts.run_pscr_plain_baseline import deterministic_action, stack


PROTOCOL = "PSCR-RC-COMMITMENT-RELEASE-MAPPO-M1-V1"


def seed_all(seed: int) -> torch.Generator:
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    generator = torch.Generator(device="cpu"); generator.manual_seed(seed)
    return generator


class Cursor:
    def __init__(self, seed: int) -> None:
        self.rng = np.random.default_rng(seed)

    def next(self) -> PSCRContingencyServiceEnv:
        return PSCRContingencyServiceEnv(P4_CONFIG(seed=int(self.rng.integers(0, 2**31 - 1))))


def train(seed: int, arm: str, updates: int, parallel_envs: int, output: Path) -> None:
    generator = seed_all(seed)
    agent = PSCRReliabilityCommitmentMAPPO(mode=arm)
    optimizer = torch.optim.Adam(agent.parameters(), lr=3e-4)
    cursor = Cursor(seed + 37)
    envs = [cursor.next() for _ in range(parallel_envs)]
    gamma, lam, clip, epochs, rollout_steps = 0.99, 0.95, 0.2, 4, 64
    fields = ("update", "train_reward", "policy_loss", "value_loss", "commitment_q_loss", "commitment_alignment_loss")
    with (output / "train_log.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader()
        for update in range(1, updates + 1):
            records = []
            for _ in range(rollout_steps):
                obs, critic, masks = stack(envs)
                obs_t = torch.as_tensor(obs, dtype=torch.float32)
                critic_t = torch.as_tensor(critic, dtype=torch.float32)
                masks_t = torch.as_tensor(masks, dtype=torch.float32)
                with torch.no_grad():
                    distribution = agent.action_distribution(obs_t, masks_t)
                    action_t = torch.multinomial(distribution.probs.reshape(-1, distribution.probs.shape[-1]), 1, generator=generator).reshape(distribution.probs.shape[:-1])
                    logp_t = distribution.log_prob(action_t).sum(dim=-1)
                    value_t = agent.value(critic_t)
                rewards, dones = [], []
                for index, env in enumerate(envs):
                    _, _, _, reward, done, _ = env.step(action_t[index].numpy())
                    rewards.append(float(reward.mean())); dones.append(float(done[0, 0]))
                    if done[0, 0]:
                        envs[index] = cursor.next()
                records.append((obs, critic, masks, action_t.numpy(), logp_t.numpy(), value_t.numpy(), np.asarray(rewards), np.asarray(dones)))
            _, final_critic, _ = stack(envs)
            with torch.no_grad():
                next_value = agent.value(torch.as_tensor(final_critic, dtype=torch.float32)).numpy()
            advantages = np.zeros((rollout_steps, parallel_envs), dtype=np.float32)
            returns = np.zeros((rollout_steps, parallel_envs), dtype=np.float32)
            gae = np.zeros(parallel_envs, dtype=np.float32)
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
            policy_loss = value_loss = q_loss = alignment_loss = 0.0
            for _ in range(epochs):
                distribution = agent.action_distribution(flat_obs, flat_masks)
                ratio = torch.exp(distribution.log_prob(flat_actions).sum(dim=-1) - old_logp)
                policy = -torch.minimum(ratio * flat_adv, torch.clamp(ratio, 1.0 - clip, 1.0 + clip) * flat_adv).mean()
                value = F.mse_loss(agent.value(flat_critic), flat_returns)
                q = agent.commitment_values(flat_critic)
                selected_q = q.gather(1, flat_actions)
                q_fit = F.mse_loss(selected_q, flat_returns[:, None].expand_as(selected_q))
                pre = flat_obs[..., agent.future_active_index] < 0.5
                target = agent.commitment_target_distribution(flat_critic, flat_masks).detach()
                per_agent_kl = torch.sum(target * (torch.log(target + 1.0e-8) - torch.log(distribution.probs + 1.0e-8)), dim=-1)
                align = (per_agent_kl * pre.float()).sum() / pre.float().sum().clamp_min(1.0)
                # Every arm fits the capacity-matched Q head.  Only full and
                # permuted arms transmit its action preference to the actor.
                commitment_weight = 0.03 if arm in {"full", "permuted_reliability"} else 0.0
                loss = policy + 0.5 * value - 0.01 * distribution.entropy().mean() + 0.05 * q_fit + commitment_weight * align
                optimizer.zero_grad(); loss.backward(); torch.nn.utils.clip_grad_norm_(agent.parameters(), 0.5); optimizer.step()
                policy_loss, value_loss, q_loss, alignment_loss = map(float, (policy.detach(), value.detach(), q_fit.detach(), align.detach()))
            writer.writerow({"update": update, "train_reward": float(np.mean([row[6].mean() for row in records])), "policy_loss": policy_loss, "value_loss": value_loss, "commitment_q_loss": q_loss, "commitment_alignment_loss": alignment_loss}); handle.flush()
    torch.save({"protocol": PROTOCOL, "arm": arm, "seed": seed, "state_dict": agent.state_dict()}, output / "endpoint.pt")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("train", "evaluate"))
    parser.add_argument("--arm", choices=("full", "phase_control", "permuted_reliability"), required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--updates", type=int, default=256); parser.add_argument("--parallel-envs", type=int, default=8)
    parser.add_argument("--checkpoint", type=Path); parser.add_argument("--output-root", type=Path, required=True); parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute: raise SystemExit("refusing without --execute")
    if args.output_root.exists(): raise FileExistsError(f"refusing to overwrite {args.output_root}")
    args.output_root.mkdir(parents=True)
    if args.mode == "train":
        train(args.seed, args.arm, args.updates, args.parallel_envs, args.output_root); return
    if args.checkpoint is None: raise ValueError("evaluate requires --checkpoint")
    payload = torch.load(args.checkpoint, map_location="cpu", weights_only=True)
    if payload.get("protocol") != PROTOCOL or payload.get("arm") != args.arm: raise ValueError("unexpected checkpoint")
    agent = PSCRReliabilityCommitmentMAPPO(mode=args.arm); agent.load_state_dict(payload["state_dict"])
    from scripts.run_pscr_p4_reliability_endpoint import evaluate
    rows, summary = evaluate(agent, args.seed + 70_000)
    with (args.output_root / "episode_metrics.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    (args.output_root / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
