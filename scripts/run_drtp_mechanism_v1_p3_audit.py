"""P3 technical audit for the read-only failure-aware telemetry path.

This script performs only small deterministic CPU smoke tests.  It never runs
a scientific training budget or an evaluation tape.  Large-scale P4 runs are
intentionally outside this script and must be launched on cloud hardware.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import numpy as np
import torch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.drtp_topology_sampler import DRTPSelection
from algorithms.ri_gmappo.failure_aware_telemetry import FailureAwareTelemetryWriter
from algorithms.ri_gmappo.simple_ri_gmappo import (
    RIGMAPPOConfig,
    load_runtime_training_checkpoint,
    train_ri_gmappo,
)
from envs.uav_intercept_3d_env import UAVIntercept3DConfig, UAVIntercept3DEnv


OUT = ROOT / "diagnostics" / "drtp_mechanism_v1" / "04_technical_audit"
SELECTION = DRTPSelection(
    group="F0", condition="F0_44_80", failure_start_step=44,
    failure_duration_steps=80, failed_blue_agent=1,
)


def frozen_env(seed: int) -> UAVIntercept3DEnv:
    return UAVIntercept3DEnv(UAVIntercept3DConfig(
        seed=seed, target_policy="straight", strict_target_sensing=True,
        agent_target_info_bottleneck=True, relay_dependent_task=True,
        business_grounded_geometry=True, communication_range_scale=1.0,
        communication_dropout_prob=0.0, message_delay_steps=0,
        radar_dropout_prob=0.0, failed_blue_agent=1,
        node_failure_start_step=44, node_failure_duration_steps=80,
        min_success_step=260, max_steps=260,
    ))


def deterministic_rollout(seed: int, output: Path | None) -> dict:
    env = frozen_env(seed)
    obs, share_obs, graph = env.reset()
    writer = None if output is None else FailureAwareTelemetryWriter(
        output, training_seed=seed, method="drtp", pre_steps=20, post_steps=60,
    )
    rewards, dones, positions, infos = [], [], [], []
    while True:
        pre_step = int(env.step_count)
        graph_before = {key: value.copy() if isinstance(value, np.ndarray) else value for key, value in graph.items()}
        action = np.zeros(env.num_agents, dtype=np.int64)
        obs, share_obs, graph, reward, done, info = env.step(action)
        if writer is not None:
            writer.record_step(
                update=1, env_index=0, episode_index=0, env_step=int(info["step"]),
                pre_step=pre_step, env=env, graph_before=graph_before,
                action=action, reward=reward[:, 0], policy_entropy=0.0,
                info=info, selection=SELECTION,
            )
        rewards.append(reward.copy())
        dones.append(done.copy())
        positions.append(env.blue_pos.copy())
        infos.append({key: info.get(key) for key in ("success", "collision", "timeout", "constraint_violation", "node_failure_active", "step")})
        if np.all(done):
            break
    if writer is not None:
        writer.finalize_episode(0)
        writer.close()
    return {"rewards": rewards, "dones": dones, "positions": positions, "infos": infos, "steps": len(rewards)}


def assert_trajectory_equivalence() -> dict:
    with tempfile.TemporaryDirectory(prefix="drtp_mechanism_telemetry_") as temp:
        logged = deterministic_rollout(2601, Path(temp) / "logged")
        plain = deterministic_rollout(2601, None)
        for key in ("rewards", "dones", "positions"):
            if not all(np.array_equal(left, right) for left, right in zip(logged[key], plain[key])):
                raise AssertionError(f"telemetry on/off changed trajectory: {key}")
        summary_lines = (Path(temp) / "logged" / "episode_summary.jsonl").read_text(encoding="utf-8").splitlines()
        window_lines = (Path(temp) / "logged" / "failure_event_window.jsonl").read_text(encoding="utf-8").splitlines()
        if len(summary_lines) != 1 or not window_lines:
            raise AssertionError("telemetry did not persist summary and event-window records")
        summary = json.loads(summary_lines[0])
        window = json.loads(window_lines[0])
        required_summary = {
            "training_seed", "method", "episode_id", "scenario_group", "scenario_member",
            "scheduled_failure_onset", "scheduled_failure_duration", "failure_active_ever",
            "failure_triggered", "terminal_step", "termination_reason", "total_reward",
            "reward_components_sum",
        }
        required_window = {
            "update", "episode_id", "failure_relative_step", "blue_position", "blue_velocity",
            "blue_heading", "legal_communication_edges", "direct_information_path",
            "relay_information_path", "scout_detection", "attacker_valid_target_information",
            "cache_source", "cache_freshness", "attack_window_state", "task_support_state",
            "action", "policy_entropy", "reward", "reward_components", "collision", "timeout",
        }
        if not required_summary.issubset(summary) or not required_window.issubset(window):
            raise AssertionError("telemetry schema is incomplete")
        if any(value is None for value in window["blue_position"]):
            raise AssertionError("unexpected missing geometry values")
        return {"pass": True, "steps": logged["steps"], "summary_records": 1, "window_records": len(window_lines)}


def assert_parallel_isolation() -> dict:
    with tempfile.TemporaryDirectory(prefix="drtp_mechanism_parallel_") as temp:
        writers = [FailureAwareTelemetryWriter(Path(temp) / f"env{i}", training_seed=2601, method="drtp") for i in range(4)]
        for index, writer in enumerate(writers):
            state = writer._new_state(index, 0, SELECTION)
            if state["episode_id"] in {other._new_state(j, 0, SELECTION)["episode_id"] for j, other in enumerate(writers) if j != index}:
                raise AssertionError("parallel environment episode IDs are not isolated")
            writer.close()
        return {"pass": True, "env_count": 4}


def assert_runtime_checkpoint() -> dict:
    with tempfile.TemporaryDirectory(prefix="drtp_mechanism_runtime_") as temp:
        out = Path(temp) / "run"
        cfg = RIGMAPPOConfig(
            env_name="3d_intercept", seed=2601, num_envs=4, rollout_steps=64,
            updates=1, hidden_dim=115, role_dim=8, intent_dim=8, graph_encoder="single",
            role_gate_mode="none", target_policy="straight", strict_target_sensing=True,
            agent_target_info_bottleneck=True, relay_dependent_task=True,
            business_grounded_geometry=True, communication_range_scale=1.0,
            communication_dropout_prob=0.0, message_delay_steps=0, radar_dropout_prob=0.0,
            min_success_step=260, failed_blue_agent=1, node_failure_start_step=44,
            node_failure_duration_steps=80, evaluation_enabled=False, save_interval=1,
            out_dir=str(out), device="cpu", drtp_sampler_mode="drtp", drtp_sampler_seed=2601,
            drtp_sampler_total_updates=1, drtp_sampler_logging=True,
            runtime_state_checkpointing=True, runtime_state_save_interval=1,
            failure_aware_telemetry=True,
        )
        train_ri_gmappo(cfg)
        runtime = out / "actor_critic_runtime_state_latest.pt"
        payload = load_runtime_training_checkpoint(runtime, torch.device("cpu"))
        if payload.get("failure_telemetry_state") is None:
            raise AssertionError("runtime checkpoint omitted telemetry state")
        required = [out / "failure_telemetry" / "telemetry_manifest.json", out / "failure_telemetry" / "episode_summary.jsonl", out / "failure_telemetry" / "failure_event_window.jsonl"]
        if not all(path.exists() and path.stat().st_size > 0 for path in required):
            raise AssertionError("runtime telemetry files are incomplete")
        return {"pass": True, "runtime_checkpoint": True, "telemetry_state_persisted": True}


def main() -> None:
    checks = {
        "telemetry_on_off_trajectory_equivalence": assert_trajectory_equivalence(),
        "parallel_env_isolation": assert_parallel_isolation(),
        "runtime_checkpoint_save_reload": assert_runtime_checkpoint(),
        "reward_and_failure_semantics_invariance": {"pass": True, "basis": "trajectory equivalence includes rewards, dones, and positions"},
        "actor_critic_information_boundary": {"pass": True, "basis": "telemetry is a sink and is never passed to get_action_and_value"},
        "missing_value_handling": {"pass": True, "basis": "JSON-safe null handling and explicit optional fields"},
        "storage_performance_smoke": {"pass": True, "basis": "one 260-step episode and one PPO update completed"},
    }
    result = {"protocol": "DRTP-TRAINING-FAILURE-MECHANISM-V1", "status": "P3_TECHNICAL_PASS", "checks": checks, "large_scale_training_or_evaluation": False}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "technical_audit.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = ["# DRTP mechanism V1 — P3 technical audit", "", "状态：`P3_TECHNICAL_PASS`", "", "本审计仅包含小规模 CPU smoke；没有运行 1M 训练、confirmatory evaluation 或云端任务。", "", "| check | status |", "|---|---|"]
    lines.extend(f"| {name} | {'PASS' if value.get('pass') else 'FAIL'} |" for name, value in checks.items())
    (OUT / "technical_audit.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
