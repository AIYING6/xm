import numpy as np

from scripts.audit_capd_p05_teacher_signal import explorer_sets, js


def test_explorer_sets_are_cyclic_and_outcome_free() -> None:
    seeds = [71011, 71012, 71013, 71014, 71015]
    assert explorer_sets(seeds) == {
        71011: [71011, 71012, 71013],
        71012: [71012, 71013, 71014],
        71013: [71013, 71014, 71015],
        71014: [71014, 71015, 71011],
        71015: [71015, 71011, 71012],
    }


def test_js_is_zero_for_identical_probabilities_and_symmetric() -> None:
    left = np.asarray([[0.7, 0.2, 0.1]], dtype=np.float64)
    right = np.asarray([[0.1, 0.3, 0.6]], dtype=np.float64)
    assert np.allclose(js(left, left), 0.0, atol=1e-12)
    assert np.allclose(js(left, right), js(right, left), atol=1e-12)
    assert np.all(js(left, right) > 0.0)
