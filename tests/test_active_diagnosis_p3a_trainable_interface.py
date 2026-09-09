import numpy as np
import pytest

from envs.active_diagnosis_semantic_env import HARD_RELAY_FAILURE, RECOVERABLE_RANGE_LOSS
from envs.active_diagnosis_trainable_uav_env import (
    ActiveDiagnosisTrainableConfig,
    ActiveDiagnosisTrainableUAVEnv,
)
from scripts.audit_active_diagnosis_p3a_trainable_interface import run_gate


def test_p3a_gate_passes() -> None:
    result = run_gate()
    assert result["verdict"] == "P3A_TRAINABLE_INTERFACE_PASS"
    assert result["p3b_implementation_authorized"] is True
    assert result["performance_pilot_authorized"] is False
    assert result["performance_training_started"] is False


def test_hidden_modes_share_pre_probe_actor_inputs() -> None:
    a = ActiveDiagnosisTrainableUAVEnv(ActiveDiagnosisTrainableConfig(RECOVERABLE_RANGE_LOSS, 91))
    b = ActiveDiagnosisTrainableUAVEnv(ActiveDiagnosisTrainableConfig(HARD_RELAY_FAILURE, 91))
    ao, ashare, ag = a.reset()
    bo, bshare, bg = b.reset()
    assert np.array_equal(ao, bo)
    assert np.array_equal(ashare, bshare)
    assert all(np.array_equal(ag[key], bg[key]) for key in ag)


def test_probe_is_relay_only_and_budgeted() -> None:
    env = ActiveDiagnosisTrainableUAVEnv()
    _, _, graph = env.reset()
    assert graph["action_masks"][env.relay_id, env.probe_action] == 1
    assert graph["action_masks"][0, env.probe_action] == 0
    bad = np.full(env.num_agents, env.neutral_action)
    bad[0] = env.probe_action
    with pytest.raises(ValueError, match="masked action"):
        env.step(bad)
