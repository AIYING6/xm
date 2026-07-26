from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.distributions import Categorical


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.simple_ri_gmappo import (  # noqa: E402
    RIGMAPPOAgent,
    RIGMAPPOConfig,
    collect_rollout,
    compute_gae,
    eval_policy,
    make_envs,
    set_seed,
    stack_graphs,
)


class HAPPOBaselineAgent(nn.Module):
    """Minimal role-heterogeneous HAPPO-style baseline.

    Each blue UAV owns a separate no-graph actor/critic. The training update is
    sequential over agents. This is intentionally a no-graph external baseline,
    not a variant of the proposed multi-relation graph method.
    """

    def __init__(
        self,
        *,
        obs_dim: int,
        node_feat_dim: int,
        edge_feat_dim: int,
        share_obs_dim: int,
        action_dim: int,
        num_agents: int,
        num_roles: int,
        hidden_dim: int,
        role_dim: int,
        intent_dim: int,
    ):
        super().__init__()
        self.num_agents = num_agents
        self.num_roles = num_roles
        self.policies = nn.ModuleList(
            [
                RIGMAPPOAgent(
                    obs_dim=obs_dim,
                    node_feat_dim=node_feat_dim,
                    edge_feat_dim=edge_feat_dim,
                    share_obs_dim=share_obs_dim,
                    action_dim=action_dim,
                    num_agents=num_agents,
                    num_roles=num_roles,
                    hidden_dim=hidden_dim,
                    role_dim=role_dim,
                    intent_dim=intent_dim,
                    graph_encoder="no_graph",
                    use_intent_context=False,
                )
                for _ in range(num_agents)
            ]
        )

    def critic_value(self, share_obs: torch.Tensor, role: torch.Tensor) -> torch.Tensor:
        values = []
        for agent_id, policy in enumerate(self.policies):
            values.append(policy.critic_value(share_obs, role)[:, agent_id])
        return torch.stack(values, dim=1)

    def get_single_action_and_value(
        self,
        agent_id: int,
        obs: torch.Tensor,
        node_feat: torch.Tensor,
        edge_feat: torch.Tensor | None,
        role: torch.Tensor,
        adj: torch.Tensor,
        share_obs: torch.Tensor,
        *,
        action: torch.Tensor | None = None,
        deterministic: bool = False,
        relation_adj: torch.Tensor | None = None,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        policy = self.policies[agent_id]
        logits, _, _ = policy.actor(
            obs,
            node_feat,
            edge_feat,
            role,
            adj,
            self.num_agents,
            relation_adj=relation_adj,
        )
        dist = Categorical(logits=logits[:, agent_id])
        if action is None:
            action = torch.argmax(logits[:, agent_id], dim=-1) if deterministic else dist.sample()
        log_prob = dist.log_prob(action)
        entropy = dist.entropy()
        value = policy.critic_value(share_obs, role)[:, agent_id]
        return action, log_prob, entropy, value

    def get_action_and_value(
        self,
        obs: torch.Tensor,
        node_feat: torch.Tensor,
        edge_feat: torch.Tensor | None,
        role: torch.Tensor,
        adj: torch.Tensor,
        share_obs: torch.Tensor,
        relation_adj: torch.Tensor | None = None,
        action: torch.Tensor | None = None,
        deterministic: bool = False,
        **_unused,
    ):
        actions, log_probs, entropies, values = [], [], [], []
        for agent_id in range(self.num_agents):
            action_i = None if action is None else action[:, agent_id]
            act, logp, entropy, value = self.get_single_action_and_value(
                agent_id,
                obs,
                node_feat,
                edge_feat,
                role,
                adj,
                share_obs,
                action=action_i,
                deterministic=deterministic,
                relation_adj=relation_adj,
            )
            actions.append(act)
            log_probs.append(logp)
            entropies.append(entropy)
            values.append(value)
        batch = obs.shape[0]
        intent_logits = torch.zeros(batch, 1, 5, dtype=obs.dtype, device=obs.device)
        attention = torch.zeros(batch, adj.shape[-1], adj.shape[-1], dtype=obs.dtype, device=obs.device)
        return (
            torch.stack(actions, dim=1),
            torch.stack(log_probs, dim=1),
            torch.stack(entropies, dim=1),
            torch.stack(values, dim=1),
            attention,
            intent_logits,
        )


def load_happo_training_checkpoint(
    agent: HAPPOBaselineAgent,
    optimizers: list[optim.Optimizer],
    checkpoint_path: str,
    device: torch.device,
) -> None:
    checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=False)
    model_state = checkpoint.get("model_state", checkpoint)
    agent.load_state_dict(model_state)
    optimizer_states = checkpoint.get("optimizer_states") if isinstance(checkpoint, dict) else None
    if optimizer_states is not None:
        if len(optimizers) != len(optimizer_states):
            raise ValueError(
                f"optimizer count mismatch for {checkpoint_path}: "
                f"current={len(optimizers)} checkpoint={len(optimizer_states)}"
            )
        for optimizer, optimizer_state in zip(optimizers, optimizer_states):
            optimizer.load_state_dict(optimizer_state)
        print(f"loaded HAPPO optimizer states from {checkpoint_path}", flush=True)


def save_happo_training_checkpoint(
    path: Path,
    agent: HAPPOBaselineAgent,
    optimizers: list[optim.Optimizer],
    update: int,
) -> None:
    torch.save(
        {
            "model_state": agent.state_dict(),
            "optimizer_states": [optimizer.state_dict() for optimizer in optimizers],
            "update": int(update),
        },
        path,
    )


def update_happo_policy(
    agent: HAPPOBaselineAgent,
    optimizers: list[optim.Optimizer],
    batch: dict,
    cfg: RIGMAPPOConfig,
    device: torch.device,
) -> dict[str, float]:
    t_steps, n_envs, num_agents = batch["actions"].shape
    num_graphs = t_steps * n_envs
    obs = torch.as_tensor(batch["obs"].reshape(num_graphs, num_agents, -1), dtype=torch.float32, device=device)
    node_feat = torch.as_tensor(batch["node_feat"].reshape(num_graphs, *batch["node_feat"].shape[2:]), dtype=torch.float32, device=device)
    edge_feat = torch.as_tensor(batch["edge_feat"].reshape(num_graphs, *batch["edge_feat"].shape[2:]), dtype=torch.float32, device=device)
    role = torch.as_tensor(batch["role"].reshape(num_graphs, *batch["role"].shape[2:]), dtype=torch.long, device=device)
    adj = torch.as_tensor(batch["adj"].reshape(num_graphs, *batch["adj"].shape[2:]), dtype=torch.float32, device=device)
    relation_adj = torch.as_tensor(
        batch["relation_adj"].reshape(num_graphs, *batch["relation_adj"].shape[2:]), dtype=torch.float32, device=device
    )
    share_obs = torch.as_tensor(batch["share_obs"].reshape(num_graphs, num_agents, -1), dtype=torch.float32, device=device)
    actions = torch.as_tensor(batch["actions"].reshape(num_graphs, num_agents), dtype=torch.long, device=device)
    old_logp = torch.as_tensor(batch["logp"].reshape(num_graphs, num_agents), dtype=torch.float32, device=device)
    advantages = torch.as_tensor(batch["advantages"].reshape(num_graphs, num_agents), dtype=torch.float32, device=device)
    returns = torch.as_tensor(batch["returns"].reshape(num_graphs, num_agents), dtype=torch.float32, device=device)
    advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)

    losses, policy_losses, value_losses, entropies = [], [], [], []
    indices = np.arange(num_graphs)
    for _ in range(cfg.ppo_epochs):
        np.random.shuffle(indices)
        for start in range(0, num_graphs, cfg.minibatch_graphs):
            mb = indices[start : start + cfg.minibatch_graphs]
            for agent_id in range(num_agents):
                _, new_logp, entropy, values = agent.get_single_action_and_value(
                    agent_id,
                    obs[mb],
                    node_feat[mb],
                    edge_feat[mb],
                    role[mb],
                    adj[mb],
                    share_obs[mb],
                    action=actions[mb, agent_id],
                    relation_adj=relation_adj[mb],
                )
                ratio = (new_logp - old_logp[mb, agent_id]).exp()
                pg_loss1 = -advantages[mb, agent_id] * ratio
                pg_loss2 = -advantages[mb, agent_id] * torch.clamp(ratio, 1.0 - cfg.clip_coef, 1.0 + cfg.clip_coef)
                policy_loss = torch.max(pg_loss1, pg_loss2).mean()
                value_loss = 0.5 * (returns[mb, agent_id] - values).pow(2).mean()
                entropy_loss = entropy.mean()
                loss = policy_loss + cfg.value_coef * value_loss - cfg.entropy_coef * entropy_loss

                optimizers[agent_id].zero_grad()
                loss.backward()
                nn.utils.clip_grad_norm_(agent.policies[agent_id].parameters(), cfg.max_grad_norm)
                optimizers[agent_id].step()

                losses.append(float(loss.detach().cpu()))
                policy_losses.append(float(policy_loss.detach().cpu()))
                value_losses.append(float(value_loss.detach().cpu()))
                entropies.append(float(entropy_loss.detach().cpu()))
    return {
        "loss": float(np.mean(losses)),
        "policy_loss": float(np.mean(policy_losses)),
        "value_loss": float(np.mean(value_losses)),
        "entropy": float(np.mean(entropies)),
        "intent_loss": 0.0,
        "intent_acc": 0.0,
    }


def train_happo(cfg: RIGMAPPOConfig) -> Path:
    if cfg.env_name != "3d_intercept":
        raise ValueError("HAPPO baseline smoke currently supports only env_name=3d_intercept")
    set_seed(cfg.seed)
    device = torch.device(cfg.device)
    out_dir = Path(cfg.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    envs = make_envs(cfg)
    obs_list, share_list, graph_list = [], [], []
    for env in envs:
        obs, share_obs, graph = env.reset()
        obs_list.append(obs)
        share_list.append(share_obs)
        graph_list.append(graph)
    obs = np.stack(obs_list)
    share_obs = np.stack(share_list)
    graph_obs = stack_graphs(graph_list)
    sample_env = envs[0]
    sample_graph = graph_list[0]
    agent = HAPPOBaselineAgent(
        obs_dim=sample_env.obs_dim,
        node_feat_dim=sample_graph["node_feat"].shape[-1],
        edge_feat_dim=sample_graph["edge_feat"].shape[-1],
        share_obs_dim=sample_env.share_obs_dim,
        action_dim=sample_env.action_dim,
        num_agents=sample_env.num_agents,
        num_roles=max(5, int(np.max(sample_graph["role"])) + 1),
        hidden_dim=cfg.hidden_dim,
        role_dim=cfg.role_dim,
        intent_dim=cfg.intent_dim,
    ).to(device)
    optimizers = [optim.Adam(policy.parameters(), lr=cfg.lr, eps=1e-5) for policy in agent.policies]
    if cfg.resume:
        load_happo_training_checkpoint(agent, optimizers, cfg.resume, device)

    log_path = out_dir / "train_log.csv"
    fieldnames = [
        "update",
        "loss",
        "policy_loss",
        "value_loss",
        "entropy",
        "intent_loss",
        "intent_acc",
        "train_avg_reward",
        "eval_success_rate",
        "eval_collision_rate",
        "eval_timeout_rate",
        "eval_avg_steps",
        "eval_avg_distance",
        "eval_intent_acc",
    ]
    write_header = not (cfg.append_log and log_path.exists())
    mode = "a" if cfg.append_log else "w"
    with log_path.open(mode, newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        for local_update in range(1, cfg.updates + 1):
            update = cfg.update_offset + local_update
            batch = collect_rollout(agent, envs, obs, share_obs, graph_obs, cfg, device)
            obs, share_obs, graph_obs = batch["next_obs"], batch["next_share_obs"], batch["next_graph_obs"]
            train_info = update_happo_policy(agent, optimizers, batch, cfg, device)
            row = {"update": update, **train_info, "train_avg_reward": float(batch["rewards"].mean())}
            if update % cfg.eval_interval == 0 or update == 1:
                row.update(eval_policy(agent, cfg, base_seed=10_000 + update * 100))
                print(row, flush=True)
            else:
                row.update(
                    {
                        "eval_success_rate": "",
                        "eval_collision_rate": "",
                        "eval_timeout_rate": "",
                        "eval_avg_steps": "",
                        "eval_avg_distance": "",
                        "eval_intent_acc": "",
                    }
                )
            writer.writerow(row)
            f.flush()
            if update % cfg.save_interval == 0 or local_update == cfg.updates:
                torch.save(agent.state_dict(), out_dir / "happo_latest.pt")
                save_happo_training_checkpoint(out_dir / "happo_training_state_latest.pt", agent, optimizers, update)
                if cfg.save_snapshots:
                    torch.save(agent.state_dict(), out_dir / f"happo_update_{update:04d}.pt")
                    save_happo_training_checkpoint(
                        out_dir / f"happo_training_state_update_{update:04d}.pt",
                        agent,
                        optimizers,
                        update,
                    )
    return log_path


def parse_args() -> RIGMAPPOConfig:
    parser = argparse.ArgumentParser(description="Train a minimal no-graph HAPPO-style external baseline.")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--updates", type=int, default=1)
    parser.add_argument("--num-envs", type=int, default=1)
    parser.add_argument("--rollout-steps", type=int, default=8)
    parser.add_argument("--hidden-dim", type=int, default=64)
    parser.add_argument("--role-dim", type=int, default=8)
    parser.add_argument("--intent-dim", type=int, default=8)
    parser.add_argument("--intent-coef", type=float, default=0.0)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--entropy-coef", type=float, default=0.001)
    parser.add_argument("--eval-episodes", type=int, default=1)
    parser.add_argument("--eval-interval", type=int, default=1)
    parser.add_argument("--save-interval", type=int, default=1)
    parser.add_argument("--save-snapshots", action="store_true")
    parser.add_argument("--resume", type=str, default=None)
    parser.add_argument("--update-offset", type=int, default=0)
    parser.add_argument("--append-log", action="store_true")
    parser.add_argument("--target-policy", type=str, default="straight")
    parser.add_argument("--strict-target-sensing", action="store_true")
    parser.add_argument("--agent-target-info-bottleneck", action="store_true")
    parser.add_argument("--target-prior-position", type=float, nargs=3, default=(10_000.0, 0.0, 5_000.0))
    parser.add_argument("--communication-dropout-prob", type=float, default=0.0)
    parser.add_argument("--message-delay-steps", type=int, default=0)
    parser.add_argument("--failed-blue-agent", type=int, default=-1)
    parser.add_argument("--node-failure-start-step", type=int, default=0)
    parser.add_argument("--node-failure-duration-steps", type=int, default=0)
    parser.add_argument("--max-target-message-age-steps", type=int, default=80)
    parser.add_argument("--min-target-confidence", type=float, default=0.2)
    parser.add_argument("--safety-proximity-distance", type=float, default=0.0)
    parser.add_argument("--safety-proximity-penalty-weight", type=float, default=0.0)
    parser.add_argument("--device", type=str, default="cpu")
    parser.add_argument("--out-dir", type=str, default=str(ROOT / "results" / "happo_baseline_smoke"))
    args = parser.parse_args()
    return RIGMAPPOConfig(
        env_name="3d_intercept",
        seed=args.seed,
        updates=args.updates,
        num_envs=args.num_envs,
        rollout_steps=args.rollout_steps,
        hidden_dim=args.hidden_dim,
        role_dim=args.role_dim,
        intent_dim=args.intent_dim,
        graph_encoder="no_graph",
        lr=args.lr,
        entropy_coef=args.entropy_coef,
        intent_coef=args.intent_coef,
        eval_episodes=args.eval_episodes,
        eval_interval=args.eval_interval,
        save_interval=args.save_interval,
        save_snapshots=args.save_snapshots,
        resume=args.resume,
        update_offset=args.update_offset,
        append_log=args.append_log,
        target_policy=args.target_policy,
        strict_target_sensing=args.strict_target_sensing,
        agent_target_info_bottleneck=args.agent_target_info_bottleneck,
        target_prior_position=tuple(args.target_prior_position),
        communication_dropout_prob=args.communication_dropout_prob,
        message_delay_steps=args.message_delay_steps,
        failed_blue_agent=args.failed_blue_agent,
        node_failure_start_step=args.node_failure_start_step,
        node_failure_duration_steps=args.node_failure_duration_steps,
        max_target_message_age_steps=args.max_target_message_age_steps,
        min_target_confidence=args.min_target_confidence,
        safety_proximity_distance=args.safety_proximity_distance,
        safety_proximity_penalty_weight=args.safety_proximity_penalty_weight,
        device=args.device,
        out_dir=args.out_dir,
    )


def main() -> None:
    log_path = train_happo(parse_args())
    print(f"training log: {log_path}")


if __name__ == "__main__":
    main()
