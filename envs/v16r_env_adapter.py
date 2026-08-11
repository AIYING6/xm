"""Standard-interface adapter for the v1.6R legal graph and guidance API."""
from __future__ import annotations

from typing import Any

import numpy as np

from .uav_intercept_3d_env import UAVIntercept3DConfig, UAVIntercept3DEnv
from .v16r_legal_interface import LegalObservationInterface, stack_recipient_graphs


class V16RIntercept3DEnv:
    """Non-invasive v1.6R facade; legacy environment remains untouched."""

    def __init__(self, config: UAVIntercept3DConfig | None = None):
        self.base = UAVIntercept3DEnv(config or UAVIntercept3DConfig(strict_target_sensing=True, agent_target_info_bottleneck=True))
        self.legal = LegalObservationInterface(self.base)
        self.num_agents = self.base.num_agents
        self.obs_dim = self.base.obs_dim
        self.share_obs_dim = self.base.share_obs_dim
        self.action_dim = 2

    @property
    def config(self) -> UAVIntercept3DConfig:
        return self.base.config

    @property
    def done(self) -> bool:
        return self.base.done

    def reset(self):
        obs, share_obs, _legacy_graph = self.base.reset()
        return obs, share_obs, stack_recipient_graphs(self.legal)

    def step(self, actions: np.ndarray):
        obs, share_obs, _legacy_graph, rewards, dones, infos = self.base.step_guidance(actions)
        return obs, share_obs, stack_recipient_graphs(self.legal), rewards, dones, infos

    def legal_snapshot(self, recipient_id: int) -> dict[str, Any]:
        return self.legal.snapshot(recipient_id)

