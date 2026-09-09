import json

import torch

from algorithms.active_diagnosis.recurrent_sg_mappo import RecurrentSGMAPPO
from algorithms.active_diagnosis.task_value_estimator import TaskValueEstimator
from envs.active_diagnosis_trainable_uav_env import ActiveDiagnosisTrainableUAVEnv
from scripts.run_active_diagnosis_p3b_pilot import evaluate_arm, preflight, train_prefix


def test_staged_preflight_exposes_exact_logical_budget(tmp_path) -> None:
    result = preflight(tmp_path)
    assert result["verdict"] == "P3B_STAGED_RUNNER_IMPLEMENTED"
    assert result["logical_total_updates"] == 3907
    assert result["logical_environment_steps"] == 1_000_192
    assert result["calibration_quality_stop_enforced"] is True


def test_one_update_common_prefix_writes_fixed_checkpoint(tmp_path) -> None:
    output = train_prefix(83011, tmp_path, updates=1)
    manifest = json.loads((output / "run_manifest.json").read_text())
    assert manifest["status"] == "completed"
    assert manifest["environment_steps"] == 256
    assert (output / "prefix_checkpoint.pt").is_file()


def test_fixed_endpoint_evaluation_uses_all_prior_hypothesis_cells(tmp_path) -> None:
    env = ActiveDiagnosisTrainableUAVEnv()
    agent = RecurrentSGMAPPO(env.obs_dim, env.share_obs_dim, env.action_dim, hidden_dim=96, role_dim=8)
    estimator = TaskValueEstimator(env.obs_dim, hidden_dim=64)
    run = tmp_path / "runs" / "recurrent_mappo" / "seed83011"
    calibration = tmp_path / "calibration" / "seed83011"
    run.mkdir(parents=True); calibration.mkdir(parents=True)
    torch.save(agent.state_dict(), run / "actor_critic_latest.pt")
    torch.save({"task_value": {"model": estimator.state_dict()}}, calibration / "calibration_checkpoint.pt")
    destination = evaluate_arm(83011, "recurrent_mappo", tmp_path, episodes_per_cell=1)
    lines = destination.read_text().splitlines()
    assert len(lines) == 5
    assert "recoverable_range_loss" in destination.read_text()
    assert "hard_terminal_comm_failure" in destination.read_text()
