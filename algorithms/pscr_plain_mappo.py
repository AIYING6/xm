"""Capacity-matched shared MAPPO baseline for PSCR-v2."""
from __future__ import annotations

from algorithms.m2_commitment_ppo import M2PlainMAPPO


class PSCRPlainMAPPO(M2PlainMAPPO):
    """No PSCR-specific mechanism: shared actor and centralized critic only."""

    def __init__(self) -> None:
        # Actor: position, speed/energy/connectivity/time, own attitude,
        # role and public service-request state.  Critic uses the matching
        # joint physical state, without unrevealed future-request truth.
        super().__init__(obs_dim=27, critic_dim=47, hidden_dim=128, action_dim=27)
