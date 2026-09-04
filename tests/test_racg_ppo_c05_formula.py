import numpy as np

from scripts.audit_racg_ppo_c05_formula import racg_direction


MASSES = np.array([0.5] + [1.0 / 12.0] * 6)


def test_disagreement_is_exact_ordinary_fallback():
    rng = np.random.default_rng(7)
    left = rng.normal(size=(31, 7))
    entropy = rng.normal(size=31)
    result = racg_direction(left, -left, entropy, MASSES)
    assert result.reliability == 0.0
    assert np.array_equal(result.direction, result.ordinary)


def test_cross_fit_swap_and_scale_invariance():
    rng = np.random.default_rng(11)
    left = rng.normal(size=(41, 7))
    right = left + rng.normal(scale=0.2, size=(41, 7))
    entropy = rng.normal(scale=0.1, size=41)
    direct = racg_direction(left, right, entropy, MASSES)
    swapped = racg_direction(right, left, entropy, MASSES)
    scaled = racg_direction(4.0 * left, 4.0 * right, 4.0 * entropy, MASSES)
    assert np.allclose(direct.direction, swapped.direction)
    assert np.allclose(scaled.direction, 4.0 * direct.direction)
    assert np.isclose(scaled.reliability, direct.reliability)


def test_complete_actor_direction_cannot_be_cancelled():
    rng = np.random.default_rng(23)
    for _ in range(64):
        left = rng.normal(size=(29, 7))
        right = left + rng.normal(scale=0.8, size=(29, 7))
        entropy = rng.normal(scale=0.2, size=29)
        result = racg_direction(left, right, entropy, MASSES)
        assert np.linalg.norm(result.direction) + 1e-10 >= 0.5 * np.linalg.norm(result.ordinary)
        assert np.min(result.weights) >= -1e-10
        assert np.isclose(np.sum(result.weights), 1.0)
