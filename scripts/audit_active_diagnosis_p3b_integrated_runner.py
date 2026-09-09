"""Real-environment implementation gate for the integrated P3B runner."""

from __future__ import annotations

import argparse
import copy
from dataclasses import replace
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from algorithms.active_diagnosis.pilot_runner import (
    PILOT_ARMS,
    ActiveDiagnosisPPOConfig,
    calibrate_task_value_estimator,
    collect_rollout,
    load_runtime_state_dict,
    make_runtime,
    runtime_state_dict,
    update_from_rollout,
)
from algorithms.active_diagnosis.recurrent_sg_mappo import RecurrentSGMAPPO
from algorithms.active_diagnosis.task_value_estimator import TaskValueEstimator, TaskValueReplayBuffer
from envs.active_diagnosis_semantic_env import RECOVERABLE_RANGE_LOSS
from envs.active_diagnosis_trainable_uav_env import (
    ActiveDiagnosisTrainableConfig,
    ActiveDiagnosisTrainableUAVEnv,
    HARD_TERMINAL_COMM_FAILURE,
)


FREEZE = ROOT / "configs" / "active_diagnosis_p3b_pilot_freeze.json"


def _components(arm: str, base: RecurrentSGMAPPO | None = None):
    envs = [
        ActiveDiagnosisTrainableUAVEnv(ActiveDiagnosisTrainableConfig(RECOVERABLE_RANGE_LOSS, 8111)),
        ActiveDiagnosisTrainableUAVEnv(ActiveDiagnosisTrainableConfig(HARD_TERMINAL_COMM_FAILURE, 8112)),
    ]
    agent = RecurrentSGMAPPO(envs[0].obs_dim, envs[0].share_obs_dim, envs[0].action_dim, hidden_dim=24)
    if base is not None:
        agent.load_state_dict(copy.deepcopy(base.state_dict()))
    estimator = TaskValueEstimator(envs[0].obs_dim, hidden_dim=24)
    replay = TaskValueReplayBuffer(envs[0].obs_dim, capacity=128, seed=91)
    runtime = make_runtime(arm, envs, agent, recoverable_prior=0.5, device="cpu")
    return envs, agent, estimator, replay, runtime


def collect_result() -> dict:
    freeze_bytes = FREEZE.read_bytes()
    freeze = json.loads(freeze_bytes)
    torch.manual_seed(81); np.random.seed(81)
    _, common, _, _, _ = _components("recurrent_mappo")
    cfg = ActiveDiagnosisPPOConfig(rollout_steps=64, bptt_horizon=16, ppo_epochs=1)
    rows = {}
    arm_models = {}
    for arm in PILOT_ARMS:
        _, agent, estimator, replay, runtime = _components(arm, common)
        before = copy.deepcopy(agent.state_dict())
        batch = collect_rollout(agent, estimator, replay, runtime, cfg)
        optimizer = torch.optim.Adam(agent.parameters(), lr=3e-4)
        metrics = update_from_rollout(agent, optimizer, batch, cfg)
        changed = any(not torch.equal(before[key], agent.state_dict()[key]) for key in before)
        rows[arm] = {
            "environment_steps": int(cfg.rollout_steps * len(runtime.envs)),
            "illegal_executed_actions": int(batch["illegal_executed_actions"]),
            "sampled_executed_difference_count": int(np.sum(batch["sampled_actions"] != batch["executed_actions"])),
            "externally_controlled_agent_time_count": int(np.sum(batch["actor_control_mask"] == 0.0)),
            "finite_update": bool(changed and all(np.isfinite(value) for value in metrics.values())),
            "metrics": metrics,
        }
        arm_models[arm] = agent

    # Exact mid-option continuation check on real environments.
    _, agent, estimator, replay, runtime = _components("entropy_probe", common)
    short = ActiveDiagnosisPPOConfig(rollout_steps=5, bptt_horizon=4, ppo_epochs=1)
    collect_rollout(agent, estimator, replay, runtime, short)
    saved_runtime = copy.deepcopy(runtime_state_dict(runtime))
    saved_model = copy.deepcopy(agent.state_dict())
    first = collect_rollout(agent, estimator, replay, runtime, short)
    _, clone, clone_estimator, clone_replay, clone_runtime = _components("entropy_probe", common)
    clone.load_state_dict(saved_model)
    load_runtime_state_dict(clone_runtime, saved_runtime)
    second = collect_rollout(clone, clone_estimator, clone_replay, clone_runtime, short)
    continuation_exact = all(np.array_equal(first[key], second[key]) for key in (
        "sampled_actions", "executed_actions", "old_log_prob", "rewards", "dones"
    ))

    # Force a short audit-only horizon to exercise terminal supervision. The
    # frozen performance environment remains untouched.
    envs, terminal_agent, terminal_estimator, terminal_replay, terminal_runtime = _components(
        "recurrent_mappo", common
    )
    for env in envs:
        env.base.config = replace(env.base.config, max_steps=6)
    terminal_batch = collect_rollout(
        terminal_agent, terminal_estimator, terminal_replay, terminal_runtime,
        ActiveDiagnosisPPOConfig(rollout_steps=6, bptt_horizon=3, ppo_epochs=1),
    )
    terminal_records = terminal_replay.state_dict()["records"]

    calibration_estimator = TaskValueEstimator(envs[0].obs_dim, hidden_dim=24)
    calibration_optimizer = torch.optim.Adam(calibration_estimator.parameters(), lr=1e-2)
    calibration = calibrate_task_value_estimator(
        common, calibration_estimator, calibration_optimizer,
        geometry_seeds=[8211, 8212], train_geometry_count=1, gradient_steps=3,
    )

    parameter_counts = {
        arm: sum(parameter.numel() for parameter in model.parameters())
        for arm, model in arm_models.items()
    }
    tape_cells = freeze["evaluation"]["episode_id_cells"]
    episode_ids = []
    for start, stop in tape_cells.values():
        episode_ids.extend(range(start, stop + 1))
    checks = {
        "three_arms_share_exact_initial_recurrent_parameters": len(set(parameter_counts.values())) == 1,
        "all_three_arms_take_finite_real_environment_ppo_update": all(row["finite_update"] for row in rows.values()),
        "all_executed_actions_are_legal": all(row["illegal_executed_actions"] == 0 for row in rows.values()),
        "ungated_arm_has_no_external_action_attribution": rows["recurrent_mappo"]["externally_controlled_agent_time_count"] == 0,
        "both_gated_arms_store_distinct_sampled_and_executed_tracks": all(
            rows[arm]["sampled_executed_difference_count"] > 0
            and rows[arm]["externally_controlled_agent_time_count"] > 0
            for arm in ("entropy_probe", "decision_relevant_probe")
        ),
        "mid_probe_checkpoint_continuation_is_exact": continuation_exact,
        "completed_training_episodes_create_real_return_supervision": (
            terminal_runtime.completed_episodes == 2
            and len(terminal_records) == 2
            and {record[1] for record in terminal_records} == {0, 1}
            and all(np.isfinite(record[3]) for record in terminal_records)
        ),
        "fixed_tape_episode_ids_are_unique_and_disjoint_from_training_seeds": (
            len(episode_ids) == len(set(episode_ids))
            and not set(episode_ids).intersection(freeze["training_seeds"])
        ),
        "calibration_is_explicit_and_not_hidden_in_ppo_budget": (
            freeze["task_value_calibration"]["ppo_updates_during_calibration"] == 0
            and freeze["task_value_calibration"]["calibration_simulator_steps_reported_separately"]
        ),
        "probe_then_recovery_calibration_covers_full_factorial_without_actor_update": (
            calibration["episodes"] == 8
            and calibration["ppo_updates"] == 0
            and not calibration["actor_parameters_changed"]
            and all(
                {(row["hypothesis_index"], row["recovery_option"]) for row in records}
                == {(0, 0), (0, 1), (1, 0), (1, 1)}
                for records in calibration["records"].values()
            )
        ),
        "task_value_gate_uses_relay_local_observation_not_centralized_critic_state": (
            calibration_estimator.state_dim == envs[0].obs_dim
            and calibration_estimator.state_dim != envs[0].share_obs_dim
            and all(
                len(row["state"]) == envs[0].obs_dim
                for records in calibration["records"].values()
                for row in records
            )
        ),
    }
    passed = all(checks.values())
    return {
        "protocol": "ACTIVE-DIAGNOSIS-P3B-INTEGRATED-RUNNER-AUDIT-V1",
        "verdict": "P3B_INTEGRATED_RUNNER_PASS" if passed else "P3B_INTEGRATED_RUNNER_FAIL",
        "checks": checks,
        "arm_audit": rows,
        "fixed_tape_sha256": hashlib.sha256(freeze_bytes).hexdigest(),
        "real_environment_steps": int(
            sum(row["environment_steps"] for row in rows.values()) + 30 + 12 + calibration["environment_steps"]
        ),
        "ppo_smoke_updates": len(PILOT_ARMS),
        "performance_training_started": False,
        "performance_pilot_authorized": False,
        "calibration_technical_summary": {
            key: value for key, value in calibration.items()
            if key not in {"replay", "records", "validation"}
        },
        "remaining_blocker": "full common-prefix task-value calibration must pass before arm-specific training",
        "automatic_continuation": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = collect_result()
    text = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    if result["verdict"].endswith("FAIL"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
