"""Capacity-matched MAPPO for the PSCR service-intent interface."""
from __future__ import annotations

from algorithms.m2_commitment_ppo import M2PlainMAPPO


class PSCRServiceMAPPO(M2PlainMAPPO):
    """Shared MAPPO baseline; no predictive opportunity mechanism is included."""

    def __init__(self) -> None:
        super().__init__(obs_dim=27, critic_dim=47, hidden_dim=128, action_dim=4)
