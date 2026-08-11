"""R1 regression tests for the additive continuous guidance environment API."""
from __future__ import annotations

import numpy as np

from envs.uav_intercept_3d_env import ACTION3D_TABLE, UAVIntercept3DConfig, UAVIntercept3DEnv


def main() -> int:
    cfg = UAVIntercept3DConfig(seed=17062)
    legacy = UAVIntercept3DEnv(cfg)
    continuous = UAVIntercept3DEnv(UAVIntercept3DConfig(seed=17062))
    failures: list[str] = []
    zero_index = int(np.flatnonzero(np.all(ACTION3D_TABLE == 0.0, axis=1))[0])
    legacy.step(np.full(cfg.num_blue, zero_index, dtype=np.int64))
    continuous.step_guidance(np.zeros((cfg.num_blue, 2), dtype=np.float32))
    if not np.all(continuous.blue_speed >= np.asarray([185.0, 175.0, 205.0], dtype=np.float32)):
        failures.append("fixed controller did not provide deterministic closure acceleration")
    if np.allclose(legacy.blue_pos, continuous.blue_pos, atol=1e-5):
        failures.append("continuous path unexpectedly aliases legacy discrete dynamics")
    try:
        continuous.step_guidance(np.zeros((cfg.num_blue, 3), dtype=np.float32))
        failures.append("wrong guidance shape was accepted")
    except ValueError:
        pass
    continuous.reset()
    try:
        continuous.step_guidance(np.full((cfg.num_blue, 2), np.nan, dtype=np.float32))
        failures.append("NaN guidance was accepted")
    except ValueError:
        pass
    continuous.reset()
    continuous.step_guidance(np.full((cfg.num_blue, 2), 4.0, dtype=np.float32))
    if not np.isfinite(continuous.blue_pos).all():
        failures.append("clipped guidance produced non-finite state")
    print(f"checks=5, failed={len(failures)}")
    for failure in failures:
        print(f"FAIL: {failure}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
