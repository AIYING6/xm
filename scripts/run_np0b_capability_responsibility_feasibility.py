"""NP0B capability-overlap and responsibility-feasibility calibration."""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.run_np1_dynamic_capability_calibration import DynamicCapabilityAdapter  # noqa: E402
from scripts import run_new_project_l0_single_interceptor as l0  # noqa: E402
from scripts.run_np1c_responsibility_necessity_recalibration import cfg as base_cfg  # noqa: E402

OUT = ROOT / "results" / "np0b_capability_responsibility_feasibility"
SEEDS = (9121, 9122, 9123, 9124)
TRANSITION_STEP = 10
HORIZON = 120
PROTOCOL = "NP0B_CAPABILITY_OVERLAP_AND_RESPONSIBILITY_FEASIBILITY_V1"

CAPABILITY_MATRIX_PRE = {
    "scout": {"S": 1, "I": 1, "A": 1, "E": 0},
    "relay": {"S": 1, "I": 1, "A": 1, "E": 0},
    "attacker": {"S": 0, "I": 1, "A": 1, "E": 1},
}
CAPABILITY_MATRIX_POST = {
    "scout": {"S": 0, "I": 1, "A": 1, "E": 0},
    "relay": {"S": 1, "I": 1, "A": 1, "E": 0},
    "attacker": {"S": 0, "I": 1, "A": 1, "E": 1},
}
R0 = {"S": "scout", "I": "relay", "A": "attacker", "E": "attacker"}
R1 = {"S": "relay", "I": "relay", "A": "attacker", "E": "attacker"}


def oracle_guidance(env: DynamicCapabilityAdapter) -> np.ndarray:
    raw = np.asarray(l0.scripted_oracle_actions(env)).reshape(-1)
    out = np.zeros((env.config.num_blue, 2), dtype=np.float32)
    for i, value in enumerate(raw[: env.config.num_blue]):
        mapped = l0.convert_oracle_action(int(value))
        out[i] = l0.GUIDANCE_ACTION_TABLE[mapped % l0.GUIDANCE_FLIGHT_ACTION_DIM]
    return out


def cfg(seed: int):
    c = replace(base_cfg(seed), max_steps=HORIZON, target_policy="straight")
    return c


def physical_run(seed: int, transition: bool) -> dict[str, object]:
    env = DynamicCapabilityAdapter(cfg(seed), transition_step=TRANSITION_STEP if transition else HORIZON + 1)
    obs, _, _ = env.reset()
    relay_detected_after = False
    records = []
    info: dict[str, float] = {}
    while not env.done and env.step_count < HORIZON:
        obs, _, _, _, dones, info = env.step_guidance(oracle_guidance(env))
        if transition and env.step_count >= TRANSITION_STEP and float(env.detected_by[1]) > 0.5:
            relay_detected_after = True
        records.append({
            "step": int(env.step_count),
            "scout_detected": float(env.detected_by[env.scout_id]),
            "relay_detected": float(env.detected_by[1]),
            "relay_has_target": bool(env._has_target_information(1)),
            "attacker_has_target": bool(env._has_target_information(2)),
        })
        if bool(dones[0, 0]):
            break
    outcome = "NEUTRALIZED" if info.get("target_neutralized", 0.0) > 0.5 else (
        "COLLISION" if info.get("collision", 0.0) > 0.5 else (
            "CONSTRAINT_FAILURE" if info.get("constraint_violation", 0.0) > 0.5 else "TIMEOUT"
        )
    )
    return {"seed": seed, "transition": transition, "outcome": outcome, "steps": int(env.step_count), "relay_detected_after_transition": relay_detected_after, "records": records}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    nominal = [physical_run(seed, False) for seed in SEEDS]
    post_transition = [physical_run(seed, True) for seed in SEEDS]
    matrix_old_post_feasible = all(CAPABILITY_MATRIX_POST[role][req] for req, role in R0.items())
    matrix_alt_post_feasible = all(CAPABILITY_MATRIX_POST[role][req] for req, role in R1.items())
    nominal_success = sum(r["outcome"] == "NEUTRALIZED" for r in nominal)
    alt_physical_success = sum(r["outcome"] == "NEUTRALIZED" for r in post_transition)
    backup_path = all(r["relay_detected_after_transition"] for r in post_transition)
    # Old assignment infeasibility is a capability-level fact, not inferred
    # from a poor controller: Scout no longer has S while R0 still assigns S.
    old_assignment_infeasible = not matrix_old_post_feasible
    if nominal_success == len(SEEDS) and old_assignment_infeasible and matrix_alt_post_feasible and alt_physical_success == len(SEEDS) and backup_path:
        verdict = "NP0B_PASS__OVERLAP_AND_RESPONSIBILITY_FEASIBILITY_ESTABLISHED__READY_FOR_NP1"
    else:
        verdict = "NP0B_NO_GO__CAPABILITY_RESPONSIBILITY_FEASIBILITY_NOT_ESTABLISHED"
    report = {
        "protocol_version": PROTOCOL,
        "training": False,
        "algorithm": None,
        "capability_matrix_pre": CAPABILITY_MATRIX_PRE,
        "capability_matrix_post": CAPABILITY_MATRIX_POST,
        "pre_assignment_R0": R0,
        "alternative_assignment_R1": R1,
        "nominal": nominal,
        "post_transition_oracle": post_transition,
        "nominal_neutralized": nominal_success,
        "post_transition_oracle_neutralized": alt_physical_success,
        "old_assignment_infeasible_by_matrix": old_assignment_infeasible,
        "alternative_assignment_feasible_by_matrix": matrix_alt_post_feasible,
        "backup_sensing_path_observed": backup_path,
        "verdict": verdict,
    }
    (OUT / "NP0B_FEASIBILITY_REPORT.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (OUT / "NP0B_FEASIBILITY_MANIFEST.json").write_text(json.dumps({
        "protocol_version": PROTOCOL,
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "seeds": list(SEEDS),
        "uses_training": False,
        "uses_new_method": False,
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"{verdict}: nominal={nominal_success}/{len(SEEDS)} alternative={alt_physical_success}/{len(SEEDS)} backup_path={backup_path}")


if __name__ == "__main__":
    main()
