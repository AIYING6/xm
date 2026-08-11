"""Deterministic preflight for relay-path task redesign.

It guards against treating a topology as relay-dependent while an attacker
observation can still read the environment-wide latest target detection.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from envs.uav_intercept_3d_env import ROLE_ATTACKER, ROLE_INTERCEPTOR, velocity_from_state
from scripts.run_l4_delay_development import cfg
from scripts import run_new_project_l0_single_interceptor as l0


def main() -> None:
    run_cfg = cfg(8901, ROOT / "results" / "_l5_contract_preflight", updates=1)
    assert run_cfg.strict_target_sensing is True
    assert run_cfg.agent_target_info_bottleneck is False
    env = l0.make_env(run_cfg, 901_001, training=False)
    env.reset()
    attacker = next(i for i, typ in enumerate(env.config.blue_types) if typ.role in {ROLE_ATTACKER, ROLE_INTERCEPTOR})
    # Establish the condition that should make target information unavailable
    # to the attacker under a recipient-specific execution contract.
    env.detected_by[:] = 0.0
    env.target_cache_valid[:] = 0.0
    env.target_cache_generation_step[:] = -1
    env.last_detected_target_pos = None
    env.last_detected_target_vel = None
    before = env._get_obs()[attacker, 8:15].copy()
    # This is a source claimed by a different, unspecified detector. No sender
    # packet or attacker cache is created.
    env.last_detected_target_pos = env.red_pos[0].copy()
    env.last_detected_target_vel = velocity_from_state(env.red_speed[0], env.red_heading[0], env.red_gamma[0])
    after = env._get_obs()[attacker, 8:15].copy()
    assert not np.array_equal(before, after), "attacker observation unexpectedly hid global detection"
    assert env.target_cache_valid[attacker] <= 0.5
    assert not env.sender_packet_cache[attacker]
    print("L5_RELAY_PATH_ACTOR_CONTRACT_PREFLIGHT: FAIL AS EXPECTED")
    print("attacker observation changes from global last_detected_target despite no local detection, delivered packet, or cache-valid target claim")


if __name__ == "__main__":
    main()
