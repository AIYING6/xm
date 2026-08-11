"""Recipient-specific legal information interface for v1.6R.

This module deliberately sits between the environment and actor/graph code.  It
does not expose raw environment state; target evidence is emitted only when the
recipient has current sensing or a delivered, non-expired cache entry.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from .uav_intercept_3d_env import (
    ROLE_TARGET,
    UAVIntercept3DEnv,
    velocity_from_state,
)


@dataclass(frozen=True)
class LegalTargetEvidence:
    available: bool
    position: np.ndarray
    velocity: np.ndarray
    age_steps: float
    confidence: float
    source: int
    path: tuple[int, ...]
    kind: str


class LegalObservationInterface:
    """Read-only recipient-specific view used by v1.6R actors."""

    def __init__(self, env: UAVIntercept3DEnv):
        self.env = env

    def target_evidence(self, recipient_id: int) -> LegalTargetEvidence:
        env = self.env
        cfg = env.config
        if not (0 <= recipient_id < cfg.num_blue):
            raise IndexError(f"invalid recipient_id={recipient_id}")

        # Local sensing has priority over communicated evidence.
        if float(env.detected_by[recipient_id]) > 0.5:
            vel = velocity_from_state(
                env.red_speed[0], env.red_heading[0], env.red_gamma[0]
            ).astype(np.float32)
            return LegalTargetEvidence(
                True,
                env.red_pos[0].copy(),
                vel,
                0.0,
                1.0,
                recipient_id,
                (recipient_id,),
                "local_sensing",
            )

        # No global fallback is permitted.  In particular, do not call
        # _estimated_target_state() or read last_detected_target_* here.
        if bool(env._has_fresh_target_cache(recipient_id)):
            pos = env.target_cache_pos[recipient_id].copy()
            vel = env.target_cache_vel[recipient_id].copy()
            return LegalTargetEvidence(
                True,
                pos,
                vel,
                float(env._local_target_cache_age(recipient_id)),
                float(env._local_target_cache_confidence(recipient_id)),
                int(env.target_cache_source[recipient_id]),
                tuple(env.target_cache_path[recipient_id]),
                "delivered_cache",
            )

        return LegalTargetEvidence(
            False,
            np.zeros(3, dtype=np.float32),
            np.zeros(3, dtype=np.float32),
            float("inf"),
            0.0,
            -1,
            (),
            "none",
        )

    def snapshot(self, recipient_id: int) -> dict[str, Any]:
        """Return only legal evidence plus recipient-local state metadata."""
        env = self.env
        evidence = self.target_evidence(recipient_id)
        typ = env.config.blue_types[recipient_id]
        return {
            "recipient_id": int(recipient_id),
            "self_state": {
                "position": env.blue_pos[recipient_id].copy(),
                "speed": float(env.blue_speed[recipient_id]),
                "heading": float(env.blue_heading[recipient_id]),
                "gamma": float(env.blue_gamma[recipient_id]),
                "energy": float(env.blue_energy[recipient_id]),
                "role": int(typ.role),
            },
            "target_evidence": evidence,
            "inbound_connectivity": float(env._local_inbound_connectivity(recipient_id)),
            "message_age": float(env._local_inbound_message_age(recipient_id)),
        }

    def recipient_graph(self, recipient_id: int) -> dict[str, np.ndarray]:
        """Build a legal graph for one recipient; no global target node leakage."""
        env = self.env
        cfg = env.config
        n_blue = cfg.num_blue
        n = n_blue + cfg.num_red
        evidence = self.target_evidence(recipient_id)
        node = np.zeros((n, 20), dtype=np.float32)
        edge = np.zeros((n, n, 17), dtype=np.float32)
        relation = np.zeros((2, n, n), dtype=np.float32)  # sensing, communication
        roles = [int(t.role) for t in cfg.blue_types] + [ROLE_TARGET]
        positions = np.vstack([env.blue_pos, evidence.position[None, :]])
        velocities = [
            velocity_from_state(env.blue_speed[i], env.blue_heading[i], env.blue_gamma[i])
            for i in range(n_blue)
        ] + [evidence.velocity]
        for i in range(n):
            p = positions[i]
            v = velocities[i]
            speed = float(np.linalg.norm(v))
            max_speed = cfg.target_type.max_speed if i == n_blue else cfg.blue_types[i].max_speed
            node[i, :3] = np.asarray([p[0] / cfg.world_radius, p[1] / cfg.world_radius, p[2] / cfg.max_altitude])
            node[i, 3] = speed / max_speed
            if speed > 1e-6:
                node[i, 4] = float(np.sin(np.arctan2(v[1], v[0])))
                node[i, 5] = float(np.cos(np.arctan2(v[1], v[0])))
            node[i, 11 + min(roles[i], 4)] = 1.0
            node[i, 16] = float(evidence.available and i == n_blue)
            node[i, 19] = float(i < n_blue)

        # Self-loop only plus legal evidence relations.  A communication edge
        # exists only when the recipient's cache provenance names that sender.
        for i in range(n):
            edge[i, i, 15] = 1.0
        if evidence.available and n_blue >= 1:
            target = n_blue
            if evidence.kind == "local_sensing":
                relation[0, recipient_id, target] = 1.0
            elif evidence.source >= 0:
                relation[1, recipient_id, evidence.source] = 1.0
                edge[recipient_id, evidence.source, 14] = min(1.0, evidence.age_steps / max(1, cfg.max_target_message_age_steps))
                edge[recipient_id, evidence.source, 16] = float(evidence.confidence)
                relation[1, evidence.source, target] = 1.0
        return {"node": node, "edge": edge, "relation_adj": relation}


def stack_recipient_graphs(interface: LegalObservationInterface) -> dict[str, np.ndarray]:
    """Stack one legal graph per recipient for a future v1.6R collector.

    The leading dimension is the recipient dimension.  This intentionally does
    not imitate the legacy shared graph shape, so accidental information
    broadcasting fails loudly at the adapter boundary.
    """
    graphs = [interface.recipient_graph(i) for i in range(interface.env.num_agents)]
    return {
        key: np.stack([graph[key] for graph in graphs], axis=0)
        for key in ("node", "edge", "relation_adj")
    }
