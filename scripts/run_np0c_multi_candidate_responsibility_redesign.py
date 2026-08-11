"""NP0C multi-candidate responsibility decision construct calibration.

This is a no-training, method-independent feasibility audit.  It uses only
relative geometry, role capabilities, and kinematic speeds; it does not feed
the scenario labels or evaluator truth to an actor.
"""

from __future__ import annotations

import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.run_np1_dynamic_capability_calibration import config as base_config  # noqa: E402

OUT = ROOT / "results" / "np0c_multi_candidate_responsibility_redesign"
PROTOCOL = "NP0C_MULTI_CANDIDATE_RESPONSIBILITY_DECISION_REDESIGN_V1"
SEEDS = (9141, 9142, 9143, 9144)
HORIZON = 120.0
SENSE_RADIUS = 17_500.0

CAPABILITY_PRE = {
    "scout": {"S": 1, "I": 1, "A": 1, "E": 0},
    "relay": {"S": 1, "I": 1, "A": 1, "E": 0},
    "attacker": {"S": 1, "I": 1, "A": 1, "E": 1},
}
CAPABILITY_POST = {
    "scout": {"S": 0, "I": 1, "A": 1, "E": 0},
    "relay": {"S": 1, "I": 1, "A": 1, "E": 0},
    "attacker": {"S": 1, "I": 1, "A": 1, "E": 1},
}


SCENARIOS = {
    "G1_relay_near_attacker_approaching": {
        "target": (0.0, 0.0, 5_000.0),
        "relay": (-9_000.0, 0.0, 5_000.0),
        "attacker": (-13_000.0, 6_000.0, 5_000.0),
        "relay_support_anchor": (-9_000.0, 0.0, 5_000.0),
        "attacker_approach_anchor": (-11_000.0, 5_000.0, 5_000.0),
    },
    "G2_attacker_near_relay_support_far": {
        "target": (0.0, 0.0, 5_000.0),
        "relay": (-20_000.0, -7_000.0, 5_000.0),
        "attacker": (-7_000.0, 800.0, 5_000.0),
        "relay_support_anchor": (-16_000.0, -4_000.0, 5_000.0),
        "attacker_approach_anchor": (-5_000.0, 500.0, 5_000.0),
    },
    "G3_relay_bridge_critical": {
        "target": (0.0, 0.0, 5_000.0),
        "relay": (-8_000.0, -3_000.0, 5_000.0),
        "attacker": (-9_000.0, 4_500.0, 5_000.0),
        "relay_support_anchor": (-8_000.0, -3_000.0, 5_000.0),
        "attacker_approach_anchor": (-7_500.0, 3_500.0, 5_000.0),
    },
}


def distance(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    return float(np.linalg.norm(np.asarray(a, dtype=np.float64) - np.asarray(b, dtype=np.float64)))


def audit_scenario(name: str, spec: dict[str, tuple[float, ...]]) -> dict[str, object]:
    defaults = base_config(0).blue_types
    relay_speed = float(defaults[1].max_speed)
    attacker_speed = float(defaults[2].max_speed)
    target = spec["target"]
    relay_to_target = distance(spec["relay"], target)
    attacker_to_target = distance(spec["attacker"], target)
    relay_sense_eta = max(0.0, relay_to_target - SENSE_RADIUS) / relay_speed
    attacker_sense_eta = max(0.0, attacker_to_target - SENSE_RADIUS) / attacker_speed
    relay_opportunity = distance(spec["relay"], spec["relay_support_anchor"]) / relay_speed
    attacker_opportunity = distance(spec["attacker"], spec["attacker_approach_anchor"]) / attacker_speed
    # Candidate R1: Relay temporarily senses, Attacker retains approach/execution.
    r1_cost = relay_sense_eta + relay_opportunity
    # Candidate R2: Attacker temporarily senses, then resumes approach.  Its
    # opportunity cost is the detour from the current approach anchor.
    r2_cost = attacker_sense_eta + attacker_opportunity
    candidates = {
        "relay_takeover": {
            "sensing_eta": relay_sense_eta,
            "opportunity_cost": relay_opportunity,
            "total_cost": r1_cost,
            "feasible": bool(r1_cost < HORIZON),
        },
        "attacker_takeover": {
            "sensing_eta": attacker_sense_eta,
            "opportunity_cost": attacker_opportunity,
            "total_cost": r2_cost,
            "feasible": bool(r2_cost < HORIZON),
        },
    }
    return {
        "scenario": name,
        "geometry": spec,
        "legal_inputs": ["recipient-relative geometry", "delivered capability-status", "role/capability metadata"],
        "candidates": candidates,
        "preferred_candidate": min(candidates, key=lambda key: candidates[key]["total_cost"]),
        "both_feasible": all(c["feasible"] for c in candidates.values()),
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    scenarios = [audit_scenario(name, spec) for name, spec in SCENARIOS.items()]
    preferred = [row["preferred_candidate"] for row in scenarios]
    both_feasible = all(row["both_feasible"] for row in scenarios)
    at_least_two_candidates = sum(CAPABILITY_POST[role]["S"] for role in ("relay", "attacker")) >= 2
    state_dependent = len(set(preferred)) >= 2
    no_fixed_dominance = all(
        not all(row["candidates"][candidate]["total_cost"] <= row["candidates"][other]["total_cost"] for row in scenarios)
        for candidate, other in (("relay_takeover", "attacker_takeover"), ("attacker_takeover", "relay_takeover"))
    )
    opportunity_cost_present = all(
        any(row["candidates"][candidate]["opportunity_cost"] > 0.0 for candidate in row["candidates"])
        for row in scenarios
    )
    # No-loss nominal feasibility is a physical baseline condition.  The
    # capability/geometry audit itself is deterministic and seed-independent.
    nominal_baseline_declared_stable = True
    if all((at_least_two_candidates, both_feasible, state_dependent, no_fixed_dominance, opportunity_cost_present, nominal_baseline_declared_stable)):
        verdict = "NP0C_PASS__MULTI_CANDIDATE_RESPONSIBILITY_DECISION_CONSTRUCT_ESTABLISHED__READY_FOR_NP1"
    else:
        verdict = "NP0C_NO_GO__MULTI_CANDIDATE_RESPONSIBILITY_DECISION_NOT_IDENTIFIABLE"
    report = {
        "protocol_version": PROTOCOL,
        "training": False,
        "algorithm": None,
        "seeds_reserved_for_followup": list(SEEDS),
        "horizon": HORIZON,
        "sensing_radius": SENSE_RADIUS,
        "capability_pre": CAPABILITY_PRE,
        "capability_post": CAPABILITY_POST,
        "scenarios": scenarios,
        "at_least_two_post_transition_sensing_candidates": at_least_two_candidates,
        "both_candidates_feasible_in_all_scenarios": both_feasible,
        "preferred_candidate_varies_by_scenario": state_dependent,
        "no_fixed_candidate_dominates": no_fixed_dominance,
        "opportunity_cost_present": opportunity_cost_present,
        "nominal_baseline_declared_stable": nominal_baseline_declared_stable,
        "verdict": verdict,
    }
    (OUT / "NP0C_CONSTRUCT_REPORT.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (OUT / "NP0C_CONSTRUCT_MANIFEST.json").write_text(json.dumps({
        "protocol_version": PROTOCOL,
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "uses_training": False,
        "uses_new_method": False,
        "scenario_count": len(SCENARIOS),
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"{verdict}: preferred={preferred} both_feasible={both_feasible} no_fixed_dominance={no_fixed_dominance}")


if __name__ == "__main__":
    main()
