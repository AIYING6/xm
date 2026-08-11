"""Deterministic regressions for the recipient-specific target contract."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from envs.uav_intercept_3d_env import ROLE_ATTACKER, ROLE_INTERCEPTOR, ROLE_SCOUT, UAVIntercept3DConfig, UAVIntercept3DEnv, velocity_from_state


def make_env() -> tuple[UAVIntercept3DEnv, int, int]:
    env = UAVIntercept3DEnv(UAVIntercept3DConfig(seed=61, strict_target_sensing=True, agent_target_info_bottleneck=True, communication_dropout_prob=1.0))
    env.reset()
    attacker = next(i for i, typ in enumerate(env.config.blue_types) if typ.role in {ROLE_ATTACKER, ROLE_INTERCEPTOR})
    scout = next(i for i, typ in enumerate(env.config.blue_types) if typ.role == ROLE_SCOUT)
    return env, scout, attacker


def clear_actor_target_evidence(env: UAVIntercept3DEnv, attacker: int) -> None:
    env.detected_by[attacker] = 0.0
    env.target_cache_valid[attacker] = 0.0
    env.target_cache_generation_step[attacker] = -1
    env.target_cache_confidence[attacker] = 0.0
    env.target_cache_path[attacker] = []
    env.sender_packet_cache[attacker].clear()


def target_velocity(env: UAVIntercept3DEnv) -> np.ndarray:
    return velocity_from_state(env.red_speed[0], env.red_heading[0], env.red_gamma[0])


def test_global_detection_is_hidden_without_recipient_evidence() -> None:
    env, _scout, attacker = make_env()
    clear_actor_target_evidence(env, attacker)
    env.last_detected_target_pos = None
    env.last_detected_target_vel = None
    before_actor = env._get_obs()[attacker].copy()
    before_critic = env._get_share_obs()[attacker].copy()
    env.last_detected_target_pos = env.red_pos[0].copy()
    env.last_detected_target_vel = target_velocity(env)
    after_actor = env._get_obs()[attacker]
    after_critic = env._get_share_obs()[attacker]
    assert np.array_equal(before_actor, after_actor)
    assert not np.array_equal(before_critic, after_critic), "privileged target state must remain critic-only when configured"


def test_local_sensing_updates_actor_target_feature() -> None:
    env, _scout, attacker = make_env()
    clear_actor_target_evidence(env, attacker)
    before = env._get_obs()[attacker, 8:15].copy()
    env.detected_by[attacker] = 1.0
    env._write_target_cache(attacker, pos=env.red_pos[0], vel=target_velocity(env), source=attacker,
                            generation_step=env.step_count, delivery_step=env.step_count, hop_count=0,
                            confidence=1.0, path=[attacker])
    after = env._get_obs()[attacker, 8:15]
    assert not np.array_equal(before, after)
    assert env.target_cache_path[attacker] == [attacker]


def test_delivered_cache_valid_packet_updates_actor_and_preserves_sender_provenance() -> None:
    env, scout, attacker = make_env()
    clear_actor_target_evidence(env, attacker)
    env.detected_by[scout] = 1.0
    env._write_target_cache(scout, pos=env.red_pos[0], vel=target_velocity(env), source=scout,
                            generation_step=env.step_count, delivery_step=env.step_count, hop_count=0,
                            confidence=1.0, path=[scout])
    packet = env._make_sender_status_packet(scout, env.step_count)
    env._store_sender_packet(attacker, packet, env.step_count)
    env._write_target_cache(attacker, pos=np.asarray(packet["target_pos"]), vel=np.asarray(packet["target_vel"]),
                            source=int(packet["sender_id"]), generation_step=int(packet["target_generation_step"]),
                            delivery_step=env.step_count, hop_count=int(packet["target_hop_count"]) + 1,
                            confidence=float(packet["target_confidence"]) * 0.95, path=[scout, attacker])
    assert env._has_fresh_target_cache(attacker)
    assert int(env.target_cache_source[attacker]) == scout
    assert env.target_cache_path[attacker] == [scout, attacker]
    assert env.sender_packet_cache[attacker][scout]["sender_id"] == scout
    assert np.any(env._get_obs()[attacker, 8:15] != 0.0)


def test_cache_age_boundary_and_expiry() -> None:
    env, scout, attacker = make_env()
    clear_actor_target_evidence(env, attacker)
    env.step_count = 100
    max_age = int(env.config.max_target_message_age_steps)
    env._write_target_cache(attacker, pos=env.red_pos[0], vel=target_velocity(env), source=scout,
                            generation_step=env.step_count - max_age, delivery_step=env.step_count - max_age,
                            hop_count=1, confidence=0.9, path=[scout, attacker])
    assert env._has_fresh_target_cache(attacker), "age == max age must remain legal"
    at_boundary = env._get_obs()[attacker, 8:15].copy()
    # The cache rejects an older generation by design. Clear it first so this
    # branch tests the age predicate itself rather than cache replacement.
    env.target_cache_valid[attacker] = 0.0
    env.target_cache_generation_step[attacker] = -1
    env._write_target_cache(attacker, pos=env.red_pos[0], vel=target_velocity(env), source=scout,
                            generation_step=env.step_count - max_age - 1, delivery_step=env.step_count - max_age - 1,
                            hop_count=1, confidence=0.9, path=[scout, attacker])
    assert not env._has_fresh_target_cache(attacker), "age == max age + 1 must be excluded"
    assert np.all(env._get_obs()[attacker, 8:15] == 0.0)
    assert np.any(at_boundary != 0.0)


def main() -> None:
    tests = [obj for name, obj in sorted(globals().items()) if name.startswith("test_") and callable(obj)]
    for test in tests:
        test(); print(f"PASS {test.__name__}")
    print(f"ACTOR_TARGET_INFORMATION_CONTRACT_TEST_REPORT: PASS ({len(tests)} tests)")


if __name__ == "__main__":
    main()
