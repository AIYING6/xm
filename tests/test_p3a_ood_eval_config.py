# test_p3a_ood_eval_config.py — P3-A OOD eval-side config invariants (no checkpoints).
import numpy as np
import pytest

from algorithms.ri_gmappo.simple_ri_gmappo import RIGMAPPOConfig, make_env

BASE = dict(
    env_name="3d_intercept", seed=1, target_policy="straight",
    communication_dropout_prob=0.0, message_delay_steps=0,
    radar_dropout_prob=0.0, strict_target_sensing=True,
    agent_target_info_bottleneck=True, failed_blue_agent=1,
    node_failure_start_step=25, node_failure_duration_steps=80,
    communication_range_scale=1.0,
)


def mk(over: dict):
    cfg = dict(BASE)
    cfg.update(over)
    return make_env(RIGMAPPOConfig(**cfg), seed=1, training=False)


def step(env, n=3):
    obs, so, g = env.reset()
    act = np.zeros(env.config.num_blue, dtype=np.int64)
    for _ in range(n):
        obs, so, g, rew, done, info = env.step(act)
        if np.all(done):
            break
    return env


def test_default_reset_noop():
    env = mk({})
    env.reset()
    assert np.allclose(env.blue_pos[0], [-14000.0, -5500.0, 4800.0])
    assert np.allclose(env.blue_pos[1], [-16000.0, 0.0, 5200.0])
    assert np.allclose(env.blue_pos[2], [-14000.0, 5500.0, 4600.0])
    assert np.allclose(env.red_pos[0, [0, 2]], [10000.0, 5000.0])


def test_g1_centroid_preserved():
    e0 = mk({}); e0.reset()
    e1 = mk({"blue_init_spacing_scale": 1.2, "blue_init_rotation_deg": 20.0}); e1.reset()
    c0 = e0.blue_pos[:, :2].mean(0); c1 = e1.blue_pos[:, :2].mean(0)
    assert np.allclose(c0, c1, atol=1e-2)


def test_g1_spacing_scale_exact():
    e0 = mk({}); e0.reset()
    e1 = mk({"blue_init_spacing_scale": 1.2, "blue_init_rotation_deg": 0.0}); e1.reset()
    c0 = e0.blue_pos[:, :2].mean(0); c1 = e1.blue_pos[:, :2].mean(0)
    d0 = np.linalg.norm(e0.blue_pos[:, :2] - c0, axis=1)
    d1 = np.linalg.norm(e1.blue_pos[:, :2] - c1, axis=1)
    assert np.allclose(d1, d0 * 1.2, atol=1e-2)


def test_g1_rotation_exact():
    e0 = mk({}); e0.reset()
    e1 = mk({"blue_init_rotation_deg": 20.0}); e1.reset()
    c0 = e0.blue_pos[:, :2].mean(0); c1 = e1.blue_pos[:, :2].mean(0)
    v0 = e0.blue_pos[0, :2] - c0; v1 = e1.blue_pos[0, :2] - c1
    a0 = np.arctan2(v0[1], v0[0]); a1 = np.arctan2(v1[1], v1[0])
    diff = np.degrees((a1 - a0) % (2 * np.pi))
    assert abs(diff - 20.0) < 0.1 or abs(diff - (20.0 - 360.0)) < 0.1


def test_g2_range_scale_exact():
    e0 = mk({}); e0.reset()
    e1 = mk({"target_init_range_scale": 1.4, "target_init_bearing_offset_deg": 0.0}); e1.reset()
    c0 = e0.blue_pos[:, :2].mean(0); c1 = e1.blue_pos[:, :2].mean(0)
    r0 = np.linalg.norm(e0.red_pos[0, :2] - c0)
    r1 = np.linalg.norm(e1.red_pos[0, :2] - c1)
    assert np.allclose(r1, r0 * 1.4, atol=1e-2)


def test_g2_bearing_offset_exact():
    e0 = mk({}); e0.reset()
    e1 = mk({"target_init_bearing_offset_deg": 25.0}); e1.reset()
    c0 = e0.blue_pos[:, :2].mean(0); c1 = e1.blue_pos[:, :2].mean(0)
    b0 = np.arctan2(e0.red_pos[0, 1] - c0[1], e0.red_pos[0, 0] - c0[0])
    b1 = np.arctan2(e1.red_pos[0, 1] - c1[1], e1.red_pos[0, 0] - c1[0])
    diff = np.degrees((b1 - b0) % (2 * np.pi))
    assert abs(diff - 25.0) < 0.1 or abs(diff - (25.0 - 360.0)) < 0.1


def _longest_pair(env):
    xy = env.blue_pos[:, :2]
    dists = np.linalg.norm(xy[:, None, :] - xy[None, :, :], axis=-1)
    np.fill_diagonal(dists, -np.inf)
    a, b = np.unravel_index(int(np.argmax(dists)), dists.shape)
    lo = a if env.blue_pos[a, 1] <= env.blue_pos[b, 1] else b
    hi = b if lo == a else a
    return lo, hi


def test_c1_symmetric_prune():
    # large comm range so the longest pair is reachable in the unpruned case
    env = mk({"comm_topology_mode": "symmetric_longest_prune",
              "communication_range_scale": 10.0})
    env.reset()
    lo, hi = _longest_pair(env)
    assert sorted(env._ood_prune_links) == sorted([(lo, hi), (hi, lo)])
    env = step(env, 3)
    # both directions pruned after comm update
    assert env.comm_adj[hi, lo] == 0.0 and env.comm_adj[lo, hi] == 0.0


def test_c2_directed_prune_only():
    env = mk({"comm_topology_mode": "directed_longest_prune",
              "communication_range_scale": 10.0})
    env.reset()
    lo, hi = _longest_pair(env)
    assert env._ood_prune_links == [(lo, hi)]  # lower-y -> higher-y only
    env = step(env, 3)
    assert env.comm_adj[hi, lo] == 0.0   # lower-y -> higher-y pruned
    assert env.comm_adj[lo, hi] == 1.0   # reverse kept


def test_j1_composition():
    env = mk({"blue_init_spacing_scale": 1.2, "blue_init_rotation_deg": 20.0,
              "target_policy": "weaving", "comm_topology_mode": "symmetric_longest_prune"})
    env.reset()
    assert len(env._ood_prune_links) == 2
    assert env.config.target_policy == "weaving"


@pytest.mark.parametrize("cell_over", [
    {"blue_init_spacing_scale": 1.2, "blue_init_rotation_deg": 20.0},
    {"target_init_range_scale": 1.4, "target_init_bearing_offset_deg": 25.0},
    {"target_policy": "weaving"},
    {"target_policy": "break_turn"},
    {"comm_topology_mode": "symmetric_longest_prune"},
    {"comm_topology_mode": "directed_longest_prune"},
    {"blue_init_spacing_scale": 1.2, "blue_init_rotation_deg": 20.0,
     "target_policy": "weaving", "comm_topology_mode": "symmetric_longest_prune"},
])
def test_all_cells_interface_smoke(cell_over):
    env = mk(cell_over)
    obs, so, g = env.reset()
    act = np.zeros(env.config.num_blue, dtype=np.int64)
    for _ in range(5):
        obs, so, g, rew, done, info = env.step(act)
        assert g["relation_adj"].shape == (3, 4, 4)
        if np.all(done):
            break


def test_happo_same_env_config():
    # HAPPO uses the same make_env; verify OOD overrides flow into the env
    env = mk({"blue_init_spacing_scale": 1.2, "blue_init_rotation_deg": 20.0})
    env.reset()
    c = env.blue_pos[:, :2].mean(0)
    d = np.linalg.norm(env.blue_pos[:, :2] - c, axis=1)
    base = mk({}); base.reset()
    c0 = base.blue_pos[:, :2].mean(0)
    d0 = np.linalg.norm(base.blue_pos[:, :2] - c0, axis=1)
    assert np.allclose(d, d0 * 1.2, atol=1e-2)
