"""Integrated rollout/update state for the active-diagnosis P3B pilot.

This module keeps the causal boundaries explicit:

* the actor samples a low-level action and stores its log probability;
* an external gate may replace one executed action and sets its attribution
  weight to zero;
* the critic and GAE use the real executed transition;
* complete training episodes, never evaluation episodes, supervise the task
  value estimator using the simulator hypothesis as a loss-row index only.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import random
from typing import Any

import numpy as np
import torch
from torch.nn.utils import clip_grad_norm_

from algorithms.active_diagnosis.pilot_gate_adapter import (
    FailureBelief,
    GateDecision,
    ProbeGate,
    apply_forced_options,
    policy_action_masks,
)
from algorithms.active_diagnosis.recurrent_sg_mappo import (
    RecurrentSGMAPPO,
    masked_clipped_actor_objective,
    replay_recurrent_sequence,
)
from algorithms.active_diagnosis.task_value_estimator import TaskValueEstimator, TaskValueReplayBuffer
from algorithms.redundant_topology_sg_mappo import gae
from envs.active_diagnosis_trainable_uav_env import (
    ActiveDiagnosisTrainableConfig,
    ActiveDiagnosisTrainableUAVEnv,
    HARD_TERMINAL_COMM_FAILURE,
    TRAINABLE_FAILURE_HYPOTHESES,
)


PILOT_ARMS = ("recurrent_mappo", "entropy_probe", "decision_relevant_probe")
OBSERVATION_KERNEL = np.asarray([[0.9, 0.1], [0.1, 0.9]], dtype=np.float64)


@dataclass(frozen=True)
class ActiveDiagnosisPPOConfig:
    rollout_steps: int = 64
    bptt_horizon: int = 16
    gamma: float = 0.99
    gae_lambda: float = 0.95
    clip_coef: float = 0.2
    entropy_coef: float = 0.01
    value_coef: float = 0.5
    max_grad_norm: float = 0.5
    ppo_epochs: int = 4


@dataclass
class EpisodeSupervisionState:
    initial_gate_observation: np.ndarray
    hypothesis_index: int
    total_return: float = 0.0
    fallback_used: bool = False


@dataclass
class ActiveDiagnosisRuntime:
    arm: str
    envs: list[ActiveDiagnosisTrainableUAVEnv]
    obs: np.ndarray
    share: np.ndarray
    graphs: list[dict[str, np.ndarray]]
    hidden: torch.Tensor
    episode_starts: np.ndarray
    gates: list[ProbeGate | None]
    pending_decisions: list[GateDecision | None]
    supervision: list[EpisodeSupervisionState]
    episode_counts: list[int]
    seed_base: int
    completed_episodes: int = 0


def _stack_graph(graphs: list[dict[str, np.ndarray]], key: str) -> np.ndarray:
    return np.stack([graph[key] for graph in graphs])


def _hypothesis_index(env: ActiveDiagnosisTrainableUAVEnv) -> int:
    return int(env.hypothesis == HARD_TERMINAL_COMM_FAILURE)


def make_runtime(
    arm: str,
    envs: list[ActiveDiagnosisTrainableUAVEnv],
    agent: RecurrentSGMAPPO,
    *,
    recoverable_prior: float,
    device: torch.device | str,
    seed_base: int = 100_000,
) -> ActiveDiagnosisRuntime:
    if arm not in PILOT_ARMS:
        raise ValueError(f"unknown pilot arm: {arm}")
    if not envs:
        raise ValueError("at least one environment is required")
    reset_rows = [env.reset() for env in envs]
    obs = np.stack([row[0] for row in reset_rows])
    share = np.stack([row[1] for row in reset_rows])
    graphs = [row[2] for row in reset_rows]
    gates: list[ProbeGate | None] = []
    for _ in envs:
        if arm == "recurrent_mappo":
            gates.append(None)
        else:
            gates.append(ProbeGate(
                "entropy" if arm == "entropy_probe" else "decision_relevant",
                FailureBelief(recoverable_prior, OBSERVATION_KERNEL),
                envs[0].config.probe_utility_cost,
            ))
    # The DVOI gate is executed by the relay and may only consume the relay's
    # deployment-legal actor observation.  Centralised ``share`` observations
    # remain critic-only and must never enter the task-value estimator.
    supervision = [
        EpisodeSupervisionState(obs[i, env.relay_id].copy(), _hypothesis_index(env))
        for i, env in enumerate(envs)
    ]
    return ActiveDiagnosisRuntime(
        arm=arm,
        envs=envs,
        obs=obs,
        share=share,
        graphs=graphs,
        hidden=agent.actor.initial_state(len(envs), envs[0].num_agents, device=device),
        episode_starts=np.ones(len(envs), dtype=bool),
        gates=gates,
        pending_decisions=[None for _ in envs],
        supervision=supervision,
        episode_counts=[0 for _ in envs],
        seed_base=int(seed_base),
    )


def _no_gate_decision() -> GateDecision:
    return GateDecision(False, False, 0.0, "actor_control")


def _decision_before_step(
    runtime: ActiveDiagnosisRuntime,
    env_index: int,
    estimator: TaskValueEstimator,
    device: torch.device,
) -> GateDecision:
    env = runtime.envs[env_index]
    gate = runtime.gates[env_index]
    if gate is None:
        return _no_gate_decision()
    if env.probe_remaining > 0:
        return GateDecision(True, False, 0.0, "probe_option_active")
    if env.fallback_remaining > 0:
        return GateDecision(False, True, 0.0, "fallback_option_active")
    pending = runtime.pending_decisions[env_index]
    if pending is not None:
        runtime.pending_decisions[env_index] = None
        return pending
    if runtime.episode_starts[env_index]:
        if runtime.arm == "decision_relevant_probe":
            state = torch.as_tensor(
                runtime.obs[env_index, env.relay_id][None], dtype=torch.float32, device=device
            )
            values = estimator.all_values(state).detach().cpu().numpy()[0]
            return gate.initial_decision(values)
        return gate.initial_decision()
    return _no_gate_decision()


def collect_rollout(
    agent: RecurrentSGMAPPO,
    estimator: TaskValueEstimator,
    task_replay: TaskValueReplayBuffer,
    runtime: ActiveDiagnosisRuntime,
    cfg: ActiveDiagnosisPPOConfig,
    *,
    device: torch.device | str = "cpu",
) -> dict[str, Any]:
    device = torch.device(device)
    initial_hidden = runtime.hidden.detach().clone()
    buffers: dict[str, list[Any]] = {name: [] for name in (
        "obs", "share", "roles", "adj", "policy_masks", "sampled_actions",
        "executed_actions", "old_log_prob", "values", "rewards", "dones",
        "episode_starts", "actor_control_mask",
    )}
    illegal_actions = 0
    for _ in range(cfg.rollout_steps):
        env_masks = _stack_graph(runtime.graphs, "action_masks")
        if runtime.arm == "recurrent_mappo":
            policy_masks = env_masks.copy()
        else:
            policy_masks = np.stack([
                policy_action_masks(mask, env.probe_action, env.fallback_action, env.neutral_action)
                for mask, env in zip(env_masks, runtime.envs)
            ])
        obs_t = torch.as_tensor(runtime.obs, dtype=torch.float32, device=device)
        share_t = torch.as_tensor(runtime.share, dtype=torch.float32, device=device)
        roles_t = torch.as_tensor(_stack_graph(runtime.graphs, "roles"), dtype=torch.long, device=device)
        adj_t = torch.as_tensor(_stack_graph(runtime.graphs, "active_adj"), dtype=torch.float32, device=device)
        masks_t = torch.as_tensor(policy_masks, dtype=torch.float32, device=device)
        starts_t = torch.as_tensor(runtime.episode_starts, dtype=torch.bool, device=device)
        hidden_before = torch.where(starts_t[:, None, None], torch.zeros_like(runtime.hidden), runtime.hidden)
        with torch.no_grad():
            sampled, log_prob, _, values, next_hidden, _ = agent.action_value_step(
                obs_t, roles_t, adj_t, masks_t, share_t, hidden_before
            )
        sampled_np = sampled.cpu().numpy()
        executed_rows, control_rows, decisions = [], [], []
        for i, env in enumerate(runtime.envs):
            decision = _decision_before_step(runtime, i, estimator, device)
            executed, control = apply_forced_options(
                sampled_np[i], decision, env.relay_id, env.attacker_id,
                env.probe_action, env.fallback_action,
            )
            illegal_actions += int(np.any(env_masks[i, np.arange(env.num_agents), executed] <= 0.0))
            executed_rows.append(executed)
            control_rows.append(control)
            decisions.append(decision)

        buffers["obs"].append(runtime.obs.copy())
        buffers["share"].append(runtime.share.copy())
        buffers["roles"].append(_stack_graph(runtime.graphs, "roles"))
        buffers["adj"].append(_stack_graph(runtime.graphs, "active_adj"))
        buffers["policy_masks"].append(policy_masks)
        buffers["sampled_actions"].append(sampled_np.copy())
        buffers["executed_actions"].append(np.stack(executed_rows))
        buffers["old_log_prob"].append(log_prob.cpu().numpy())
        buffers["values"].append(values.cpu().numpy())
        buffers["episode_starts"].append(runtime.episode_starts.copy())
        buffers["actor_control_mask"].append(np.stack(control_rows))

        next_obs_rows, next_share_rows, next_graphs = [], [], []
        reward_rows, done_rows = [], []
        next_episode_starts = np.zeros(len(runtime.envs), dtype=bool)
        for i, (env, executed) in enumerate(zip(runtime.envs, executed_rows)):
            next_obs, next_share, next_graph, reward, done, info = env.step(executed)
            reward_vector = np.asarray(reward, dtype=np.float32).reshape(env.num_agents, -1)[:, 0]
            terminal = bool(np.asarray(done).all())
            runtime.supervision[i].total_return += float(reward_vector[0])
            runtime.supervision[i].fallback_used |= bool(info["fallback_count"] > 0)
            gate = runtime.gates[i]
            if gate is not None and float(info["probe_ack_state"]) != gate.last_ack_state and not info["probe_active"]:
                runtime.pending_decisions[i] = gate.completed_probe_decision(float(info["probe_ack_state"]))
            if terminal:
                episode = runtime.supervision[i]
                task_replay.add(
                    episode.initial_gate_observation,
                    episode.hypothesis_index,
                    int(episode.fallback_used),
                    episode.total_return,
                )
                runtime.completed_episodes += 1
                runtime.episode_counts[i] += 1
                env.seed(runtime.seed_base + i * 100_000 + runtime.episode_counts[i])
                next_obs, next_share, next_graph = env.reset()
                if gate is not None:
                    gate.reset()
                runtime.pending_decisions[i] = None
                runtime.supervision[i] = EpisodeSupervisionState(
                    next_obs[env.relay_id].copy(), _hypothesis_index(env)
                )
                next_episode_starts[i] = True
            next_obs_rows.append(next_obs)
            next_share_rows.append(next_share)
            next_graphs.append(next_graph)
            reward_rows.append(reward_vector)
            done_rows.append(terminal)
        buffers["rewards"].append(np.stack(reward_rows))
        buffers["dones"].append(np.asarray(done_rows, dtype=np.float32))
        runtime.obs = np.stack(next_obs_rows)
        runtime.share = np.stack(next_share_rows)
        runtime.graphs = next_graphs
        runtime.hidden = next_hidden.detach()
        runtime.episode_starts = next_episode_starts

    batch = {name: np.stack(rows) for name, rows in buffers.items()}
    batch["initial_hidden"] = initial_hidden.detach().cpu().numpy()
    batch["next_share"] = runtime.share.copy()
    batch["illegal_executed_actions"] = illegal_actions
    return batch


def update_from_rollout(
    agent: RecurrentSGMAPPO,
    optimizer: torch.optim.Optimizer,
    batch: dict[str, Any],
    cfg: ActiveDiagnosisPPOConfig,
    *,
    device: torch.device | str = "cpu",
) -> dict[str, float]:
    device = torch.device(device)
    with torch.no_grad():
        bootstrap = agent.critic(torch.as_tensor(batch["next_share"], dtype=torch.float32, device=device)).squeeze(-1)
    advantages, returns = gae(
        batch["rewards"], batch["dones"][..., None], batch["values"],
        bootstrap.cpu().numpy(), cfg.gamma, cfg.gae_lambda,
    )
    advantages_t = torch.as_tensor(advantages, dtype=torch.float32, device=device)
    controlled = torch.as_tensor(batch["actor_control_mask"], dtype=torch.float32, device=device)
    controlled_values = advantages_t[controlled > 0]
    advantages_t = (advantages_t - controlled_values.mean()) / (controlled_values.std() + 1e-8)
    returns_t = torch.as_tensor(returns, dtype=torch.float32, device=device)
    tensors = {
        "obs": torch.as_tensor(batch["obs"], dtype=torch.float32, device=device),
        "share": torch.as_tensor(batch["share"], dtype=torch.float32, device=device),
        "roles": torch.as_tensor(batch["roles"], dtype=torch.long, device=device),
        "adj": torch.as_tensor(batch["adj"], dtype=torch.float32, device=device),
        "masks": torch.as_tensor(batch["policy_masks"], dtype=torch.float32, device=device),
        "actions": torch.as_tensor(batch["sampled_actions"], dtype=torch.long, device=device),
        "starts": torch.as_tensor(batch["episode_starts"], dtype=torch.bool, device=device),
        "old_log_prob": torch.as_tensor(batch["old_log_prob"], dtype=torch.float32, device=device),
        "initial_hidden": torch.as_tensor(batch["initial_hidden"], dtype=torch.float32, device=device),
    }
    metrics = []
    for _ in range(cfg.ppo_epochs):
        replay = replay_recurrent_sequence(
            agent, obs=tensors["obs"], roles=tensors["roles"], adj=tensors["adj"],
            masks=tensors["masks"], share=tensors["share"], sampled_actions=tensors["actions"],
            episode_starts=tensors["starts"], initial_hidden=tensors["initial_hidden"],
            bptt_horizon=cfg.bptt_horizon,
        )
        actor_loss = masked_clipped_actor_objective(
            replay, tensors["old_log_prob"], advantages_t, controlled,
            cfg.clip_coef, cfg.entropy_coef,
        )
        value_loss = 0.5 * (returns_t - replay.values).square().mean()
        loss = actor_loss + cfg.value_coef * value_loss
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        grad_norm = clip_grad_norm_(agent.parameters(), cfg.max_grad_norm)
        optimizer.step()
        metrics.append((actor_loss.detach(), value_loss.detach(), grad_norm.detach()))
    values = torch.stack([torch.stack(row) for row in metrics]).cpu().numpy()
    return {
        "actor_loss": float(values[:, 0].mean()),
        "value_loss": float(values[:, 1].mean()),
        "gradient_norm": float(values[:, 2].mean()),
        "controlled_fraction": float(batch["actor_control_mask"].mean()),
    }


def update_task_value_estimator(
    estimator: TaskValueEstimator,
    optimizer: torch.optim.Optimizer,
    replay: TaskValueReplayBuffer,
    *,
    batch_size: int = 32,
    gradient_steps: int = 1,
    device: torch.device | str = "cpu",
) -> float | None:
    if len(replay) < batch_size:
        return None
    losses = []
    for _ in range(gradient_steps):
        batch = replay.sample(batch_size, device)
        estimator.normalizer.update(batch.states)
        optimizer.zero_grad(set_to_none=True)
        loss = estimator.supervised_loss(
            batch.states, batch.hypothesis_indices, batch.option_indices, batch.returns
        )
        loss.backward()
        optimizer.step()
        losses.append(float(loss.detach().cpu()))
    return float(np.mean(losses))


def collect_task_value_calibration_episode(
    agent: RecurrentSGMAPPO,
    *,
    hypothesis: str,
    recovery_option: int,
    seed: int,
    gamma: float = 0.99,
    device: torch.device | str = "cpu",
) -> dict[str, Any]:
    """Collect one fixed-policy, probe-then-recovery calibration episode.

    Option 0 leaves recovery to the recurrent low-level policy after the
    diagnostic maneuver. Option 1 executes the frozen prior-guided fallback.
    The target excludes all rewards up to and including probe completion, so
    the gate can subtract the physical probe cost exactly once.
    """
    if hypothesis not in TRAINABLE_FAILURE_HYPOTHESES or recovery_option not in (0, 1):
        raise ValueError("invalid calibration cell")
    device = torch.device(device)
    env = ActiveDiagnosisTrainableUAVEnv(ActiveDiagnosisTrainableConfig(hypothesis, int(seed)))
    obs, share, graph = env.reset()
    initial_gate_observation = obs[env.relay_id].copy()
    hidden = agent.actor.initial_state(1, env.num_agents, device=device)
    discount = 1.0
    target_return = 0.0
    steps = 0
    final_info: dict[str, Any] = {}
    while not env.done:
        masks = policy_action_masks(
            graph["action_masks"], env.probe_action, env.fallback_action, env.neutral_action
        )
        with torch.no_grad():
            sampled, _, _, _, hidden, _ = agent.action_value_step(
                torch.as_tensor(obs[None], dtype=torch.float32, device=device),
                torch.as_tensor(graph["roles"][None], dtype=torch.long, device=device),
                torch.as_tensor(graph["active_adj"][None], dtype=torch.float32, device=device),
                torch.as_tensor(masks[None], dtype=torch.float32, device=device),
                torch.as_tensor(share[None], dtype=torch.float32, device=device),
                hidden,
                deterministic=True,
            )
        executed = sampled[0].cpu().numpy()
        if env.probe_count == 0 or env.probe_remaining > 0:
            executed[env.relay_id] = env.probe_action
        elif recovery_option == 1 and (env.fallback_count == 0 or env.fallback_remaining > 0):
            executed[env.attacker_id] = env.fallback_action
        probe_was_complete = env.probe_ack_state != 0.0
        obs, share, graph, reward, done, final_info = env.step(executed)
        if probe_was_complete:
            target_return += discount * float(np.asarray(reward).reshape(env.num_agents, -1)[0, 0])
            discount *= gamma
        steps += 1
        if bool(np.asarray(done).all()):
            break
    return {
        "state": initial_gate_observation,
        "hypothesis_index": _hypothesis_index(env),
        "recovery_option": int(recovery_option),
        "discounted_post_probe_return": float(target_return),
        "steps": steps,
        "success": float(final_info.get("success", 0.0)),
        "timeout": float(final_info.get("timeout", 0.0)),
        "collision": float(final_info.get("collision", 0.0)),
        "constraint_violation": float(final_info.get("constraint_violation", 0.0)),
    }


def calibrate_task_value_estimator(
    agent: RecurrentSGMAPPO,
    estimator: TaskValueEstimator,
    optimizer: torch.optim.Optimizer,
    *,
    geometry_seeds: list[int] | tuple[int, ...],
    train_geometry_count: int,
    gradient_steps: int = 600,
    gamma: float = 0.99,
    device: torch.device | str = "cpu",
) -> dict[str, Any]:
    """Fit and validate the frozen 2x2 recovery-value calibration grid."""
    actor_before = {key: value.detach().cpu().clone() for key, value in agent.state_dict().items()}
    seeds = [int(seed) for seed in geometry_seeds]
    if not 0 < train_geometry_count < len(seeds):
        raise ValueError("calibration requires disjoint train and validation geometries")
    records_by_seed: dict[int, list[dict[str, Any]]] = {}
    for seed in seeds:
        records_by_seed[seed] = [
            collect_task_value_calibration_episode(
                agent, hypothesis=hypothesis, recovery_option=option,
                seed=seed, gamma=gamma, device=device,
            )
            for hypothesis in TRAINABLE_FAILURE_HYPOTHESES
            for option in (0, 1)
        ]
    replay = TaskValueReplayBuffer(estimator.state_dim, capacity=4 * train_geometry_count, seed=seeds[0])
    for seed in seeds[:train_geometry_count]:
        for record in records_by_seed[seed]:
            replay.add(
                record["state"], record["hypothesis_index"], record["recovery_option"],
                record["discounted_post_probe_return"],
            )
    all_train_states = torch.as_tensor(
        np.stack([record[0] for record in replay.state_dict()["records"]]),
        dtype=torch.float32,
        device=device,
    )
    estimator.normalizer.update(all_train_states)
    final_loss = None
    batch_size = min(32, len(replay))
    for _ in range(int(gradient_steps)):
        batch = replay.sample(batch_size, device)
        optimizer.zero_grad(set_to_none=True)
        loss = estimator.supervised_loss(
            batch.states, batch.hypothesis_indices, batch.option_indices, batch.returns
        )
        loss.backward()
        optimizer.step()
        final_loss = float(loss.detach().cpu())
    validation_rows = []
    decision_matches = []
    empirical_probe_by_prior = {"0.5": [], "0.9": []}
    predicted_probe_by_prior = {"0.5": [], "0.9": []}
    absolute_errors = []
    for seed in seeds[train_geometry_count:]:
        records = records_by_seed[seed]
        target = np.empty((2, 2), dtype=np.float32)
        for record in records:
            target[record["hypothesis_index"], record["recovery_option"]] = record[
                "discounted_post_probe_return"
            ]
        state = torch.as_tensor(records[0]["state"][None], dtype=torch.float32, device=device)
        predicted = estimator.all_values(state).detach().cpu().numpy()[0]
        absolute_errors.extend(np.abs(predicted - target).reshape(-1).tolist())
        decisions = {}
        for prior in (0.5, 0.9):
            predicted_decision = ProbeGate(
                "decision_relevant", FailureBelief(prior, OBSERVATION_KERNEL), 0.12
            ).initial_decision(predicted)
            target_decision = ProbeGate(
                "decision_relevant", FailureBelief(prior, OBSERVATION_KERNEL), 0.12
            ).initial_decision(target)
            match = predicted_decision.force_probe == target_decision.force_probe
            decision_matches.append(match)
            empirical_probe_by_prior[str(prior)].append(target_decision.force_probe)
            predicted_probe_by_prior[str(prior)].append(predicted_decision.force_probe)
            decisions[str(prior)] = {
                "predicted_probe": predicted_decision.force_probe,
                "empirical_probe": target_decision.force_probe,
                "match": match,
            }
        validation_rows.append({
            "seed": seed,
            "target": target.tolist(),
            "predicted": predicted.tolist(),
            "decisions": decisions,
        })
    return {
        "protocol": "ACTIVE-DIAGNOSIS-TASK-VALUE-CALIBRATION-V1",
        "geometry_seeds": seeds,
        "train_geometry_count": train_geometry_count,
        "validation_geometry_count": len(seeds) - train_geometry_count,
        "episodes": 4 * len(seeds),
        "environment_steps": int(sum(
            record["steps"] for records in records_by_seed.values() for record in records
        )),
        "final_training_loss": final_loss,
        "validation_mean_absolute_error": float(np.mean(absolute_errors)),
        "validation_gate_decision_agreement": float(np.mean(decision_matches)),
        "validation_empirical_probe_rate": {
            prior: float(np.mean(values)) for prior, values in empirical_probe_by_prior.items()
        },
        "validation_predicted_probe_rate": {
            prior: float(np.mean(values)) for prior, values in predicted_probe_by_prior.items()
        },
        "decision_relevant_balanced_prior_present": bool(any(empirical_probe_by_prior["0.5"])),
        "validation": validation_rows,
        "replay": replay,
        "records": records_by_seed,
        "ppo_updates": 0,
        "actor_parameters_changed": any(
            not torch.equal(actor_before[key], agent.state_dict()[key].detach().cpu())
            for key in actor_before
        ),
    }


def evaluate_episode(
    agent: RecurrentSGMAPPO,
    estimator: TaskValueEstimator,
    *,
    arm: str,
    hypothesis: str,
    seed: int,
    recoverable_prior: float,
    device: torch.device | str = "cpu",
) -> dict[str, Any]:
    """Deterministic fixed-endpoint episode with the training information boundary."""
    device = torch.device(device)
    env = ActiveDiagnosisTrainableUAVEnv(ActiveDiagnosisTrainableConfig(hypothesis, int(seed)))
    runtime = make_runtime(
        arm, [env], agent, recoverable_prior=recoverable_prior,
        device=device, seed_base=int(seed) * 10,
    )
    total_return = 0.0
    final_info: dict[str, Any] = {}
    while not env.done:
        env_masks = runtime.graphs[0]["action_masks"]
        masks = env_masks if arm == "recurrent_mappo" else policy_action_masks(
            env_masks, env.probe_action, env.fallback_action, env.neutral_action
        )
        starts = torch.as_tensor(runtime.episode_starts, dtype=torch.bool, device=device)
        hidden = torch.where(starts[:, None, None], torch.zeros_like(runtime.hidden), runtime.hidden)
        with torch.no_grad():
            sampled, _, _, _, next_hidden, _ = agent.action_value_step(
                torch.as_tensor(runtime.obs, dtype=torch.float32, device=device),
                torch.as_tensor(runtime.graphs[0]["roles"][None], dtype=torch.long, device=device),
                torch.as_tensor(runtime.graphs[0]["active_adj"][None], dtype=torch.float32, device=device),
                torch.as_tensor(masks[None], dtype=torch.float32, device=device),
                torch.as_tensor(runtime.share, dtype=torch.float32, device=device),
                hidden,
                deterministic=True,
            )
        decision = _decision_before_step(runtime, 0, estimator, device)
        executed, _ = apply_forced_options(
            sampled[0].cpu().numpy(), decision, env.relay_id, env.attacker_id,
            env.probe_action, env.fallback_action,
        )
        if np.any(env_masks[np.arange(env.num_agents), executed] <= 0.0):
            raise AssertionError("evaluation attempted an illegal action")
        obs, share, graph, reward, done, final_info = env.step(executed)
        total_return += float(np.asarray(reward).reshape(env.num_agents, -1)[0, 0])
        gate = runtime.gates[0]
        if gate is not None and float(final_info["probe_ack_state"]) != gate.last_ack_state and not final_info["probe_active"]:
            runtime.pending_decisions[0] = gate.completed_probe_decision(float(final_info["probe_ack_state"]))
        runtime.obs = obs[None]
        runtime.share = share[None]
        runtime.graphs = [graph]
        runtime.hidden = next_hidden.detach()
        runtime.episode_starts[:] = False
        if bool(np.asarray(done).all()):
            break
    return {
        "return": total_return,
        "success": float(final_info["success"]),
        "timeout": float(final_info["timeout"]),
        "collision": float(final_info["collision"]),
        "constraint_violation": float(final_info["constraint_violation"]),
        "steps": int(env.step_count),
        "probe_count": int(env.probe_count),
        "fallback_count": int(env.fallback_count),
    }


def runtime_state_dict(runtime: ActiveDiagnosisRuntime) -> dict[str, Any]:
    return {
        "format": "active_diagnosis_pilot_runtime_v1",
        "arm": runtime.arm,
        "environment_states": [env.runtime_state_dict() for env in runtime.envs],
        "obs": runtime.obs.copy(),
        "share": runtime.share.copy(),
        "graphs": deepcopy(runtime.graphs),
        "hidden": runtime.hidden.detach().cpu().clone(),
        "episode_starts": runtime.episode_starts.copy(),
        "gates": [None if gate is None else gate.state_dict() for gate in runtime.gates],
        "pending_decisions": deepcopy(runtime.pending_decisions),
        "supervision": deepcopy(runtime.supervision),
        "episode_counts": list(runtime.episode_counts),
        "seed_base": runtime.seed_base,
        "completed_episodes": runtime.completed_episodes,
        "rng": {
            "python": random.getstate(),
            "numpy": np.random.get_state(),
            "torch": torch.get_rng_state(),
        },
    }


def load_runtime_state_dict(runtime: ActiveDiagnosisRuntime, state: dict[str, Any]) -> None:
    if state.get("format") != "active_diagnosis_pilot_runtime_v1" or state.get("arm") != runtime.arm:
        raise ValueError("incompatible active-diagnosis pilot runtime")
    if len(state["environment_states"]) != len(runtime.envs):
        raise ValueError("environment count differs")
    for env, env_state in zip(runtime.envs, state["environment_states"]):
        env.load_runtime_state_dict(deepcopy(env_state))
    runtime.obs = np.asarray(state["obs"], dtype=np.float32).copy()
    runtime.share = np.asarray(state["share"], dtype=np.float32).copy()
    runtime.graphs = deepcopy(state["graphs"])
    runtime.hidden = state["hidden"].clone().to(runtime.hidden.device)
    runtime.episode_starts = np.asarray(state["episode_starts"], dtype=bool).copy()
    for gate, gate_state in zip(runtime.gates, state["gates"]):
        if gate is None:
            if gate_state is not None:
                raise ValueError("ungated arm received gate state")
        else:
            gate.load_state_dict(gate_state)
    runtime.pending_decisions = deepcopy(state["pending_decisions"])
    runtime.supervision = deepcopy(state["supervision"])
    runtime.episode_counts = [int(value) for value in state["episode_counts"]]
    runtime.seed_base = int(state["seed_base"])
    runtime.completed_episodes = int(state["completed_episodes"])
    random.setstate(state["rng"]["python"])
    np.random.set_state(state["rng"]["numpy"])
    torch.set_rng_state(state["rng"]["torch"])
