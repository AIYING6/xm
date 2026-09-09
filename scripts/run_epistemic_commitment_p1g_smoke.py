"""Local optimizer/checkpoint smoke for the epistemic commitment pilot.

This runner is intentionally tiny and is not a performance experiment.  It
connects the frozen two-stage task to the candidate or matched recurrent actor,
performs a few CPU PPO-style updates, and exposes exact continuation state.
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import sys

import numpy as np
import torch
from torch import nn


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from algorithms.epistemic_commitment import (
    CapacityMatchedRecurrentActor,
    CommitmentActorConfig,
    InformationSetCommitmentActor,
)
from algorithms.epistemic_commitment_objective import commitment_actor_loss
from envs.epistemic_commitment_trainable_env import (
    ACTION_FALLBACK,
    EpistemicCommitmentEpisodeSpec,
    EpistemicCommitmentTrainableEnv,
    RELIABILITY_CONTEXTS,
)


METHOD_CANDIDATE = "information_set_commitment"
METHOD_RECURRENT = "capacity_and_risk_matched_recurrent"
METHODS = (METHOD_CANDIDATE, METHOD_RECURRENT)


class CommitmentCritic(nn.Module):
    def __init__(self, input_dim: int = 117, hidden_dim: int = 32) -> None:
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, 1),
        )

    def forward(self, share_obs: torch.Tensor) -> torch.Tensor:
        return self.network(share_obs).squeeze(-1)


def smoke_episode_specs(update_index: int, batch_size: int) -> list[EpistemicCommitmentEpisodeSpec]:
    contexts = tuple(RELIABILITY_CONTEXTS)
    specs: list[EpistemicCommitmentEpisodeSpec] = []
    for offset in range(batch_size):
        index = update_index * batch_size + offset
        context = contexts[index % len(contexts)]
        probability = RELIABILITY_CONTEXTS[context]
        # Deterministic low-discrepancy event sequence; no global RNG or result
        # selection enters the smoke contract.
        delivered = ((index * 37 + 11) % 100) < int(round(100 * probability))
        specs.append(EpistemicCommitmentEpisodeSpec(920_000 + index, context, delivered))
    return specs


class CommitmentSmokeRunner:
    checkpoint_protocol = "EPISTEMIC-COMMITMENT-P1G-SMOKE-CHECKPOINT-V1"

    def __init__(self, method: str, seed: int, batch_size: int = 12) -> None:
        if method not in METHODS:
            raise ValueError(f"unknown method: {method}")
        self.method = method
        self.seed = int(seed)
        self.batch_size = int(batch_size)
        torch.manual_seed(self.seed)
        config = CommitmentActorConfig(input_dim=39, hidden_dim=32)
        if method == METHOD_CANDIDATE:
            self.actor: nn.Module = InformationSetCommitmentActor(config)
        else:
            self.actor = CapacityMatchedRecurrentActor(config)
        self.critic = CommitmentCritic()
        self.actor_optimizer = torch.optim.Adam(self.actor.parameters(), lr=3e-4)
        self.critic_optimizer = torch.optim.Adam(self.critic.parameters(), lr=1e-3)
        self.action_generator = torch.Generator(device="cpu")
        self.action_generator.manual_seed(self.seed + 73)
        self.update_index = 0

    def _collect(self) -> dict[str, torch.Tensor | list[dict]]:
        histories: list[np.ndarray] = []
        share_obs: list[np.ndarray] = []
        priors: list[float] = []
        environments: list[EpistemicCommitmentTrainableEnv] = []
        for spec in smoke_episode_specs(self.update_index, self.batch_size):
            env = EpistemicCommitmentTrainableEnv(self.seed, spec)
            obs0, _, _ = env.reset()
            obs1, shared1, _, _, _, _ = env.step([ACTION_FALLBACK] * 3)
            for agent_id in (env.leader_id, env.follower_id):
                histories.append(np.stack((obs0[agent_id], obs1[agent_id]), axis=0))
                priors.append(RELIABILITY_CONTEXTS[spec.context])
            share_obs.append(shared1[0])
            environments.append(env)

        history_tensor = torch.as_tensor(np.stack(histories), dtype=torch.float32)
        prior_tensor = torch.as_tensor(priors, dtype=torch.float32)
        shared_tensor = torch.as_tensor(np.stack(share_obs), dtype=torch.float32)
        output = self.actor(history_tensor)
        probabilities = torch.softmax(output["mode_logits"], dim=-1)
        actions = torch.multinomial(probabilities, 1, generator=self.action_generator).squeeze(-1)
        old_log_prob = torch.log(torch.gather(probabilities, 1, actions[:, None]).squeeze(1)).detach()

        rewards: list[float] = []
        infos: list[dict] = []
        for episode_index, env in enumerate(environments):
            leader = int(actions[2 * episode_index].item())
            follower = int(actions[2 * episode_index + 1].item())
            _, _, _, reward, _, info = env.step([leader, ACTION_FALLBACK, follower])
            rewards.append(float(reward[0, 0]))
            infos.append(info)
        reward_tensor = torch.as_tensor(rewards, dtype=torch.float32)
        return {
            "history": history_tensor,
            "prior": prior_tensor,
            "share_obs": shared_tensor,
            "actions": actions,
            "old_log_prob": old_log_prob,
            "rewards": reward_tensor,
            "infos": infos,
        }

    def update(self) -> dict:
        batch = self._collect()
        values = self.critic(batch["share_obs"])
        episode_advantages = batch["rewards"] - values.detach()
        advantages = torch.repeat_interleave(episode_advantages, 2)
        advantages = (advantages - advantages.mean()) / (advantages.std(unbiased=False) + 1e-6)
        output = self.actor(batch["history"])
        actor_loss, actor_telemetry = commitment_actor_loss(
            output,
            batch["actions"],
            batch["old_log_prob"],
            advantages,
            batch["prior"],
        )
        critic_loss = torch.mean((values - batch["rewards"]) ** 2)

        self.actor_optimizer.zero_grad(set_to_none=True)
        actor_loss.backward()
        torch.nn.utils.clip_grad_norm_(self.actor.parameters(), 0.5)
        self.actor_optimizer.step()
        self.critic_optimizer.zero_grad(set_to_none=True)
        critic_loss.backward()
        torch.nn.utils.clip_grad_norm_(self.critic.parameters(), 0.5)
        self.critic_optimizer.step()

        infos: list[dict] = batch["infos"]
        metrics = {
            "update": self.update_index,
            "method": self.method,
            "episodes": self.batch_size,
            "mean_task_value": float(batch["rewards"].mean().item()),
            "bilateral_commitment_rate": float(np.mean([info["bilateral_commitment_success"] for info in infos])),
            "single_sided_commitment_rate": float(np.mean([info["single_sided_commitment"] for info in infos])),
            "defer_rate": float(np.mean([info["defer"] for info in infos])),
            "fallback_rate": float(np.mean([info["fallback"] for info in infos])),
            "collision_rate": float(np.mean([info["collision"] for info in infos])),
            "constraint_violation_rate": float(np.mean([info["constraint_violation"] for info in infos])),
            "stale_token_commit_rate": float(np.mean([info["stale_token_commit"] for info in infos])),
            "actor_loss": float(actor_loss.detach().item()),
            "critic_loss": float(critic_loss.detach().item()),
            "calibration_loss": float(actor_telemetry["calibration_loss"].detach().item()),
        }
        self.update_index += 1
        return metrics

    def state_dict(self) -> dict:
        return {
            "protocol": self.checkpoint_protocol,
            "method": self.method,
            "seed": self.seed,
            "batch_size": self.batch_size,
            "update_index": self.update_index,
            "actor": copy.deepcopy(self.actor.state_dict()),
            "critic": copy.deepcopy(self.critic.state_dict()),
            "actor_optimizer": copy.deepcopy(self.actor_optimizer.state_dict()),
            "critic_optimizer": copy.deepcopy(self.critic_optimizer.state_dict()),
            "action_generator_state": self.action_generator.get_state().clone(),
        }

    def load_state_dict(self, state: dict) -> None:
        if state.get("protocol") != self.checkpoint_protocol:
            raise ValueError("unsupported P1G checkpoint protocol")
        if state.get("method") != self.method or int(state.get("seed")) != self.seed:
            raise ValueError("checkpoint belongs to another method or seed")
        if int(state.get("batch_size")) != self.batch_size:
            raise ValueError("checkpoint batch size mismatch")
        self.update_index = int(state["update_index"])
        self.actor.load_state_dict(state["actor"])
        self.critic.load_state_dict(state["critic"])
        self.actor_optimizer.load_state_dict(state["actor_optimizer"])
        self.critic_optimizer.load_state_dict(state["critic_optimizer"])
        self.action_generator.set_state(state["action_generator_state"])

    def save_checkpoint(self, path: Path) -> None:
        if path.exists():
            raise FileExistsError(f"refusing to overwrite fixed smoke checkpoint: {path}")
        path.parent.mkdir(parents=True, exist_ok=True)
        torch.save(self.state_dict(), path)

    def load_checkpoint(self, path: Path) -> None:
        self.load_state_dict(torch.load(path, map_location="cpu", weights_only=False))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--method", choices=METHODS, required=True)
    parser.add_argument("--seed", type=int, default=98101)
    parser.add_argument("--updates", type=int, default=1)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--checkpoint", type=Path)
    args = parser.parse_args()
    if args.updates < 1 or args.updates > 4:
        raise ValueError("P1G smoke permits 1--4 optimizer updates")
    runner = CommitmentSmokeRunner(args.method, args.seed)
    metrics = [runner.update() for _ in range(args.updates)]
    report = {
        "protocol": "EPISTEMIC-COMMITMENT-P1G-LOCAL-SMOKE-V1",
        "method": args.method,
        "seed": args.seed,
        "metrics": metrics,
        "scientific_evidence": False,
        "performance_training_started": False,
        "smoke_optimizer_updates": args.updates,
    }
    if args.checkpoint:
        runner.save_checkpoint(args.checkpoint)
    payload = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(payload + "\n")
    print(payload)


if __name__ == "__main__":
    main()
