import numpy as np

from scripts.audit_racg_ppo_p0 import bounded_anchored_direction, cross_fitted_gram


def test_zero_reliability_is_exact_ordinary_fallback():
    ordinary = np.array([1.0, -2.0, 3.0])
    robust = np.array([-4.0, 5.0, 6.0])
    result = bounded_anchored_direction(ordinary, robust, 0.0, 0.5)
    assert np.array_equal(result, ordinary)


def test_bounded_correction_cannot_cancel_nonzero_anchor():
    ordinary = np.array([1.0, 0.0])
    robust = np.array([-100.0, 0.0])
    result = bounded_anchored_direction(ordinary, robust, 1.0, 0.5)
    assert np.linalg.norm(result) >= 0.5 * np.linalg.norm(ordinary)
    assert result[0] > 0.0


def test_cross_fitted_gram_is_symmetric():
    left = np.arange(21, dtype=np.float64).reshape(3, 7)
    right = np.flip(left, axis=0).copy()
    gram = cross_fitted_gram(left, right)
    assert np.allclose(gram, gram.T)
