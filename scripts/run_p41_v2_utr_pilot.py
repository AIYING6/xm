"""P41 T4 UTR baseline runner.

The runner reads frozen tapes.  Training uses only the training tape, validation
uses only the validation tape, and final evaluation requires a separately
created endpoint checkpoint.
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from algorithms.p41_utr_ppo import P41UTRPPO
from envs.recoverable_service_chain_v2_env import RecoverableServiceChainV2Env
from scripts.p41_v2_tapes import scenario_from_dict


def load_tape(path: Path) -> list:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("protocol") != "P41-V2-SCENARIO-TAPE-V1":
        raise ValueError("unexpected P41 tape protocol")
    return [scenario_from_dict(row) for row in payload["episodes"]]


class TapeCursor:
    def __init__(self, tape: list):
        self.tape = tape
        self.index = 0

    def next(self) -> RecoverableServiceChainV2Env:
        scenario = self.tape[self.index % len(self.tape)]
        self.index += 1
        return RecoverableServiceChainV2Env(scenario)


def _seed_all(seed: int) -> torch.Generator:
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    generator = torch.Generator(device="cpu"); generator.manual_seed(seed)
    return generator


def _stack_envs(envs: list[RecoverableServiceChainV2Env]) -> tuple[np.ndarray, np.ndarray]:
    return np.stack([env.actor_observation() for env in envs]), np.stack([env.critic_observation() for env in envs])


def evaluate(agent: P41UTRPPO | None, tape: list, seed: int, random_legal: bool = False) -> tuple[list[dict], dict]:
    generator = np.random.default_rng(seed)
    rows: list[dict] = []
    action_counts = {"service_site_0": 0, "service_site_1": 0, "relay_reconfigurations": 0}
    for episode, scenario in enumerate(tape):
        env = RecoverableServiceChainV2Env(scenario); env.reset()
        while not env.done:
            obs = env.actor_observation()
            if random_legal:
                actions = generator.integers(0, 3, size=3, dtype=np.int64)
            else:
                with torch.no_grad():
                    logits = agent.action_distribution(torch.as_tensor(obs[None], dtype=torch.float32))
                    actions = torch.argmax(logits.logits, dim=-1).squeeze(0).cpu().numpy().astype(np.int64)
            if actions[2] == 1: action_counts["service_site_0"] += 1
            if actions[2] == 2: action_counts["service_site_1"] += 1
            _, _, _, _, _, info = env.step(actions)
        summary = env.terminal_summary()
        action_counts["relay_reconfigurations"] += int(summary["reconfigurations"])
        rows.append({"episode": episode, "family": scenario.name.split("_")[0], **summary})
    summary = {
        "episodes": len(rows),
        "mean_completed_service_value": float(np.mean([row["completed_value"] for row in rows])),
        "completion_rate": float(np.mean([row["completed_value"] > 0.0 for row in rows])),
        "commit_abort_rate": float(np.mean([row["aborted"] for row in rows])),
        **action_counts,
    }
    return rows, summary


def train(seed: int, train_tape: list, validation_tape: list, updates: int, parallel_envs: int, out: Path) -> None:
    action_generator = _seed_all(seed)
    agent = P41UTRPPO()
    optimizer = torch.optim.Adam(agent.parameters(), lr=3e-4)
    cursor = TapeCursor(train_tape)
    envs = [cursor.next() for _ in range(parallel_envs)]
    gamma, gae_lambda, clip, epochs = 0.99, 0.95, 0.2, 4
    log_path = out / "train_log.csv"
    with log_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=("update", "train_reward", "policy_loss", "value_loss", "validation_value", "validation_completion"))
        writer.writeheader()
        for update in range(1, updates + 1):
            records = []
            for _ in range(9):
                obs, critic = _stack_envs(envs)
                obs_t = torch.as_tensor(obs, dtype=torch.float32)
                critic_t = torch.as_tensor(critic, dtype=torch.float32)
                with torch.no_grad():
                    dist = agent.action_distribution(obs_t)
                    actions_t = torch.multinomial(
                        dist.probs.reshape(-1, dist.probs.shape[-1]), 1,
                        generator=action_generator,
                    ).reshape(dist.probs.shape[:-1])
                    logp_t = dist.log_prob(actions_t).sum(dim=-1)
                    value_t = agent.value(critic_t)
                rewards, dones = [], []
                for index, env in enumerate(envs):
                    _, _, _, reward, done, _ = env.step(actions_t[index].cpu().numpy())
                    rewards.append(float(reward.mean()))
                    dones.append(float(done[0, 0]))
                    if done[0, 0]: envs[index] = cursor.next()
                records.append((obs, critic, actions_t.cpu().numpy(), logp_t.cpu().numpy(), value_t.cpu().numpy(), np.asarray(rewards), np.asarray(dones)))
            _, final_critic = _stack_envs(envs)
            with torch.no_grad(): next_value = agent.value(torch.as_tensor(final_critic, dtype=torch.float32)).cpu().numpy()
            advantages = np.zeros((9, parallel_envs), dtype=np.float32); returns = np.zeros_like(advantages); gae = np.zeros(parallel_envs, dtype=np.float32)
            for step in reversed(range(9)):
                values, rewards, dones = records[step][4], records[step][5], records[step][6]
                following = next_value if step == 8 else records[step + 1][4]
                delta = rewards + gamma * (1.0 - dones) * following - values
                gae = delta + gamma * gae_lambda * (1.0 - dones) * gae
                advantages[step] = gae; returns[step] = gae + values
            flat_obs = torch.as_tensor(np.concatenate([row[0] for row in records]), dtype=torch.float32)
            flat_critic = torch.as_tensor(np.concatenate([row[1] for row in records]), dtype=torch.float32)
            flat_actions = torch.as_tensor(np.concatenate([row[2] for row in records]), dtype=torch.int64)
            old_logp = torch.as_tensor(np.concatenate([row[3] for row in records]), dtype=torch.float32)
            flat_adv = torch.as_tensor(advantages.reshape(-1), dtype=torch.float32); flat_adv = (flat_adv - flat_adv.mean()) / (flat_adv.std() + 1e-8)
            flat_returns = torch.as_tensor(returns.reshape(-1), dtype=torch.float32)
            policy_loss = value_loss = 0.0
            for _ in range(epochs):
                dist = agent.action_distribution(flat_obs)
                logp = dist.log_prob(flat_actions).sum(dim=-1)
                ratio = torch.exp(logp - old_logp)
                actor_loss = -torch.minimum(ratio * flat_adv, torch.clamp(ratio, 1.0 - clip, 1.0 + clip) * flat_adv).mean()
                critic_loss = torch.nn.functional.mse_loss(agent.value(flat_critic), flat_returns)
                entropy = dist.entropy().mean()
                loss = actor_loss + 0.5 * critic_loss - 0.01 * entropy
                optimizer.zero_grad(); loss.backward(); torch.nn.utils.clip_grad_norm_(agent.parameters(), 0.5); optimizer.step()
                policy_loss, value_loss = float(actor_loss.detach()), float(critic_loss.detach())
            if update % 32 == 0 or update == updates:
                _, validation = evaluate(agent, validation_tape, seed + update)
            else:
                validation = {"mean_completed_service_value": "", "completion_rate": ""}
            writer.writerow({"update": update, "train_reward": float(np.mean([row[5].mean() for row in records])), "policy_loss": policy_loss, "value_loss": value_loss, "validation_value": validation["mean_completed_service_value"], "validation_completion": validation["completion_rate"]})
            handle.flush()
    torch.save({"protocol": "P41-V2-UTR-PPO-V1", "seed": seed, "state_dict": agent.state_dict()}, out / "endpoint.pt")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("train", "evaluate", "random-evaluate"))
    parser.add_argument("--train-tape", type=Path)
    parser.add_argument("--validation-tape", type=Path)
    parser.add_argument("--evaluation-tape", type=Path)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--updates", type=int, default=512)
    parser.add_argument("--parallel-envs", type=int, default=16)
    parser.add_argument("--checkpoint", type=Path)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute: raise SystemExit("refusing to run without --execute")
    if args.output_root.exists(): raise FileExistsError(f"refusing to overwrite {args.output_root}")
    args.output_root.mkdir(parents=True)
    if args.mode == "train":
        if args.train_tape is None or args.validation_tape is None: raise ValueError("train mode requires training and validation tapes")
        train(args.seed, load_tape(args.train_tape), load_tape(args.validation_tape), args.updates, args.parallel_envs, args.output_root)
        return
    if args.evaluation_tape is None: raise ValueError("evaluation requires --evaluation-tape")
    tape = load_tape(args.evaluation_tape)
    if args.mode == "random-evaluate":
        rows, summary = evaluate(None, tape, args.seed, random_legal=True)
    else:
        if args.checkpoint is None: raise ValueError("evaluate requires --checkpoint")
        payload = torch.load(args.checkpoint, map_location="cpu", weights_only=True)
        if payload.get("protocol") != "P41-V2-UTR-PPO-V1": raise ValueError("unexpected checkpoint protocol")
        agent = P41UTRPPO(); agent.load_state_dict(payload["state_dict"]); agent.eval()
        rows, summary = evaluate(agent, tape, args.seed)
    with (args.output_root / "episode_metrics.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys()); writer.writeheader(); writer.writerows(rows)
    (args.output_root / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
