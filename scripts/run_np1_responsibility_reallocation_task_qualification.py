"""NP1 qualification of the NP0B responsibility-reallocation construct."""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.run_np0b_capability_responsibility_feasibility import (  # noqa: E402
    CAPABILITY_MATRIX_POST,
    R0,
    R1,
)
from scripts.run_np1_dynamic_capability_calibration import DynamicCapabilityAdapter  # noqa: E402
from scripts import run_new_project_l0_single_interceptor as l0  # noqa: E402
from scripts.run_np1c_responsibility_necessity_recalibration import cfg as base_cfg  # noqa: E402

OUT = ROOT / "results" / "np1_responsibility_reallocation_task_qualification"
SEEDS = (9131, 9132, 9133, 9134)
TRANSITION_STEP = 10
HORIZON = 120
PROTOCOL = "NP1_RESPONSIBILITY_REALLOCATION_TASK_QUALIFICATION_V1"


def cfg(seed: int):
    # NP0B physical task is frozen: straight target, overlap-capable Relay,
    # same geometry and cache semantics.  No new onset/TTL tuning here.
    return replace(base_cfg(seed), max_steps=HORIZON, target_policy="straight")


def oracle_guidance(env: DynamicCapabilityAdapter) -> np.ndarray:
    raw = np.asarray(l0.scripted_oracle_actions(env)).reshape(-1)
    out = np.zeros((env.config.num_blue, 2), dtype=np.float32)
    for i, value in enumerate(raw[: env.config.num_blue]):
        mapped = l0.convert_oracle_action(int(value))
        out[i] = l0.GUIDANCE_ACTION_TABLE[mapped % l0.GUIDANCE_FLIGHT_ACTION_DIM]
    return out


def run(seed: int, condition: str) -> dict[str, object]:
    transition = condition != "A_no_loss_R0"
    env = DynamicCapabilityAdapter(cfg(seed), transition_step=TRANSITION_STEP if transition else HORIZON + 1)
    obs, _, _ = env.reset()
    pre_actions: list[np.ndarray] = []
    records: list[dict[str, object]] = []
    info: dict[str, float] = {}
    while not env.done and env.step_count < HORIZON:
        if condition == "B_loss_frozen_R0" and env.step_count >= TRANSITION_STEP and pre_actions:
            # Frozen R0: continue the pre-transition policy; Relay does not
            # take a new sensing/approach responsibility.
            action = pre_actions[-1].copy()
        else:
            action = oracle_guidance(env)
        if env.step_count < TRANSITION_STEP:
            pre_actions.append(action.copy())
        obs, _, _, _, dones, info = env.step_guidance(action)
        records.append({
            "step": int(env.step_count),
            "action": action.tolist(),
            "scout_detected": float(env.detected_by[env.scout_id]),
            "scout_has_target": bool(env._has_target_information(env.scout_id)),
            "relay_detected": float(env.detected_by[1]),
            "relay_has_target": bool(env._has_target_information(1)),
            "attacker_has_target": bool(env._has_target_information(2)),
            "attacker_cache_age": float(env._local_target_cache_age(2)),
        })
        if bool(dones[0, 0]):
            break
    outcome = "NEUTRALIZED" if info.get("target_neutralized", 0.0) > 0.5 else (
        "COLLISION" if info.get("collision", 0.0) > 0.5 else (
            "CONSTRAINT_FAILURE" if info.get("constraint_violation", 0.0) > 0.5 else "TIMEOUT"
        )
    )
    post = [r for r in records if int(r["step"]) >= TRANSITION_STEP]
    return {
        "seed": seed,
        "condition": condition,
        "outcome": outcome,
        "steps": int(env.step_count),
        "records": records,
        "scout_loss_observed": transition and any(not r["scout_has_target"] for r in post),
        "relay_new_local_sensing": condition == "C_loss_R1" and any(float(r["relay_detected"]) > 0.5 for r in post),
        "attacker_fresh_evidence_restored": condition == "C_loss_R1" and any(bool(r["attacker_has_target"]) for r in post),
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    a = [run(seed, "A_no_loss_R0") for seed in SEEDS]
    b = [run(seed, "B_loss_frozen_R0") for seed in SEEDS]
    c = [run(seed, "C_loss_R1") for seed in SEEDS]
    a_success = sum(r["outcome"] == "NEUTRALIZED" for r in a)
    b_success = sum(r["outcome"] == "NEUTRALIZED" for r in b)
    c_success = sum(r["outcome"] == "NEUTRALIZED" for r in c)
    capability_only_unique = sum(
        int(CAPABILITY_MATRIX_POST[role]["S"]) == 1 for role in ("scout", "relay", "attacker")
    ) == 1
    evidence_chain = all(r["scout_loss_observed"] and r["relay_new_local_sensing"] for r in c)
    if a_success == len(a) and b_success < a_success and c_success > b_success and evidence_chain and not capability_only_unique:
        verdict = "NP1_PASS__DYNAMIC_RESPONSIBILITY_DECISION_PROBLEM_IDENTIFIED__READY_FOR_NP2_LEARNABILITY"
    elif evidence_chain and capability_only_unique:
        verdict = "NP1_PARTIAL__REALLOCATION_VALID_BUT_DECISION_COMPLEXITY_INSUFFICIENT"
    else:
        verdict = "NP1_NO_GO__RESPONSIBILITY_REALLOCATION_NOT_IDENTIFIABLE"
    report = {
        "protocol_version": PROTOCOL,
        "training": False,
        "algorithm": None,
        "assignment_R0": R0,
        "assignment_R1": R1,
        "A_no_loss_R0": a,
        "B_loss_frozen_R0": b,
        "C_loss_R1": c,
        "A_neutralized": a_success,
        "B_neutralized": b_success,
        "C_neutralized": c_success,
        "capability_only_rule_unique": capability_only_unique,
        "evidence_chain_C": evidence_chain,
        "verdict": verdict,
    }
    (OUT / "NP1_QUALIFICATION_REPORT.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (OUT / "NP1_QUALIFICATION_MANIFEST.json").write_text(json.dumps({
        "protocol_version": PROTOCOL,
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "seeds": list(SEEDS),
        "conditions": ["A_no_loss_R0", "B_loss_frozen_R0", "C_loss_R1"],
        "uses_training": False,
        "uses_new_method": False,
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"{verdict}: A={a_success}/{len(a)} B={b_success}/{len(b)} C={c_success}/{len(c)} unique_rule={capability_only_unique}")


if __name__ == "__main__":
    main()
