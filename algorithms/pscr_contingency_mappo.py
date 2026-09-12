"""Capacity-matched plain MAPPO for the five-intent contingency interface."""
from __future__ import annotations

from algorithms.m2_commitment_ppo import M2PlainMAPPO


class PSCRContingencyMAPPO(M2PlainMAPPO):
    def __init__(self) -> None:
        super().__init__(obs_dim=27, critic_dim=47, hidden_dim=128, action_dim=5)
