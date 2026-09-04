import numpy as np

from algorithms.ri_gmappo.racg_ppo import frozen_racg_direction
from scripts.audit_racg_ppo_c05_formula import racg_direction


def test_c1_implementation_matches_c05_frozen_reference():
    rng = np.random.default_rng(20260904)
    left = rng.normal(size=(73, 7))
    right = left + rng.normal(scale=0.4, size=(73, 7))
    entropy = rng.normal(scale=0.07, size=73)
    reference = racg_direction(left, right, entropy, np.array([0.5] + [1.0 / 12.0] * 6))
    actual = frozen_racg_direction(left, right, entropy)
    assert np.allclose(actual["direction"], reference.direction, atol=1e-10, rtol=1e-10)
    assert np.allclose(actual["weights"], reference.weights, atol=1e-10, rtol=1e-10)
    assert np.isclose(actual["reliability"], reference.reliability)


def test_c1_disagreement_falls_back_without_zeroing_ordinary():
    rng = np.random.default_rng(31)
    left = rng.normal(size=(37, 7))
    entropy = rng.normal(size=37)
    actual = frozen_racg_direction(left, -left, entropy)
    assert actual["ordinary_fallback"]
    assert np.array_equal(actual["direction"], actual["ordinary"])
    assert np.linalg.norm(actual["direction"]) > 0.0
