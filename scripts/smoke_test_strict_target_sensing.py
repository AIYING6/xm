from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from envs.uav_intercept_3d_env import UAVIntercept3DConfig, UAVIntercept3DEnv


def target_from_local_obs(env: UAVIntercept3DEnv, obs: np.ndarray, agent_id: int = 0) -> np.ndarray:
    rel = np.asarray(
        [
            obs[agent_id, 8] * env.config.world_radius,
            obs[agent_id, 9] * env.config.world_radius,
            obs[agent_id, 10] * env.config.max_altitude,
        ],
        dtype=np.float32,
    )
    return env.blue_pos[agent_id] + rel


def target_from_graph(env: UAVIntercept3DEnv, graph: dict[str, np.ndarray]) -> np.ndarray:
    node = graph["node_feat"][-1]
    return np.asarray(
        [
            node[0] * env.config.world_radius,
            node[1] * env.config.world_radius,
            node[2] * env.config.max_altitude,
        ],
        dtype=np.float32,
    )


def assert_close(name: str, actual: np.ndarray, expected: np.ndarray, atol: float = 1e-3) -> None:
    if not np.allclose(actual, expected, atol=atol):
        raise AssertionError(f"{name}: expected {expected}, got {actual}")


def main() -> None:
    legacy_env = UAVIntercept3DEnv(
        UAVIntercept3DConfig(seed=7, target_policy="straight", radar_dropout_prob=1.0, strict_target_sensing=False)
    )
    legacy_obs, _, legacy_graph = legacy_env.reset()
    assert legacy_env.last_detected_target_pos is None
    assert_close("legacy local target", target_from_local_obs(legacy_env, legacy_obs), legacy_env.red_pos[0])
    assert_close("legacy graph target", target_from_graph(legacy_env, legacy_graph), legacy_env.red_pos[0])

    strict_env = UAVIntercept3DEnv(
        UAVIntercept3DConfig(seed=7, target_policy="straight", radar_dropout_prob=1.0, strict_target_sensing=True)
    )
    strict_obs, _, strict_graph = strict_env.reset()
    prior = np.asarray(strict_env.config.target_prior_position, dtype=np.float32)
    assert strict_env.last_detected_target_pos is None
    assert strict_env._info(timeout=False)["target_estimate_is_prior"] == 1.0
    assert_close("strict local target prior", target_from_local_obs(strict_env, strict_obs), prior)
    assert_close("strict graph target prior", target_from_graph(strict_env, strict_graph), prior)
    if np.allclose(prior, strict_env.red_pos[0], atol=1e-3):
        raise AssertionError("strict target prior unexpectedly equals sampled target truth")

    print("strict target sensing smoke: OK")


if __name__ == "__main__":
    main()
