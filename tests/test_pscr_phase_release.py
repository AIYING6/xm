from __future__ import annotations

import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from algorithms.pscr_phase_release_mappo import PSCRPhaseReleaseMAPPO


def main() -> None:
    model = PSCRPhaseReleaseMAPPO(planning_mode="robust")
    obs = torch.zeros((2, 3, 27), dtype=torch.float32)
    obs[..., 20] = 1.0
    masks = torch.ones((2, 3, 5), dtype=torch.float32)
    pre = model.plan_distribution(obs, masks).probs
    obs[..., 22] = 1.0
    post = model.plan_distribution(obs, masks).probs
    assert pre.shape == post.shape == (2, 3, 5)
    assert torch.allclose(pre.sum(dim=-1), torch.ones((2, 3)))
    assert torch.allclose(post.sum(dim=-1), torch.ones((2, 3)))
    assert torch.allclose(post[:, 0], post[:, 1])
    print("PSCR_PHASE_RELEASE_SMOKE_PASS")


if __name__ == "__main__":
    main()
