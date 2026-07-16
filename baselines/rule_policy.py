from __future__ import annotations

import math
import numpy as np

from envs.uav_pursuit_env import ACTION_TABLE, angle_diff


def greedy_intercept_policy(env) -> np.ndarray:
    """A simple validation policy, not a research contribution."""
    actions = []
    for i in range(env.config.num_pursuers):
        target_idx = env._nearest_target(i)
        rel = env.t_pos[target_idx] - env.p_pos[i]
        desired = math.atan2(rel[1], rel[0])
        err = angle_diff(desired, env.p_heading[i])
        dist = np.linalg.norm(rel)

        turn = 0
        if err > 0.08:
            turn = 1
        elif err < -0.08:
            turn = -1

        accel = 1 if dist > env.config.capture_radius * 2.0 else -1

        cmd = np.array([turn, accel], dtype=np.float32)
        action = int(np.argmin(np.linalg.norm(ACTION_TABLE - cmd, axis=1)))
        actions.append(action)
    return np.asarray(actions, dtype=np.int64)

