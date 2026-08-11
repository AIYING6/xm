"""NP1 physical qualification for frozen G1/G2/G3 x R0/R1/R2."""

from __future__ import annotations

import json
import math
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.run_np0c_multi_candidate_responsibility_redesign import SCENARIOS  # noqa: E402
from scripts.run_np1_dynamic_capability_calibration import DynamicCapabilityAdapter  # noqa: E402
from scripts import run_new_project_l0_single_interceptor as l0  # noqa: E402
from scripts.run_np1c_responsibility_necessity_recalibration import cfg as base_cfg  # noqa: E402

OUT = ROOT / "results" / "np1_multi_candidate_responsibility_physical_qualification"
SEEDS = (9151, 9152, 9153, 9154)
TRANSITION_STEP = 10
HORIZON = 120
PROTOCOL = "NP1_MULTI_CANDIDATE_RESPONSIBILITY_PHYSICAL_QUALIFICATION_V1"


def scenario_config(seed: int):
    c = replace(base_cfg(seed), max_steps=HORIZON, target_policy="straight")
    types = list(c.blue_types)
    types[0] = replace(types[0], radar_range=17_500.0)
    types[1] = replace(types[1], radar_range=17_500.0)
    types[2] = replace(types[2], radar_range=17_500.0)
    return replace(c, blue_types=types)


def oracle_guidance(env: DynamicCapabilityAdapter) -> np.ndarray:
    raw = np.asarray(l0.scripted_oracle_actions(env)).reshape(-1)
    out = np.zeros((env.config.num_blue, 2), dtype=np.float32)
    for i, value in enumerate(raw[: env.config.num_blue]):
        mapped = l0.convert_oracle_action(int(value))
        out[i] = l0.GUIDANCE_ACTION_TABLE[mapped % l0.GUIDANCE_FLIGHT_ACTION_DIM]
    return out


def set_scenario(env: DynamicCapabilityAdapter, spec: dict[str, tuple[float, ...]]) -> None:
    env.red_pos[0] = np.asarray(spec["target"], dtype=np.float32)
    env.blue_pos[0] = np.asarray((-14_000.0, -5_500.0, 4_800.0), dtype=np.float32)
    env.blue_pos[1] = np.asarray(spec["relay"], dtype=np.float32)
    env.blue_pos[2] = np.asarray(spec["attacker"], dtype=np.float32)
    for i in range(env.config.num_blue):
        rel = env.red_pos[0] - env.blue_pos[i]
        env.blue_heading[i] = math.atan2(float(rel[1]), float(rel[0]))
        env.blue_gamma[i] = 0.0
    env._update_sensing_and_comm()


def run(seed: int, scenario_name: str, assignment: str) -> dict[str, object]:
    spec = SCENARIOS[scenario_name]
    transition = assignment != "R0"
    env = DynamicCapabilityAdapter(
        scenario_config(seed),
        transition_step=TRANSITION_STEP if transition else HORIZON + 1,
    )
    obs, _, _ = env.reset()
    set_scenario(env, spec)
    obs = env._get_obs()
    pre_actions: list[np.ndarray] = []
    records: list[dict[str, object]] = []
    info: dict[str, float] = {}
    takeover_id = 1 if assignment == "R1" else 2
    other_id = 2 if assignment == "R1" else 1
    while not env.done and env.step_count < HORIZON:
        if transition and env.step_count >= TRANSITION_STEP and assignment in {"R1", "R2"}:
            action = np.zeros((env.config.num_blue, 2), dtype=np.float32)
            action[takeover_id] = oracle_guidance(env)[takeover_id]
            action[other_id] = pre_actions[-1][other_id] if pre_actions else 0.0
        else:
            action = oracle_guidance(env)
        if env.step_count < TRANSITION_STEP:
            pre_actions.append(action.copy())
        obs, _, _, _, dones, info = env.step_guidance(action)
        records.append({
            "step": int(env.step_count),
            "action": action.tolist(),
            "scout_detected": float(env.detected_by[env.scout_id]),
            "relay_detected": float(env.detected_by[1]),
            "attacker_detected": float(env.detected_by[2]),
            "relay_has_target": bool(env._has_target_information(1)),
            "attacker_has_target": bool(env._has_target_information(2)),
            "positions": env.blue_pos.tolist(),
        })
        if bool(dones[0, 0]):
            break
    post = [r for r in records if int(r["step"]) >= TRANSITION_STEP]
    first_sense = next((int(r["step"]) for r in post if float(r["relay_detected"] if takeover_id == 1 else r["attacker_detected"]) > 0.5), None)
    outcome = "NEUTRALIZED" if info.get("target_neutralized", 0.0) > 0.5 else (
        "COLLISION" if info.get("collision", 0.0) > 0.5 else (
            "CONSTRAINT_FAILURE" if info.get("constraint_violation", 0.0) > 0.5 else "TIMEOUT"
        )
    )
    return {
        "seed": seed,
        "scenario": scenario_name,
        "assignment": assignment,
        "outcome": outcome,
        "steps": int(env.step_count),
        "takeover_agent": takeover_id,
        "first_takeover_local_sensing_step": first_sense,
        "records": records,
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = [run(seed, scenario, assignment) for scenario in SCENARIOS for assignment in ("R0", "R1", "R2") for seed in SEEDS]
    summary = {}
    for scenario in SCENARIOS:
        summary[scenario] = {}
        for assignment in ("R0", "R1", "R2"):
            subset = [r for r in rows if r["scenario"] == scenario and r["assignment"] == assignment]
            summary[scenario][assignment] = {
                "neutralized": sum(r["outcome"] == "NEUTRALIZED" for r in subset),
                "n": len(subset),
                "median_steps": float(np.median([r["steps"] for r in subset])),
                "median_first_takeover_sensing": float(np.median([r["first_takeover_local_sensing_step"] or HORIZON for r in subset])),
            }
    # NP0C ordering is a pre-registered direction; this physical qualification
    # reports it rather than selecting a new ordering post hoc.
    ordering = ["R1", "R2", "R1"]
    preferred_by_physical = []
    for scenario, preferred in zip(SCENARIOS, ordering):
        s = summary[scenario]
        # Prefer the candidate with lower median sensing latency among feasible
        # candidates; neutralization is reported separately, not optimized.
        preferred_by_physical.append(min(("R1", "R2"), key=lambda a: (s[a]["median_first_takeover_sensing"], -s[a]["neutralized"])))
    nominal_stable = all(summary[s]["R0"]["neutralized"] == len(SEEDS) for s in SCENARIOS)
    ordering_stable = preferred_by_physical == ordering
    both_candidates_nontrivial = all(summary[s][a]["neutralized"] > 0 for s in SCENARIOS for a in ("R1", "R2"))
    if nominal_stable and ordering_stable and both_candidates_nontrivial:
        verdict = "NP1_PASS__STATE_DEPENDENT_RESPONSIBILITY_REALLOCATION_PHYSICALLY_VALIDATED__READY_FOR_NP2_LEARNABILITY"
    elif nominal_stable:
        verdict = "NP1_PARTIAL__MULTI_CANDIDATE_CONSTRUCT_VALID_BUT_PHYSICAL_ORDERING_UNSTABLE"
    else:
        verdict = "NP1_NO_GO__MULTI_CANDIDATE_RESPONSIBILITY_DECISION_NOT_PHYSICALLY_IDENTIFIABLE"
    report = {
        "protocol_version": PROTOCOL,
        "training": False,
        "algorithm": None,
        "scenarios": list(SCENARIOS),
        "assignments": ["R0", "R1", "R2"],
        "summary": summary,
        "preregistered_ordering": ordering,
        "physical_preferred_ordering": preferred_by_physical,
        "nominal_stable": nominal_stable,
        "ordering_stable": ordering_stable,
        "both_candidates_nontrivial": both_candidates_nontrivial,
        "verdict": verdict,
    }
    (OUT / "NP1_PHYSICAL_QUALIFICATION_REPORT.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (OUT / "NP1_PHYSICAL_QUALIFICATION_MANIFEST.json").write_text(json.dumps({
        "protocol_version": PROTOCOL,
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "seeds": list(SEEDS),
        "scenario_count": len(SCENARIOS),
        "assignment_count": 3,
        "uses_training": False,
        "uses_new_method": False,
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"{verdict}: nominal_stable={nominal_stable} ordering={preferred_by_physical} prereg={ordering}")


if __name__ == "__main__":
    main()
