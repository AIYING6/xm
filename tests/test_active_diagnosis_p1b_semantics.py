from __future__ import annotations

from envs.active_diagnosis_semantic_env import (
    ActiveDiagnosisSemanticEnv,
    DiagnosticMode,
    HARD_RELAY_FAILURE,
    RECOVERABLE_RANGE_LOSS,
)
from scripts.audit_active_diagnosis_p1b_semantics import run_semantic_gate


def test_latent_causes_are_observation_equivalent_before_probe() -> None:
    recoverable = ActiveDiagnosisSemanticEnv(RECOVERABLE_RANGE_LOSS, seed=4)
    failed = ActiveDiagnosisSemanticEnv(HARD_RELAY_FAILURE, seed=4)
    assert recoverable.actor_observation() == failed.actor_observation()


def test_probe_has_real_cost_and_respects_geometry() -> None:
    env = ActiveDiagnosisSemanticEnv(RECOVERABLE_RANGE_LOSS, seed=9)
    before_energy = env.energy
    observation, info = env.step(DiagnosticMode.HANDSHAKE_PROBE)
    assert observation["step_norm"] == env.config.probe_duration_steps / 10.0
    assert before_energy - env.energy == env.config.probe_energy_cost
    assert info["collision"] == 0.0
    assert info["boundary_violation"] == 0.0
    assert DiagnosticMode.HANDSHAKE_PROBE not in env.legal_modes()


def test_runtime_restore_replays_probe_exactly() -> None:
    env = ActiveDiagnosisSemanticEnv(RECOVERABLE_RANGE_LOSS, seed=731)
    state = env.state_dict()
    first = env.step(DiagnosticMode.HANDSHAKE_PROBE)
    env.load_state_dict(state)
    second = env.step(DiagnosticMode.HANDSHAKE_PROBE)
    assert first == second


def test_full_semantic_gate_passes() -> None:
    report = run_semantic_gate()
    assert report["verdict"] == "P1B_ACTIVE_DIAGNOSIS_ENVIRONMENT_SEMANTIC_PASS"
    assert all(report["checks"].values())
