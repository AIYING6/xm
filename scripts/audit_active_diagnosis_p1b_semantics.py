"""Execute the P1B zero-training active-diagnosis environment gate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from envs.active_diagnosis_semantic_env import (
    ActiveDiagnosisSemanticEnv,
    DiagnosticMode,
    HARD_RELAY_FAILURE,
    RECOVERABLE_RANGE_LOSS,
)
from scripts.audit_active_diagnosis_identifiability_p1 import run_audit


def run_semantic_gate() -> dict:
    gate = json.loads(
        (ROOT / "configs" / "active_diagnosis_p1b_semantic_gate.json").read_text(encoding="utf-8")
    )
    counterexample = json.loads(
        (ROOT / "configs" / "active_diagnosis_p1_counterexample.json").read_text(encoding="utf-8")
    )
    left = ActiveDiagnosisSemanticEnv(RECOVERABLE_RANGE_LOSS, seed=0)
    right = ActiveDiagnosisSemanticEnv(HARD_RELAY_FAILURE, seed=0)
    pre_probe_equal = left.actor_observation() == right.actor_observation()
    forbidden = {"hypothesis", "failure", "failed_agent", "fault_mask", "rng"}
    actor_fields = set(left.actor_observation())

    count = int(gate["distribution_audit"]["seed_count_per_hypothesis"])
    ack_rates = {}
    safe = True
    exact_cost = True
    for hypothesis in (RECOVERABLE_RANGE_LOSS, HARD_RELAY_FAILURE):
        acknowledgements = 0
        for seed in range(count):
            env = ActiveDiagnosisSemanticEnv(hypothesis, seed=seed)
            before_energy = env.energy
            before_step = env.step_count
            observation, info = env.step(DiagnosticMode.HANDSHAKE_PROBE)
            acknowledgements += int(observation["handshake_ack"] > 0.5)
            safe &= info["collision"] == 0.0 and info["boundary_violation"] == 0.0
            exact_cost &= env.step_count - before_step == env.config.probe_duration_steps
            exact_cost &= abs((before_energy - env.energy) - env.config.probe_energy_cost) < 1e-12
        ack_rates[hypothesis] = acknowledgements / count

    replay = ActiveDiagnosisSemanticEnv(RECOVERABLE_RANGE_LOSS, seed=731)
    frozen = replay.state_dict()
    first = replay.step(DiagnosticMode.HANDSHAKE_PROBE)
    replay.load_state_dict(frozen)
    second = replay.step(DiagnosticMode.HANDSHAKE_PROBE)
    restore_exact = first == second

    analytic = run_audit(counterexample)
    checks = {
        "pre_probe_actor_observation_exact": pre_probe_equal,
        "post_probe_observation_separable": abs(
            ack_rates[RECOVERABLE_RANGE_LOSS] - ack_rates[HARD_RELAY_FAILURE]
        ) >= float(gate["distribution_audit"]["minimum_empirical_ack_gap"]),
        "fault_truth_absent_from_actor_observation": not any(
            any(token in field for token in forbidden) for field in actor_fields
        ),
        "probe_cost_exact": exact_cost,
        "probe_trajectory_safe": safe,
        "policy_ordering_nontrivial": (
            analytic["balanced_prior"]["probe_gain"] > 0.0
            and any(item["probe_gain"] < 0.0 for item in analytic["extreme_priors"])
        ),
        "runtime_restore_exact": restore_exact,
    }
    passed = all(checks.values())
    return {
        "protocol": gate["protocol"],
        "verdict": "P1B_ACTIVE_DIAGNOSIS_ENVIRONMENT_SEMANTIC_PASS" if passed else "P1B_ACTIVE_DIAGNOSIS_ENVIRONMENT_SEMANTIC_FAIL",
        "checks": checks,
        "empirical_ack_rates": ack_rates,
        "empirical_ack_gap": ack_rates[RECOVERABLE_RANGE_LOSS] - ack_rates[HARD_RELAY_FAILURE],
        "actor_observation_fields": sorted(actor_fields),
        "scope": "minimal semantic state machine; not the trainable 3DOF UAV environment",
        "training_started": False,
        "environment_steps": 0,
        "ppo_updates": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = run_semantic_gate()
    text = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)
    if report["verdict"].endswith("FAIL"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
