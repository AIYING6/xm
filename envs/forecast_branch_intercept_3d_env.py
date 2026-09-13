"""3DOF interception with a public, time-limited branch forecast.

The target follows the same physical trajectory until ``branch_step``.  A
public dispatch advisory is available only at reset, while the sampled branch
is never inserted into actor observations before the manoeuvre starts.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from .uav_intercept_3d_env import UAVIntercept3DConfig, UAVIntercept3DEnv, wrap_angle


@dataclass
class ForecastBranchIntercept3DConfig(UAVIntercept3DConfig):
    forecast_right_probability: float = 0.5
    branch_step: int = 52
    branch_turn_radians: float = 0.62


class ForecastBranchIntercept3DEnv(UAVIntercept3DEnv):
    """A legal-history task substrate for forecast-contingent interception."""

    public_obs_dim = 2

    def __init__(self, config: ForecastBranchIntercept3DConfig | None = None):
        self.forecast_config = config or ForecastBranchIntercept3DConfig()
        probability = float(self.forecast_config.forecast_right_probability)
        if not 0.0 <= probability <= 1.0:
            raise ValueError("forecast_right_probability must lie in [0, 1]")
        if not 1 <= int(self.forecast_config.branch_step) < int(self.forecast_config.max_steps):
            raise ValueError("branch_step must be within the episode horizon")
        self.branch_right = False
        super().__init__(self.forecast_config)
        self.base_obs_dim = self.obs_dim
        self.base_share_obs_dim = UAVIntercept3DEnv._get_share_obs(self).shape[1]
        self.obs_dim = self.base_obs_dim + self.public_obs_dim
        self.share_obs_dim = self.base_share_obs_dim + self.public_obs_dim

    def reset(self):
        # ``self.rng`` exists before every reset invoked by the base class.
        self.branch_right = bool(self.rng.random() < self.forecast_config.forecast_right_probability)
        _, _, _ = super().reset()
        # Identical pre-branch target state across branch outcomes is part of
        # the information contract.  The target motion therefore starts from a
        # fixed heading and altitude rate after each reset.
        self.red_heading[0] = math.pi
        self.red_gamma[0] = 0.0
        self._update_sensing_and_comm()
        return self._get_obs(), self._get_share_obs(), self._get_graph_obs()

    def _public_forecast(self) -> np.ndarray:
        # The advisory is an initial public decision signal, not a persistent
        # input that a feed-forward policy can postpone using at later times.
        probability = (
            float(self.forecast_config.forecast_right_probability)
            if self.step_count == 0
            else 0.5
        )
        return np.asarray(
            [probability, float(self.step_count >= self.forecast_config.branch_step)], dtype=np.float32
        )

    def _get_obs(self) -> np.ndarray:
        # The parent allocates with ``self.obs_dim``.  Temporarily restore its
        # native width so legacy observation construction remains byte-for-byte
        # unchanged, then append the two public fields.
        extended_dim = self.obs_dim
        self.obs_dim = getattr(self, "base_obs_dim", 34)
        base = super()._get_obs()
        self.obs_dim = extended_dim
        return np.concatenate((base, np.tile(self._public_forecast(), (self.config.num_blue, 1))), axis=1)

    def _get_share_obs(self) -> np.ndarray:
        extended_dim = self.share_obs_dim
        self.share_obs_dim = getattr(self, "base_share_obs_dim", 47)
        base = super()._get_share_obs()
        self.share_obs_dim = extended_dim
        public = np.tile(self._public_forecast(), (self.config.num_blue, 1))
        return np.concatenate((base, public), axis=1).astype(np.float32)

    def _move_red(self) -> None:
        target = self.config.target_type
        if self.step_count < self.forecast_config.branch_step:
            desired_heading = math.pi
        else:
            sign = 1.0 if self.branch_right else -1.0
            desired_heading = wrap_angle(math.pi + sign * self.forecast_config.branch_turn_radians)
        turn = float(np.clip(
            (desired_heading - float(self.red_heading[0]) + math.pi) % (2.0 * math.pi) - math.pi,
            -target.max_turn_rate,
            target.max_turn_rate,
        ))
        self.red_heading[0] = wrap_angle(float(self.red_heading[0]) + turn * self.config.dt)
        velocity = np.asarray(
            [
                self.red_speed[0] * math.cos(float(self.red_heading[0])),
                self.red_speed[0] * math.sin(float(self.red_heading[0])),
                0.0,
            ],
            dtype=np.float32,
        )
        self.red_pos[0] += velocity * self.config.dt

    def step(self, actions):
        obs, share_obs, graph_obs, rewards, dones, info = super().step(actions)
        info = dict(info)
        info.update(
            {
                "forecast_right_probability_initial": float(self.forecast_config.forecast_right_probability),
                "physical_branch_active": float(self.step_count >= self.forecast_config.branch_step),
                "branch_right_telemetry": float(self.branch_right),
            }
        )
        return obs, share_obs, graph_obs, rewards, dones, info
