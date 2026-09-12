from __future__ import annotations

import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from algorithms.pscr_reliability_commitment_mappo import PSCRReliabilityCommitmentMAPPO


def main() -> None:
    obs = torch.zeros((2, 3, 27), dtype=torch.float32)
    critic = torch.zeros((2, 47), dtype=torch.float32)
    masks = torch.ones((2, 3, 5), dtype=torch.float32)
    masks[..., 2] = 0.0
    for mode in ("full", "phase_control", "permuted_reliability"):
        agent = PSCRReliabilityCommitmentMAPPO(mode=mode)
        distribution = agent.action_distribution(obs, masks)
        assert distribution.probs.shape == (2, 3, 5)
        assert torch.all(distribution.probs[..., 2] == 0.0)
        assert agent.commitment_target_distribution(critic, masks).shape == (2, 3, 5)
    print("PSCR_RC_MAPPO_SMOKE_PASS")


if __name__ == "__main__":
    main()
