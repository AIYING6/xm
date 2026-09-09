from __future__ import annotations

from envs.active_diagnosis_semantic_env import HARD_RELAY_FAILURE, RECOVERABLE_RANGE_LOSS
from envs.active_diagnosis_uav_shadow_env import ActiveDiagnosisUAVShadowEnv, observations_equal
from scripts.audit_active_diagnosis_p1c_3dof_shadow import run_shadow_gate


def test_3dof_observations_match_before_probe() -> None:
    recoverable = ActiveDiagnosisUAVShadowEnv(RECOVERABLE_RANGE_LOSS, 13)
    failed = ActiveDiagnosisUAVShadowEnv(HARD_RELAY_FAILURE, 13)
    assert observations_equal(recoverable.observation(), failed.observation())


def test_3dof_probe_separates_latent_causes_without_unsafe_motion() -> None:
    recoverable = ActiveDiagnosisUAVShadowEnv(RECOVERABLE_RANGE_LOSS, 13)
    failed = ActiveDiagnosisUAVShadowEnv(HARD_RELAY_FAILURE, 13)
    range_result = recoverable.execute_handshake_probe()
    failure_result = failed.execute_handshake_probe()
    assert range_result["ack"] is True
    assert failure_result["ack"] is False
    assert range_result["energy_cost"][recoverable.relay_id] > 0.0
    assert not range_result["collision"]
    assert not range_result["constraint_violation"]


def test_3dof_shadow_gate_passes() -> None:
    report = run_shadow_gate()
    assert report["verdict"] == "P1C_3DOF_PHYSICAL_PROBE_SEMANTIC_PASS"
    assert all(report["checks"].values())
