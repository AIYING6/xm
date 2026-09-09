"""Technical one-update audit for the frozen P3-Q1 learnability pilot."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

import numpy as np
import torch


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from algorithms.epistemic_commitment_p3_policy import (
    P3CentralCritic,
    P3PolicyConfig,
    P3RecurrentActor,
    parameter_count,
)
from envs.epistemic_commitment_p3_env import (
    MODE_DEFER,
    EpistemicCommitmentP3Env,
    P3CommunicationSpec,
)


FREEZE = ROOT / "configs" / "epistemic_commitment_p3_q1_learnability_freeze_20260909.json"
Q0_RESULT = ROOT / "docs" / "strong_q2_clean_sheet_p0_20260909" / "P3_Q0_RESULT.json"


def load_freeze() -> dict:
    value = json.loads(FREEZE.read_text(encoding="utf-8"))
    if value.get("protocol") != "EPISTEMIC-COMMITMENT-P3-Q1-LEARNABILITY-FREEZE-V1":
        raise ValueError("unexpected P3-Q1 freeze protocol")
    return value


def _rollout(actor: P3RecurrentActor, seed: int = 98311) -> dict:
    torch.manual_seed(seed)
    generator = torch.Generator(device="cpu").manual_seed(seed + 17)
    env = EpistemicCommitmentP3Env(
        P3CommunicationSpec("delivered", "delivered", "current"), seed=seed
    )
    obs, share, _ = env.reset()
    hidden = None
    observations = []
    shared = []
    modes = []
    raw_guidance = []
    old_log_probs = []
    final_info = {}
    while not env.done:
        observations.append(obs.copy())
        shared.append(share[0].copy())
        with torch.no_grad():
            output = actor(torch.as_tensor(obs[:, None, :], dtype=torch.float32), hidden)
            hidden = output["hidden"]
            mode_prob = torch.softmax(output["mode_logits"][:, 0], dim=-1)
            sampled_mode = torch.multinomial(mode_prob, 1, generator=generator).squeeze(-1)
            sampled_mode[env.relay_id] = MODE_DEFER
            noise = torch.randn((3, 2), generator=generator)
            guidance = output["guidance_mean"][:, 0] + output["guidance_log_std"][:, 0].exp() * noise
            mode_dist, guidance_dist = actor.distributions(output)
            log_prob = guidance_dist.log_prob(guidance[:, None, :]).sum(-1)[:, 0]
            role_mask = torch.tensor([1.0, 0.0, 1.0])
            log_prob = log_prob + role_mask * mode_dist.log_prob(sampled_mode[:, None])[:, 0]
        action = np.zeros((3, 3), dtype=np.float32)
        action[:, 0] = sampled_mode.numpy()
        action[:, 1:] = guidance.numpy()
        modes.append(sampled_mode.numpy())
        raw_guidance.append(guidance.numpy())
        old_log_probs.append(log_prob.numpy())
        obs, share, _, rewards, _, final_info = env.step(action)
    return {
        "observations": torch.as_tensor(np.stack(observations), dtype=torch.float32).transpose(0, 1),
        "shared": torch.as_tensor(np.stack(shared), dtype=torch.float32),
        "modes": torch.as_tensor(np.stack(modes), dtype=torch.int64).transpose(0, 1),
        "guidance": torch.as_tensor(np.stack(raw_guidance), dtype=torch.float32).transpose(0, 1),
        "old_log_prob": torch.as_tensor(np.stack(old_log_probs), dtype=torch.float32).transpose(0, 1),
        "return": torch.full((len(observations),), float(rewards[0, 0]), dtype=torch.float32),
        "info": final_info,
        "epochs": len(observations),
    }


def audit() -> dict:
    freeze = load_freeze()
    q0 = json.loads(Q0_RESULT.read_text(encoding="utf-8"))
    config = P3PolicyConfig(
        actor_hidden_dim=int(freeze["actor_hidden_dim"]),
        critic_hidden_dim=int(freeze["critic_hidden_dim"]),
        guidance_log_std_initial=float(freeze["guidance_log_std_initial"]),
    )
    torch.manual_seed(20260909)
    actor = P3RecurrentActor(config)
    critic = P3CentralCritic(config)
    actor_before = copy.deepcopy(actor.state_dict())
    critic_before = copy.deepcopy(critic.state_dict())
    batch = _rollout(actor)

    actor_optimizer = torch.optim.Adam(actor.parameters(), lr=float(freeze["actor_learning_rate"]))
    critic_optimizer = torch.optim.Adam(critic.parameters(), lr=float(freeze["critic_learning_rate"]))
    output = actor(batch["observations"])
    mode_dist, guidance_dist = actor.distributions(output)
    guidance_log_prob = guidance_dist.log_prob(batch["guidance"]).sum(-1)
    mode_log_prob = mode_dist.log_prob(batch["modes"])
    role_mask = torch.tensor([[1.0], [0.0], [1.0]])
    new_log_prob = guidance_log_prob + role_mask * mode_log_prob
    values = critic(batch["shared"])
    advantages = batch["return"] - values.detach()
    normalized_advantage = (advantages - advantages.mean()) / (advantages.std(unbiased=False) + 1e-6)
    expanded_advantage = normalized_advantage[None, :].expand_as(new_log_prob)
    ratio = torch.exp(new_log_prob - batch["old_log_prob"])
    clipped = torch.clamp(
        ratio,
        1.0 - float(freeze["ppo_clip_epsilon"]),
        1.0 + float(freeze["ppo_clip_epsilon"]),
    )
    surrogate = torch.minimum(ratio * expanded_advantage, clipped * expanded_advantage)
    entropy = guidance_dist.entropy().sum(-1) + role_mask * mode_dist.entropy()
    actor_loss = -surrogate.mean() - float(freeze["entropy_coefficient"]) * entropy.mean()
    critic_loss = torch.mean((values - batch["return"]) ** 2)
    actor_optimizer.zero_grad(set_to_none=True)
    actor_loss.backward()
    actor_grad = float(torch.nn.utils.clip_grad_norm_(actor.parameters(), float(freeze["max_grad_norm"])))
    actor_optimizer.step()
    critic_optimizer.zero_grad(set_to_none=True)
    critic_loss.backward()
    critic_grad = float(torch.nn.utils.clip_grad_norm_(critic.parameters(), float(freeze["max_grad_norm"])))
    critic_optimizer.step()

    actor_changed = any(not torch.equal(actor_before[key], actor.state_dict()[key]) for key in actor_before)
    critic_changed = any(not torch.equal(critic_before[key], critic.state_dict()[key]) for key in critic_before)
    checks = {
        "q0_pass_is_registered": q0.get("verdict") == "P3_Q0_PASS_TO_TINY_LEARNABILITY_PILOT",
        "pilot_budget_arithmetic_exact": freeze["episodes_per_run"] * freeze["physical_steps_per_episode"]
        == freeze["physical_steps_per_run"]
        and freeze["episodes_per_update"] * freeze["updates_per_run"] == freeze["episodes_per_run"],
        "fresh_three_seed_registry": freeze["training_seeds"] == [98311, 98312, 98313],
        "heldout_cells_excluded_from_training": set(freeze["training_cells"]).isdisjoint(
            freeze["heldout_cells_evaluation_only"]
        ),
        "mixed_action_shapes_exact": output["mode_logits"].shape == (3, batch["epochs"], 3)
        and output["guidance_mean"].shape == (3, batch["epochs"], 2),
        "one_closed_loop_rollout_completed": batch["epochs"] == 8 and bool(batch["info"].get("endpoint")),
        "losses_and_gradients_finite": all(
            np.isfinite(value)
            for value in (float(actor_loss.detach()), float(critic_loss.detach()), actor_grad, critic_grad)
        ),
        "actor_and_critic_update_live": actor_changed and critic_changed and actor_grad > 0 and critic_grad > 0,
        "relay_mode_excluded_from_policy_loss": float(role_mask[1, 0]) == 0.0,
        "training_remains_locked": freeze["training_authorized"] is False,
    }
    return {
        "protocol": "EPISTEMIC-COMMITMENT-P3-Q1-TRAINABLE-INTERFACE-AUDIT-V1",
        "verdict": "P3_Q1_INTERFACE_PASS_TO_RUNNER_IMPLEMENTATION" if all(checks.values()) else "P3_Q1_INTERFACE_STOP",
        "checks": checks,
        "actor_parameters": parameter_count(actor),
        "critic_parameters": parameter_count(critic),
        "smoke_rollout_endpoint": batch["info"].get("endpoint"),
        "smoke_actor_loss": float(actor_loss.detach()),
        "smoke_critic_loss": float(critic_loss.detach()),
        "smoke_actor_gradient_norm": actor_grad,
        "smoke_critic_gradient_norm": critic_grad,
        "technical_smoke_environment_steps": 64,
        "technical_smoke_ppo_updates": 1,
        "scientific_training_started": False,
        "next_authorized_action": "implement exact-resume Q1 runner, evaluator, aggregate gate, and cloud preflight",
        "evidence_boundary": "This one-update smoke validates tensor, action, loss and gradient plumbing only; it does not establish learnability or method performance."
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = audit()
    payload = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        if args.output.exists():
            raise FileExistsError(args.output)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    if report["verdict"] != "P3_Q1_INTERFACE_PASS_TO_RUNNER_IMPLEMENTATION":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
