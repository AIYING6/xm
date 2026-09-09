"""Zero-training shadow adapter connecting active diagnosis to 3DOF dynamics.

The adapter is not a trainable environment.  It freezes a matched initial
state in which range loss and a hard relay failure are actor-observation
equivalent, then executes one legal 12-step physical handshake manoeuvre.
"""

from __future__ import annotations

from copy import deepcopy

import numpy as np

from envs.active_diagnosis_semantic_env import (
    FAILURE_HYPOTHESES,
    HARD_RELAY_FAILURE,
    RECOVERABLE_RANGE_LOSS,
)
from envs.uav_intercept_3d_env import ACTION3D_TABLE, UAVIntercept3DConfig, UAVIntercept3DEnv


class ActiveDiagnosisUAVShadowEnv:
    runtime_format = "active_diagnosis_uav_shadow_state_v1"
    relay_id = 1
    attacker_id = 2
    probe_duration_steps = 12

    def __init__(self, hypothesis: str, seed: int) -> None:
        if hypothesis not in FAILURE_HYPOTHESES:
            raise ValueError(f"unknown hypothesis: {hypothesis}")
        self.hypothesis = hypothesis
        self.seed = int(seed)
        failed_agent = self.relay_id if hypothesis == HARD_RELAY_FAILURE else -1
        config = UAVIntercept3DConfig(
            business_grounded_geometry=True,
            communication_range_scale=0.5,
            communication_dropout_prob=0.0,
            failed_blue_agent=failed_agent,
            node_failure_start_step=0,
            node_failure_duration_steps=260,
            seed=self.seed,
        )
        self.base = UAVIntercept3DEnv(config)
        neutral = np.flatnonzero(np.all(ACTION3D_TABLE == 0.0, axis=1))
        if neutral.size != 1:
            raise AssertionError("3DOF action table must contain one neutral control")
        self.neutral_action = int(neutral[0])
        self.probe_count = 0
        self.reset()

    def reset(self) -> tuple[np.ndarray, np.ndarray, dict[str, np.ndarray]]:
        self.base.seed(self.seed)
        self.base.reset()
        # At scale 0.5, both relay links are initially out of range.  The relay
        # points toward the attacker and can enter handshake range in 12 steps.
        self.base.blue_pos = np.asarray(
            [[-2_000.0, -5_500.0, 5_000.0], [-2_000.0, 0.0, 5_000.0], [-2_000.0, 5_500.0, 5_000.0]],
            dtype=np.float32,
        )
        self.base.blue_heading = np.asarray([0.0, np.pi / 2.0, 0.0], dtype=np.float32)
        self.base.blue_gamma[:] = 0.0
        self.base._update_sensing_and_comm()
        self.probe_count = 0
        return self.observation()

    def observation(self) -> tuple[np.ndarray, np.ndarray, dict[str, np.ndarray]]:
        return self.base._get_obs(), self.base._get_share_obs(), self.base._get_graph_obs()

    def execute_handshake_probe(self) -> dict:
        if self.probe_count >= 1:
            raise RuntimeError("P1C permits exactly one handshake probe")
        if self.base.done:
            raise RuntimeError("base episode terminated before probe")
        self.probe_count += 1
        before_energy = self.base.blue_energy.copy()
        infos = []
        action = np.full(self.base.config.num_blue, self.neutral_action, dtype=np.int64)
        for _ in range(self.probe_duration_steps):
            _, _, _, _, _, info = self.base.step(action)
            infos.append(info)
            if self.base.done:
                raise RuntimeError("base episode terminated during frozen probe")
        relay_to_attacker = bool(self.base.comm_adj[self.attacker_id, self.relay_id] > 0.5)
        attacker_to_relay = bool(self.base.comm_adj[self.relay_id, self.attacker_id] > 0.5)
        return {
            "ack": relay_to_attacker and attacker_to_relay,
            "elapsed_steps": self.probe_duration_steps,
            "energy_cost": (before_energy - self.base.blue_energy).tolist(),
            "collision": any(float(info["collision"]) > 0.0 for info in infos),
            "constraint_violation": any(float(info["constraint_violation"]) > 0.0 for info in infos),
            "observation": self.observation(),
        }

    def state_dict(self) -> dict:
        return {
            "format": self.runtime_format,
            "hypothesis": self.hypothesis,
            "seed": self.seed,
            "probe_count": self.probe_count,
            "base": self.base.runtime_state_dict(),
        }

    def load_state_dict(self, state: dict) -> None:
        if state.get("format") != self.runtime_format:
            raise ValueError("incompatible shadow state")
        if state.get("hypothesis") != self.hypothesis or int(state.get("seed")) != self.seed:
            raise ValueError("shadow state belongs to another experiment")
        self.probe_count = int(state["probe_count"])
        self.base.load_runtime_state_dict(deepcopy(state["base"]))


def observations_equal(
    first: tuple[np.ndarray, np.ndarray, dict[str, np.ndarray]],
    second: tuple[np.ndarray, np.ndarray, dict[str, np.ndarray]],
) -> bool:
    obs_a, share_a, graph_a = first
    obs_b, share_b, graph_b = second
    if not np.array_equal(obs_a, obs_b) or not np.array_equal(share_a, share_b):
        return False
    return graph_a.keys() == graph_b.keys() and all(
        np.array_equal(graph_a[key], graph_b[key]) for key in graph_a
    )

