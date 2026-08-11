"""NP1R lexicographic physical opportunity-cost formalization."""

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

OUT = ROOT / "results" / "np1r_physical_opportunity_cost_formalization"
SEEDS = (9161, 9162, 9163, 9164)
TRANSITION_STEP = 10
HORIZON = 120
PROTOCOL = "NP1R_PHYSICAL_OPPORTUNITY_COST_FORMALIZATION_V1"

VALIDATION_SCENARIOS = {
    "G4_relay_close_attacker_far": {"target": (0.0, 0.0, 5_000.0), "relay": (-7_000.0, -2_000.0, 5_000.0), "attacker": (-16_000.0, 7_000.0, 5_000.0)},
    "G5_attacker_close_relay_far": {"target": (0.0, 0.0, 5_000.0), "relay": (-20_000.0, -8_000.0, 5_000.0), "attacker": (-6_000.0, 700.0, 5_000.0)},
    "G6_balanced_bridge": {"target": (0.0, 0.0, 5_000.0), "relay": (-8_500.0, -3_500.0, 5_000.0), "attacker": (-9_500.0, 4_000.0, 5_000.0)},
}


def cfg(seed: int):
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


def set_geometry(env: DynamicCapabilityAdapter, spec: dict[str, tuple[float, ...]]) -> None:
    env.red_pos[0] = np.asarray(spec["target"], dtype=np.float32)
    env.blue_pos[0] = np.asarray((-14_000.0, -5_500.0, 4_800.0), dtype=np.float32)
    env.blue_pos[1] = np.asarray(spec["relay"], dtype=np.float32)
    env.blue_pos[2] = np.asarray(spec["attacker"], dtype=np.float32)
    for i in range(env.config.num_blue):
        rel = env.red_pos[0] - env.blue_pos[i]
        env.blue_heading[i] = math.atan2(float(rel[1]), float(rel[0]))
        env.blue_gamma[i] = 0.0
    env._update_sensing_and_comm()


def run(seed: int, scenario: str, spec: dict[str, tuple[float, ...]], assignment: str) -> dict[str, object]:
    env = DynamicCapabilityAdapter(cfg(seed), transition_step=TRANSITION_STEP)
    obs, _, _ = env.reset()
    set_geometry(env, spec)
    pre_actions: list[np.ndarray] = []
    records: list[dict[str, object]] = []
    info: dict[str, float] = {}
    takeover = 1 if assignment == "R1" else 2
    other = 2 if takeover == 1 else 1
    while not env.done and env.step_count < HORIZON:
        action = np.zeros((env.config.num_blue, 2), dtype=np.float32)
        if env.step_count < TRANSITION_STEP:
            action = oracle_guidance(env)
            pre_actions.append(action.copy())
        else:
            action[takeover] = oracle_guidance(env)[takeover]
            action[other] = pre_actions[-1][other] if pre_actions else 0.0
        obs, _, _, _, dones, info = env.step_guidance(action)
        records.append({"step": int(env.step_count), "positions": env.blue_pos.tolist(), "takeover_detected": float(env.detected_by[takeover])})
        if bool(dones[0, 0]):
            break
    first_sense = next((int(r["step"]) for r in records if int(r["step"]) >= TRANSITION_STEP and r["takeover_detected"] > 0.5), HORIZON)
    outcome = "NEUTRALIZED" if info.get("target_neutralized", 0.0) > 0.5 else "FAILURE"
    positions = np.asarray([r["positions"] for r in records], dtype=np.float64)
    takeover_displacement = float(np.sum(np.linalg.norm(np.diff(positions[:, takeover, :], axis=0), axis=1))) if len(positions) > 1 else 0.0
    return {"seed": seed, "scenario": scenario, "assignment": assignment, "outcome": outcome, "steps": int(env.step_count), "first_sensing_step": first_sense, "takeover_displacement": takeover_displacement, "records": records}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    all_scenarios = {**SCENARIOS, **VALIDATION_SCENARIOS}
    rows = []
    for scenario, spec in all_scenarios.items():
        for assignment in ("R1", "R2"):
            for seed in SEEDS:
                rows.append(run(seed, scenario, spec, assignment))
    summary = {}
    for scenario in all_scenarios:
        summary[scenario] = {}
        for assignment in ("R1", "R2"):
            subset = [r for r in rows if r["scenario"] == scenario and r["assignment"] == assignment]
            # Frozen physical cost: lexicographic, no tunable weights.
            summary[scenario][assignment] = {
                "cost_tuple": [
                    int(not all(r["outcome"] == "NEUTRALIZED" for r in subset)),
                    float(np.median([r["steps"] for r in subset])),
                    float(np.median([r["first_sensing_step"] for r in subset])),
                    float(np.median([r["takeover_displacement"] for r in subset])),
                ],
                "neutralized": sum(r["outcome"] == "NEUTRALIZED" for r in subset),
                "n": len(subset),
            }
    winners = {scenario: min(("R1", "R2"), key=lambda a: tuple(summary[scenario][a]["cost_tuple"])) for scenario in all_scenarios}
    calibration_winners = [winners[s] for s in SCENARIOS]
    validation_winners = [winners[s] for s in VALIDATION_SCENARIOS]
    diverse = len(set(validation_winners)) == 2
    stable = all(
        len({r["outcome"] == "NEUTRALIZED" for r in rows if r["scenario"] == s and r["assignment"] == a}) == 1
        for s in all_scenarios for a in ("R1", "R2")
    )
    if diverse and stable:
        verdict = "NP1_PASS__PHYSICALLY_GROUNDED_STATE_DEPENDENT_REALLOCATION_ESTABLISHED__READY_FOR_NP2_LEARNABILITY"
    else:
        verdict = "NP1_NO_GO__RESPONSIBILITY_CHOICE_NOT_PHYSICALLY_STABLE"
    report = {
        "protocol_version": PROTOCOL,
        "training": False,
        "algorithm": None,
        "cost_definition": "lexicographic(failure, median_neutralization_steps, median_fresh_sensing_latency, median_takeover_displacement)",
        "calibration_scenarios": list(SCENARIOS),
        "validation_scenarios": list(VALIDATION_SCENARIOS),
        "summary": summary,
        "calibration_winners": calibration_winners,
        "validation_winners": validation_winners,
        "validation_has_both_winners": diverse,
        "outcome_stable_across_seeds": stable,
        "verdict": verdict,
    }
    (OUT / "NP1R_OPPORTUNITY_COST_REPORT.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (OUT / "NP1R_OPPORTUNITY_COST_MANIFEST.json").write_text(json.dumps({
        "protocol_version": PROTOCOL,
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "seeds": list(SEEDS),
        "uses_training": False,
        "uses_new_method": False,
        "weights_tuned": False,
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"{verdict}: validation_winners={validation_winners} stable={stable}")


if __name__ == "__main__":
    main()
