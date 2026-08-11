"""NP1C one-shot timing/geometry recalibration; no training or new method."""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.run_np1_dynamic_capability_calibration import (  # noqa: E402
    DynamicCapabilityAdapter,
    scripted_guidance,
)

OUT = ROOT / "results" / "np1c_responsibility_necessity_recalibration"
SEEDS = (9111, 9112, 9113, 9114)
TRANSITION_STEP = 10
HORIZON = 150
PROTOCOL = "NP1C_RESPONSIBILITY_NECESSITY_TASK_RECALIBRATION_V1"


def cfg(seed: int):
    from scripts.run_np1_dynamic_capability_calibration import config as base_config
    base = base_config(seed)
    types = list(base.blue_types)
    # Relay is a lawful backup sensor, initially just outside its sensing
    # range.  It can acquire sensing by changing trajectory after Scout loss.
    types[1] = replace(types[1], radar_range=17_500.0)
    return replace(
        base,
        max_steps=HORIZON,
        target_policy="weaving_param",
        target_heading_amp=0.65,
        relay_identifiable_target_initial_position=(2_000.0, 0.0, 5_000.0),
        target_prior_position=(2_000.0, 0.0, 5_000.0),
        blue_types=types,
    )


def run(seed: int, mode: str, transition_step: int = TRANSITION_STEP) -> dict[str, object]:
    env = DynamicCapabilityAdapter(cfg(seed), transition_step=transition_step)
    obs, _, _ = env.reset()
    pre_actions: list[np.ndarray] = []
    records: list[dict[str, object]] = []
    info: dict[str, float] = {}
    while not env.done and env.step_count < HORIZON:
        if mode == "fixed_responsibility" and env.step_count >= transition_step and pre_actions:
            action = pre_actions[-1].copy()
        else:
            action = scripted_guidance(env, obs)
        if env.step_count < transition_step:
            pre_actions.append(action.copy())
        obs, _, _, _, dones, info = env.step_guidance(action)
        records.append({
            "step": int(env.step_count),
            "action": action.tolist(),
            "scout_has_target": bool(env._has_target_information(env.scout_id)),
            "relay_detected": float(env.detected_by[1]),
            "relay_has_target": bool(env._has_target_information(1)),
            "attacker_has_target": bool(env._has_target_information(2)),
            "relay_cache_age": float(env._local_target_cache_age(1)),
            "blue_pos": env.blue_pos.tolist(),
            "target_pos": env.red_pos[0].tolist(),
        })
        if bool(dones[0, 0]):
            break
    outcome = "NEUTRALIZED" if info.get("target_neutralized", 0.0) > 0.5 else (
        "COLLISION" if info.get("collision", 0.0) > 0.5 else (
            "CONSTRAINT_FAILURE" if info.get("constraint_violation", 0.0) > 0.5 else (
                "TARGET_ESCAPE" if info.get("target_escape", 0.0) > 0.5 else "TIMEOUT"
            )
        )
    )
    return {
        "seed": seed,
        "mode": mode,
        "outcome": outcome,
        "steps": int(env.step_count),
        "records": records,
        "relay_reacquired_local_sensing": any(
            int(r["step"]) >= transition_step and float(r["relay_detected"]) > 0.5
            for r in records
        ),
        "scout_loss_observed": any(
            int(r["step"]) >= transition_step and not bool(r["scout_has_target"])
            for r in records
        ),
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    fixed = [run(seed, "fixed_responsibility") for seed in SEEDS]
    realloc = [run(seed, "reallocated") for seed in SEEDS]
    nominal_no_loss = [run(seed, "reallocated", transition_step=HORIZON + 1) for seed in SEEDS]
    fixed_success = sum(r["outcome"] == "NEUTRALIZED" for r in fixed)
    realloc_success = sum(r["outcome"] == "NEUTRALIZED" for r in realloc)
    nominal_no_loss_success = sum(r["outcome"] == "NEUTRALIZED" for r in nominal_no_loss)
    transition_valid = all(r["scout_loss_observed"] for r in fixed)
    backup_reacquired = all(r["relay_reacquired_local_sensing"] for r in realloc)
    if (
        nominal_no_loss_success == len(nominal_no_loss)
        and transition_valid
        and backup_reacquired
        and fixed_success < len(fixed)
        and realloc_success > fixed_success
    ):
        verdict = "NP1_PASS__RESPONSIBILITY_REALLOCATION_PROBLEM_IDENTIFIED__READY_FOR_METHOD_DESIGN"
    elif transition_valid and backup_reacquired:
        verdict = "NP1_PARTIAL__CAPABILITY_TRANSITION_VALID_BUT_REALLOCATION_NECESSITY_UNCLEAR"
    else:
        verdict = "NP1_NO_GO__DYNAMIC_CAPABILITY_PROBLEM_NOT_IDENTIFIABLE"
    report = {
        "protocol_version": PROTOCOL,
        "training": False,
        "transition_step": TRANSITION_STEP,
        "horizon": HORIZON,
        "target_policy": "weaving_param",
        "target_heading_amp": 0.65,
        "cache_ttl_steps": 12,
        "fixed_responsibility": fixed,
        "reallocated": realloc,
        "nominal_no_loss": nominal_no_loss,
        "fixed_responsibility_neutralized": fixed_success,
        "reallocated_neutralized": realloc_success,
        "nominal_no_loss_neutralized": nominal_no_loss_success,
        "nominal_no_loss_baseline_valid": nominal_no_loss_success == len(nominal_no_loss),
        "transition_valid": transition_valid,
        "backup_reacquired_local_sensing": backup_reacquired,
        "verdict": verdict,
    }
    (OUT / "NP1C_RECALIBRATION_REPORT.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (OUT / "NP1C_RECALIBRATION_MANIFEST.json").write_text(json.dumps({
        "protocol_version": PROTOCOL,
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "seeds": list(SEEDS),
        "uses_training": False,
        "uses_new_method": False,
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"{verdict}: fixed={fixed_success}/{len(fixed)} reallocated={realloc_success}/{len(realloc)} backup_reacquired={backup_reacquired}")


if __name__ == "__main__":
    main()
