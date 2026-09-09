"""Audit the physical-probe semantics against the existing 3DOF UAV model."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from envs.active_diagnosis_semantic_env import HARD_RELAY_FAILURE, RECOVERABLE_RANGE_LOSS
from envs.active_diagnosis_uav_shadow_env import ActiveDiagnosisUAVShadowEnv, observations_equal


def _probe_signature(result: dict) -> dict:
    return {
        "ack": result["ack"],
        "elapsed_steps": result["elapsed_steps"],
        "energy_cost": result["energy_cost"],
        "collision": result["collision"],
        "constraint_violation": result["constraint_violation"],
    }


def run_shadow_gate(seed: int = 20260909) -> dict:
    recoverable = ActiveDiagnosisUAVShadowEnv(RECOVERABLE_RANGE_LOSS, seed)
    failed = ActiveDiagnosisUAVShadowEnv(HARD_RELAY_FAILURE, seed)
    pre_equal = observations_equal(recoverable.observation(), failed.observation())
    recoverable_state = recoverable.state_dict()
    recoverable_probe = recoverable.execute_handshake_probe()
    failed_probe = failed.execute_handshake_probe()
    recoverable.load_state_dict(recoverable_state)
    replay_probe = recoverable.execute_handshake_probe()
    checks = {
        "full_actor_share_graph_pre_probe_exact": pre_equal,
        "recoverable_range_loss_acknowledges": bool(recoverable_probe["ack"]),
        "hard_relay_failure_remains_silent": not bool(failed_probe["ack"]),
        "probe_elapsed_time_nonzero": recoverable_probe["elapsed_steps"] > 0,
        "probe_energy_cost_nonzero": float(recoverable_probe["energy_cost"][1]) > 0.0,
        "probe_collision_free": not recoverable_probe["collision"] and not failed_probe["collision"],
        "probe_constraint_safe": not recoverable_probe["constraint_violation"] and not failed_probe["constraint_violation"],
        "runtime_restore_exact": _probe_signature(recoverable_probe) == _probe_signature(replay_probe),
    }
    passed = all(checks.values())
    return {
        "protocol": "ACTIVE-DIAGNOSIS-P1C-3DOF-SHADOW-GATE-V1",
        "verdict": "P1C_3DOF_PHYSICAL_PROBE_SEMANTIC_PASS" if passed else "P1C_3DOF_PHYSICAL_PROBE_SEMANTIC_FAIL",
        "checks": checks,
        "seed": seed,
        "recoverable_probe": _probe_signature(recoverable_probe),
        "hard_failure_probe": _probe_signature(failed_probe),
        "scope": "zero-training shadow adapter over UAVIntercept3DEnv; not a trainable policy interface",
        "training_started": False,
        "environment_steps": 0,
        "ppo_updates": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = run_shadow_gate()
    text = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)
    if report["verdict"].endswith("FAIL"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
