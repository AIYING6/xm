"""Fixed-capacity, non-privileged MAPPO baseline for the frozen P8 task."""
from __future__ import annotations

from algorithms.m2_commitment_ppo import M2PlainMAPPO


class PSCRP8PlainMAPPO(M2PlainMAPPO):
    """Shared actor and centralized critic; no P8-specific mechanism."""

    def __init__(self) -> None:
        super().__init__(obs_dim=33, critic_dim=50, hidden_dim=128, action_dim=5)
