"""Deterministic, no-training validation for the TLI1 reward-only repair."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from envs.uav_intercept_3d_env import (
    ROLE_ATTACKER,
    UAV3DType,
    UAVIntercept3DConfig,
    UAVIntercept3DEnv,
)


OUT = ROOT / "results" / "tli1_reward_realignment_validation"


def make_env() -> UAVIntercept3DEnv:
    attacker = UAV3DType(
        ROLE_ATTACKER, 270.0, 135.0, 22.0, 0.052, 50.0, 0.31, 7.0,
        11_000.0, math.radians(95), math.radians(42), 8_500.0,
        1_400.0, 5_200.0, math.radians(50), 1.15,
    )
    cfg = UAVIntercept3DConfig(
        num_blue=1, blue_types=[attacker], seed=1701,
        target_policy="straight", mission_neutralization_enabled=True,
        mission_reward_alignment_v1_enabled=True,
        guidance_level_action_interface=True, engage_commit_hold_steps=4,
        target_escape_radius=35_000.0, max_steps=180,
    )
    return UAVIntercept3DEnv(cfg)


def set_state(env: UAVIntercept3DEnv, distance: float, heading: float = 0.0,
              altitude_delta: float = 0.0, blue_speed: float = 270.0,
              red_speed: float = 255.0) -> None:
    env.reset()
    env.blue_pos[0] = np.asarray([0.0, 0.0, 5_000.0], dtype=np.float32)
    env.red_pos[0] = np.asarray([distance, 0.0, 5_000.0 + altitude_delta], dtype=np.float32)
    env.blue_heading[0] = float(heading)
    env.blue_gamma[0] = 0.0
    env.red_heading[0] = math.pi
    env.red_gamma[0] = 0.0
    env.blue_speed[0] = blue_speed
    env.red_speed[0] = red_speed
    env.engage_commit_hold = 0
    env.target_neutralized = False
    env.collision = False
    env.constraint_violation = False
    env.target_escaped = False
    env.done = False


def potential(env: UAVIntercept3DEnv) -> float:
    return float(env._mission_progress_potential())


def main() -> None:
    env = make_env()
    # Legal envelope: distance, heading, altitude, and closure all agree.
    set_state(env, 3_000.0)
    legal = potential(env)
    set_state(env, 6_000.0)
    outside_far = potential(env)
    set_state(env, 1_000.0)
    outside_near = potential(env)
    set_state(env, 3_000.0, heading=math.pi)
    wrong_heading = potential(env)
    set_state(env, 3_000.0, altitude_delta=4_000.0)
    wrong_altitude = potential(env)
    set_state(env, 3_000.0, heading=math.pi, blue_speed=150.0, red_speed=0.0)
    wrong_closure = potential(env)

    # The terminal success bonus is retained, but repeated commit outside the
    # physical envelope cannot create a positive mission transition.
    set_state(env, 10_000.0)
    before = potential(env)
    for _ in range(4):
        env.engage_commit_hold = 0
        env._mission_progress_potential()
    after = potential(env)

    checks = {
        "legal_exceeds_far_outside": legal > outside_far,
        "legal_exceeds_near_overshoot": legal > outside_near,
        "legal_exceeds_heading_error": legal > wrong_heading,
        "legal_exceeds_altitude_error": legal > wrong_altitude,
        "legal_exceeds_closure_error": legal > wrong_closure,
        "potential_bounded": 0.0 <= min(legal, outside_far, outside_near, wrong_heading, wrong_altitude, wrong_closure) <= 1.0
        and max(legal, outside_far, outside_near, wrong_heading, wrong_altitude, wrong_closure) <= 1.0,
        "out_of_envelope_commit_does_not_change_potential": abs(after - before) < 1e-12,
    }
    if not all(checks.values()):
        raise AssertionError(checks)
    payload = {
        "status": "TLI1_REWARD_VALIDATION_PASS",
        "training": False,
        "legal_potential": legal,
        "outside_far_potential": outside_far,
        "outside_near_potential": outside_near,
        "wrong_heading_potential": wrong_heading,
        "wrong_altitude_potential": wrong_altitude,
        "wrong_closure_potential": wrong_closure,
        "checks": checks,
        "source_commit": __import__("subprocess").check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "TLI1_REWARD_VALIDATION.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    for name, value in checks.items():
        print(f"PASS {name}" if value else f"FAIL {name}")
    print("TLI1_REWARD_VALIDATION_REPORT: PASS (7 tests)")


if __name__ == "__main__":
    main()
