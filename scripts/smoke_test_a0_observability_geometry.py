"""Numerical smoke test for the A0 bearing-information utilities."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from envs.observability_active_perception import bearing_information, posterior_covariance


def main() -> None:
    target = np.zeros(2)
    left = bearing_information(np.asarray((-2.0, 0.0)), target, 0.2)
    below = bearing_information(np.asarray((0.0, -2.0)), target, 0.2)
    posterior = posterior_covariance(np.eye(2), [left, below])
    assert left.shape == (2, 2)
    assert np.all(np.linalg.eigvalsh(posterior) > 0)
    assert float(np.linalg.det(posterior)) < 1.0
    print("A0_OBSERVABILITY_GEOMETRY_SMOKE_PASS")


if __name__ == "__main__":
    main()
