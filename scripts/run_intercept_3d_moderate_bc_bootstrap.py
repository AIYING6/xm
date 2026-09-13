"""Behavior-clone a legal local controller for the calibrated 3DOF moderate band.

This is a development-only learnability bootstrap.  The teacher reads exactly
the emitted local observation used by the actor; it never reads simulator
state.  The generated checkpoint is compatible with the plain-MAPPO runner.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.simple_ri_gmappo import RIGMAPPOAgent, RIGMAPPOConfig, eval_policy, make_env, stack_graphs  # noqa: E402
from audit_intercept_3d_legal_baseline import legal_actions  # noqa: E402


PROTOCOL = "INTERCEPT-3D-MODERATE-LOCAL-BC-BOOTSTRAP-V1"
CONDITION = {"target_policy": "weaving_mild", "communication_dropout_prob": 0.25, "radar_dropout_prob": 0.15, "message_delay_steps": 4}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=5102)
    parser.add_argument(
        "--hidden-dim",
        type=int,
        default=64,
        help="Shared actor/critic width. Use only for predeclared capacity-matched development controls.",
    )
    parser.add_argument("--episodes", type=int, default=80)
    parser.add_argument("--epochs", type=int, default=40)
    parser.add_argument("--batch-size", type=int, default=1024)
    parser.add_argument("--learning-rate", type=float, default=3e-4)
    parser.add_argument("--dagger-rounds", type=int, default=5)
    parser.add_argument("--dagger-episodes-per-round", type=int, default=12)
    parser.add_argument("--dagger-epochs", type=int, default=10)
    parser.add_argument("--eval-episodes", type=int, default=60)
    parser.add_argument(
        "--graph-encoder",
        choices=("no_graph", "local_relation"),
        default="no_graph",
        help="Actor representation; local_relation rebuilds its graph solely from focal local observations.",
    )
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "results" / "development" / "intercept_3d_moderate_bc_bootstrap" / "seed5102")
    parser.add_argument("--execute", action="store_true")
    return parser.parse_args()


def config(args: argparse.Namespace) -> RIGMAPPOConfig:
    return RIGMAPPOConfig(
        env_name="3d_intercept", seed=args.seed, hidden_dim=args.hidden_dim, graph_encoder=args.graph_encoder, role_gate_mode="none",
        intent_coef=0.0, chain_aux_coef=0.0, strict_target_sensing=False, agent_target_info_bottleneck=False,
        relay_dependent_task=False, eval_episodes=args.eval_episodes, device=args.device, **CONDITION,
    )


def build_agent(cfg: RIGMAPPOConfig) -> RIGMAPPOAgent:
    env = make_env(cfg, cfg.seed, training=False)
    _, share, graph = env.reset()
    return RIGMAPPOAgent(
        obs_dim=env.obs_dim, node_feat_dim=graph["node_feat"].shape[-1], edge_feat_dim=graph["edge_feat"].shape[-1],
        share_obs_dim=share.shape[-1], action_dim=env.action_dim, num_agents=env.num_agents,
        num_roles=max(4, int(np.max(graph["role"])) + 1), hidden_dim=cfg.hidden_dim, role_dim=cfg.role_dim,
        intent_dim=cfg.intent_dim, graph_encoder=cfg.graph_encoder, role_gate_mode="none", use_intent_context=False,
    ).to(cfg.device)


def collect_teacher_data(cfg: RIGMAPPOConfig, episodes: int) -> tuple[np.ndarray, np.ndarray]:
    features: list[np.ndarray] = []; labels: list[np.ndarray] = []
    for episode in range(episodes):
        env = make_env(cfg, 710_000 + episode, training=False)
        obs, _, _ = env.reset()
        while True:
            actions = legal_actions(obs)
            features.append(obs.copy()); labels.append(actions.copy())
            obs, _, _, _, dones, _ = env.step(actions)
            if bool(np.all(dones)):
                break
    return np.concatenate(features, axis=0).astype(np.float32), np.concatenate(labels, axis=0).astype(np.int64)


def actor_logits(agent: RIGMAPPOAgent, obs: torch.Tensor) -> torch.Tensor:
    """No-graph actor only consumes local observations; placeholders preserve its public interface."""
    batch, agents = obs.shape[:2]
    nodes = agents + 1
    device = obs.device
    node_dim = agent.actor.input[0].in_features - agent.actor.role_emb.embedding_dim
    return agent.actor(
        obs, torch.zeros((batch, nodes, node_dim), device=device), torch.zeros((batch, nodes, nodes, 1), device=device),
        torch.zeros((batch, nodes), dtype=torch.long, device=device), torch.eye(nodes, device=device).expand(batch, -1, -1),
        agents, relation_adj=torch.zeros((batch, 3, nodes, nodes), device=device),
    )[0]


def collect_learner_labeled_data(
    agent: RIGMAPPOAgent, cfg: RIGMAPPOConfig, *, round_id: int, episodes: int
) -> tuple[np.ndarray, np.ndarray]:
    """Collect states induced by the learner, while retaining legal teacher labels.

    The executed action is the learner's deterministic action.  The label is
    queried from precisely the same emitted observation, so this adds no
    simulator-state information to the actor.
    """
    features: list[np.ndarray] = []; labels: list[np.ndarray] = []
    agent.eval(); device = next(agent.parameters()).device
    with torch.no_grad():
        for episode in range(episodes):
            env = make_env(cfg, 730_000 + 10_000 * round_id + episode, training=False)
            obs, _, _ = env.reset()
            while True:
                features.append(obs.copy()); labels.append(legal_actions(obs).copy())
                action = actor_logits(agent, torch.as_tensor(obs[None], dtype=torch.float32, device=device)).argmax(dim=-1)
                obs, _, _, _, dones, _ = env.step(action.squeeze(0).cpu().numpy())
                if bool(np.all(dones)):
                    break
    return np.concatenate(features, axis=0).astype(np.float32), np.concatenate(labels, axis=0).astype(np.int64)


def fit_actor(
    agent: RIGMAPPOAgent, optimizer: torch.optim.Optimizer, x: torch.Tensor, y: torch.Tensor,
    *, epochs: int, batch_size: int, phase: str, round_id: int,
) -> list[dict[str, float | int | str]]:
    rows: list[dict[str, float | int | str]] = []
    agent.train()
    for epoch in range(1, epochs + 1):
        order = torch.randperm(len(x), device=x.device); losses: list[float] = []; correct = 0; count = 0
        for start in range(0, len(x), batch_size):
            index = order[start:start + batch_size]; logits = actor_logits(agent, x[index])
            loss = F.cross_entropy(logits.reshape(-1, agent.action_dim), y[index].reshape(-1))
            optimizer.zero_grad(); loss.backward(); torch.nn.utils.clip_grad_norm_(agent.actor.parameters(), 0.5); optimizer.step()
            losses.append(float(loss.detach())); correct += int((logits.argmax(dim=-1) == y[index]).sum()); count += int(y[index].numel())
        rows.append({"phase": phase, "round": round_id, "epoch": epoch, "cross_entropy": float(np.mean(losses)), "action_accuracy": correct / count, "dataset_agent_states": int(len(x) * 3)})
    return rows


def main() -> None:
    args = parse_args()
    if not args.execute:
        raise SystemExit("This bootstrap writes a checkpoint; pass --execute.")
    if args.out_dir.exists() and any(args.out_dir.iterdir()):
        raise FileExistsError(f"refusing to overwrite existing bootstrap: {args.out_dir}")
    if min(args.episodes, args.epochs, args.batch_size, args.dagger_rounds, args.dagger_episodes_per_round, args.dagger_epochs) <= 0:
        raise ValueError("all collection, training, and DAgger counts must be positive")
    args.out_dir.mkdir(parents=True, exist_ok=False)
    torch.manual_seed(args.seed); np.random.seed(args.seed)
    cfg = config(args)
    obs, actions = collect_teacher_data(cfg, args.episodes)
    agent = build_agent(cfg); optimizer = torch.optim.Adam(agent.actor.parameters(), lr=args.learning_rate)
    device = torch.device(args.device)
    x = torch.as_tensor(obs.reshape(-1, 3, obs.shape[-1]), device=device); y = torch.as_tensor(actions.reshape(-1, 3), device=device)
    rows = fit_actor(agent, optimizer, x, y, epochs=args.epochs, batch_size=args.batch_size, phase="behavior_cloning", round_id=0)
    for round_id in range(1, args.dagger_rounds + 1):
        learner_obs, teacher_actions = collect_learner_labeled_data(agent, cfg, round_id=round_id, episodes=args.dagger_episodes_per_round)
        x = torch.cat((x, torch.as_tensor(learner_obs.reshape(-1, 3, learner_obs.shape[-1]), device=device)), dim=0)
        y = torch.cat((y, torch.as_tensor(teacher_actions.reshape(-1, 3), device=device)), dim=0)
        rows.extend(fit_actor(agent, optimizer, x, y, epochs=args.dagger_epochs, batch_size=args.batch_size, phase="dagger", round_id=round_id))
    with (args.out_dir / "bc_train_log.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    checkpoint = args.out_dir / "actor_critic_bc_init.pt"; torch.save(agent.state_dict(), checkpoint)
    endpoint = eval_policy(agent, cfg, base_seed=720_000)
    with (args.out_dir / "endpoint_evaluation.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=("protocol", "seed", "teacher_episodes", "teacher_samples", *endpoint)); writer.writeheader()
        writer.writerow({"protocol": PROTOCOL, "seed": args.seed, "teacher_episodes": args.episodes, "teacher_samples": len(obs), **endpoint})
    manifest = {"protocol": PROTOCOL, "artifact_class": "DEVELOPMENT_ONLY_LOCAL_OBSERVATION_BC_BOOTSTRAP", "paper_evidence": False,
                "teacher": "legal_actions(local_emitted_observation_only)", "graph_encoder": args.graph_encoder,
                "hidden_dim": args.hidden_dim,
                "condition": CONDITION, "seed": args.seed,
                "teacher_episodes": args.episodes, "teacher_samples": int(len(obs)), "bc_epochs": args.epochs,
                "dagger_rounds": args.dagger_rounds, "dagger_episodes_per_round": args.dagger_episodes_per_round,
                "dagger_epochs": args.dagger_epochs, "final_dataset_agent_states": int(len(x) * 3),
                "checkpoint": checkpoint.name, "endpoint": endpoint, "status": "completed"}
    (args.out_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
