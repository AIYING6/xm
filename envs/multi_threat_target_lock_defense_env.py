"""G0-only v2 defense task: disruption interrupts a physical target-lock chain."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from envs.multi_threat_dual_capability_defense_env import (
    MultiThreatDualCapabilityDefenseConfig,
    MultiThreatDualCapabilityDefenseEnv,
)


@dataclass(frozen=True)
class MultiThreatTargetLockDefenseConfig(MultiThreatDualCapabilityDefenseConfig):
    red_target_lock_steps: int = 4
    # The target-lock variant isolates disruption as an interruption of the
    # attack prerequisite; it must not also inherit a speed-based advantage.
    suppressed_speed_scale: float = 1.0


class MultiThreatTargetLockDefenseEnv(MultiThreatDualCapabilityDefenseEnv):
    """Asset damage requires a continuous, non-disrupted red target lock.

    The lock is a task-side physical prerequisite for a precision strike, not
    a reward term.  A focused disruption beam invalidates it; the red attacker
    must reacquire the asset before it can strike.
    """

    def __init__(self, config: MultiThreatTargetLockDefenseConfig | None = None):
        self.lock_config = config or MultiThreatTargetLockDefenseConfig()
        super().__init__(self.lock_config)

    def reset(self):
        result = super().reset()
        self.red_target_lock_hold = np.zeros(2, dtype=np.int64)
        return result

    def _threat_breach(self, threat: int, asset_sign: int) -> bool:
        in_strike_geometry = bool(np.linalg.norm(self.red_pos[threat] - self._asset(asset_sign)) <= self.config.asset_strike_radius)
        disrupted = bool(self.base.step_count <= self.suppressed_until[threat])
        self.red_target_lock_hold[threat] = self.red_target_lock_hold[threat] + 1 if in_strike_geometry and not disrupted else 0
        return bool(self.red_target_lock_hold[threat] >= self.lock_config.red_target_lock_steps)
