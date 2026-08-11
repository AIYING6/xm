"""Deterministic physical endpoint regression for v1.6R mission mode."""
from __future__ import annotations

import numpy as np

from envs.uav_intercept_3d_env import UAVIntercept3DConfig, UAVIntercept3DEnv


class AlwaysInWindowEnv(UAVIntercept3DEnv):
    def _update_sensing_and_comm(self):
        self.detected_by[:] = 0.0
        self.local_attack_window[:] = 0.0

    def _move_blue_guidance(self, guidance):
        return None

    def _move_red(self):
        return None

    def _in_attack_window(self, i, typ):
        return typ.role == 2

    def _has_collision(self):
        return False

    def _has_constraint_violation(self):
        return False


def main() -> int:
    env = AlwaysInWindowEnv(UAVIntercept3DConfig(seed=17071, v16r_mission_mode=True, attack_hold_steps=4, max_steps=8))
    env.reset()
    failures = []
    for step in range(3):
        _obs, _share, _graph, _rewards, dones, info = env.step_guidance(np.zeros((3, 2), dtype=np.float32))
        if bool(dones.all()) or float(info.get("success", 0.0)) > 0.5:
            failures.append("mission ended before four physical transitions")
    _obs, _share, _graph, _rewards, dones, info = env.step_guidance(np.zeros((3, 2), dtype=np.float32))
    if not bool(dones.all()) or float(info.get("success", 0.0)) < 0.5:
        failures.append("neutralization did not occur at four-step hold")
    print(f"checks=2, failed={len(failures)}")
    for failure in failures:
        print(f"FAIL: {failure}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
