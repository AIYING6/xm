"""Legal-information scripted controller feasibility check (no global target truth)."""
from __future__ import annotations

import math
import numpy as np

from envs.uav_intercept_3d_env import ROLE_ATTACKER, angle_diff, velocity_from_state, UAVIntercept3DConfig
from envs.v16r_env_adapter import V16RIntercept3DEnv


def main() -> int:
    successes = 0
    episodes = 8
    for seed in range(17130, 17130 + episodes):
        env = V16RIntercept3DEnv(UAVIntercept3DConfig(seed=seed, max_steps=180, v16r_mission_mode=True))
        env.reset()
        for _ in range(env.config.max_steps):
            actions = np.zeros((env.num_agents, 2), dtype=np.float32)
            for i, typ in enumerate(env.config.blue_types):
                evidence = env.legal.target_evidence(i)
                if not evidence.available:
                    continue
                rel = evidence.position - env.base.blue_pos[i]
                desired = math.atan2(float(rel[1]), float(rel[0]))
                actions[i, 0] = np.clip(angle_diff(desired, float(env.base.blue_heading[i])) / max(typ.max_turn_rate, 1e-6), -1.0, 1.0)
                desired_gamma = math.atan2(float(rel[2]), float(np.linalg.norm(rel[:2]) + 1e-6))
                actions[i, 1] = np.clip((desired_gamma - float(env.base.blue_gamma[i])) / max(typ.max_gamma, 1e-6), -1.0, 1.0)
            _obs, _share, _graph, _reward, dones, info = env.step(actions)
            if bool(dones.all()):
                successes += int(float(info.get("success", 0.0)) > 0.5)
                break
    print(f"episodes={episodes}, legal_scripted_neutralized={successes}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
