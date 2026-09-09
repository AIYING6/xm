"""P3A trainable-interface gate; this is a smoke audit, not performance training."""

from __future__ import annotations

import argparse
import json
import sys
from copy import deepcopy
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from algorithms.redundant_topology_sg_mappo import SGMPPO
from envs.active_diagnosis_semantic_env import RECOVERABLE_RANGE_LOSS
from envs.active_diagnosis_trainable_uav_env import (
    ActiveDiagnosisTrainableConfig,
    ActiveDiagnosisTrainableUAVEnv,
    HARD_TERMINAL_COMM_FAILURE,
)


def _tensor_inputs(obs, share, graph):
    return (
        torch.as_tensor(obs[None], dtype=torch.float32),
        torch.as_tensor(graph["roles"][None], dtype=torch.long),
        torch.as_tensor(graph["active_adj"][None], dtype=torch.float32),
        torch.as_tensor(graph["action_masks"][None], dtype=torch.float32),
        # The independent masked SG-MAPPO smoke learner uses one centralized
        # state vector per graph.  The environment follows the repository's
        # standard interface and tiles that vector per agent, so select one
        # identical row at this adapter boundary.
        torch.as_tensor(share[0][None], dtype=torch.float32),
    )


def _run_probe(env: ActiveDiagnosisTrainableUAVEnv) -> tuple[float, bool]:
    _, _, graph = env.reset()
    for _ in range(env.config.probe_duration_steps):
        actions = np.full(env.num_agents, env.neutral_action, dtype=np.int64)
        actions[env.relay_id] = env.probe_action
        _, _, graph, _, _, info = env.step(actions)
        assert graph["action_masks"][env.relay_id, env.probe_action] == float(info["probe_active"])
    return float(info["probe_ack_state"]), bool(env.done)


def run_gate() -> dict:
    recoverable = ActiveDiagnosisTrainableUAVEnv(
        ActiveDiagnosisTrainableConfig(hypothesis=RECOVERABLE_RANGE_LOSS, seed=7301)
    )
    hard = ActiveDiagnosisTrainableUAVEnv(
        ActiveDiagnosisTrainableConfig(hypothesis=HARD_TERMINAL_COMM_FAILURE, seed=7301)
    )
    r_obs, r_share, r_graph = recoverable.reset()
    h_obs, h_share, h_graph = hard.reset()
    pre_probe_equal = bool(
        np.array_equal(r_obs, h_obs)
        and np.array_equal(r_share, h_share)
        and all(np.array_equal(r_graph[k], h_graph[k]) for k in r_graph)
    )
    interface_shapes = bool(
        r_obs.shape == (3, recoverable.obs_dim)
        and r_share.shape == (3, recoverable.share_obs_dim)
        and r_graph["node_features"].shape == (3, recoverable.obs_dim)
        and r_graph["active_adj"].shape == (3, 3)
        and r_graph["action_masks"].shape == (3, recoverable.action_dim)
    )
    initial_masks = r_graph["action_masks"]
    mask_contract = bool(
        initial_masks[recoverable.relay_id, recoverable.probe_action] == 1
        and initial_masks[0, recoverable.probe_action] == 0
        and initial_masks[2, recoverable.probe_action] == 0
        and initial_masks[recoverable.attacker_id, recoverable.fallback_action] == 1
        and initial_masks[0, recoverable.fallback_action] == 0
        and initial_masks[recoverable.relay_id, recoverable.fallback_action] == 0
        and np.all(initial_masks[:, : recoverable.flight_action_dim] == 1)
    )

    recoverable_ack, recoverable_done = _run_probe(recoverable)
    hard_ack, hard_done = _run_probe(hard)
    post_probe_separation = recoverable_ack == 1.0 and hard_ack == -1.0
    completion_before_terminal = not recoverable_done and not hard_done

    envs = [
        ActiveDiagnosisTrainableUAVEnv(ActiveDiagnosisTrainableConfig(hypothesis=hyp, seed=7400 + i))
        for i, hyp in enumerate((RECOVERABLE_RANGE_LOSS, HARD_TERMINAL_COMM_FAILURE))
    ]
    agent = SGMPPO(envs[0].obs_dim, envs[0].share_obs_dim, envs[0].action_dim)
    optimizer = torch.optim.Adam(agent.parameters(), lr=3e-4)
    samples = []
    illegal = 0
    smoke_steps = 0
    for env in envs:
        obs, share, graph = env.reset()
        for _ in range(4):
            action, old_logp, entropy, value = agent.action_value(*_tensor_inputs(obs, share, graph))
            action_np = action[0].detach().cpu().numpy()
            illegal += int(np.any(graph["action_masks"][np.arange(env.num_agents), action_np] <= 0))
            next_obs, next_share, next_graph, reward, done, _ = env.step(action_np)
            samples.append((obs, share, graph, action[0], old_logp[0], reward[:, 0], value[0], entropy[0]))
            obs, share, graph = next_obs, next_share, next_graph
            smoke_steps += 1
            if bool(done.all()):
                obs, share, graph = env.reset()

    optimizer.zero_grad()
    losses = []
    for obs, share, graph, action, old_logp, reward, value, _ in samples:
        _, logp, entropy, new_value = agent.action_value(*_tensor_inputs(obs, share, graph), action=action[None])
        advantage = torch.as_tensor(reward, dtype=torch.float32)[None] - value.detach()
        ratio = torch.exp(logp - old_logp.detach()[None])
        policy_loss = -(ratio * advantage).mean()
        value_loss = 0.5 * (new_value - torch.as_tensor(reward, dtype=torch.float32)[None]).pow(2).mean()
        losses.append(policy_loss + 0.5 * value_loss - 0.01 * entropy.mean())
    loss = torch.stack(losses).mean()
    loss.backward()
    grad_norm = float(torch.nn.utils.clip_grad_norm_(agent.parameters(), 0.5))
    optimizer.step()
    finite_update = bool(np.isfinite(float(loss.detach())) and np.isfinite(grad_norm))

    state = {
        "model": deepcopy(agent.state_dict()),
        "optimizer": deepcopy(optimizer.state_dict()),
        "envs": [env.runtime_state_dict() for env in envs],
    }
    clone = SGMPPO(envs[0].obs_dim, envs[0].share_obs_dim, envs[0].action_dim)
    clone.load_state_dict(state["model"])
    clone_env = ActiveDiagnosisTrainableUAVEnv(envs[0].config)
    clone_env.load_runtime_state_dict(state["envs"][0])
    obs, share, graph = envs[0]._observation()
    c_obs, c_share, c_graph = clone_env._observation()
    checkpoint_restore_exact = bool(
        all(torch.equal(agent.state_dict()[k], clone.state_dict()[k]) for k in agent.state_dict())
        and np.array_equal(obs, c_obs)
        and np.array_equal(share, c_share)
        and all(np.array_equal(graph[k], c_graph[k]) for k in graph)
    )

    actor_keys = tuple(r_graph)
    truth_not_exposed = bool(
        "hypothesis" not in actor_keys
        and "failure" not in actor_keys
        and pre_probe_equal
    )
    checks = {
        "standard_interface_shapes": interface_shapes,
        "pre_probe_actor_inputs_identical": pre_probe_equal,
        "latent_truth_not_exposed": truth_not_exposed,
        "relay_only_probe_action_mask": mask_contract,
        "probe_separates_decision_relevant_modes": post_probe_separation,
        "probe_completes_before_episode_terminal": completion_before_terminal,
        "masked_actor_rollout_actions_legal": illegal == 0,
        "single_ppo_smoke_update_finite": finite_update,
        "runtime_checkpoint_restore_exact": checkpoint_restore_exact,
    }
    passed = all(checks.values())
    return {
        "protocol": "ACTIVE-DIAGNOSIS-P3A-TRAINABLE-INTERFACE-GATE-V1",
        "verdict": "P3A_TRAINABLE_INTERFACE_PASS" if passed else "P3A_TRAINABLE_INTERFACE_FAIL",
        "checks": checks,
        "dimensions": {
            "agents": envs[0].num_agents,
            "actor_obs": envs[0].obs_dim,
            "critic_obs": envs[0].share_obs_dim,
            "flight_actions": envs[0].flight_action_dim,
            "total_actions": envs[0].action_dim,
        },
        "probe_outcomes": {"recoverable": recoverable_ack, "hard_failure": hard_ack},
        "smoke_environment_steps": smoke_steps + 2 * recoverable.config.probe_duration_steps,
        "ppo_smoke_updates": 1,
        "performance_training_started": False,
        "p3b_implementation_authorized": passed,
        "performance_pilot_authorized": False,
        "automatic_continuation": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run_gate()
    text = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    if result["verdict"].endswith("FAIL"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
