from __future__ import annotations

import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from algorithms.pscr_predictive_mappo import PSCRPredictiveMAPPO


def main() -> None:
    model = PSCRPredictiveMAPPO()
    obs = torch.zeros((2, 3, 27), dtype=torch.float32)
    # Common public state is identical; private positions differ.
    obs[:, :, 6] = 0.3; obs[:, :, 14] = 1.0; obs[:, :, 19] = 0.75; obs[:, :, 20] = -1.0
    obs[:, :, 0] = torch.tensor((0.1, -0.2, 0.3))
    masks = torch.ones((2, 3, 4), dtype=torch.float32); masks[:, :, 2] = 0.0
    plan = model.plan_distribution(obs, masks).probs
    assert torch.allclose(plan[:, 0], plan[:, 1]) and torch.allclose(plan[:, 1], plan[:, 2])
    assert torch.allclose(plan[..., 2], torch.zeros_like(plan[..., 2]))
    assert model.action_distribution(obs, masks).logits.shape == (2, 3, 4)
    assert model.opportunity_values(torch.zeros((2, 47))).shape == (2, 4)
    shuffled = PSCRPredictiveMAPPO(shuffle_forecast_context=True)
    assert torch.allclose(shuffled.public_context(obs)[..., 4], -model.public_context(obs)[..., 4])
    print("PSCR_PREDICTIVE_MAPPO_SMOKE_PASS")


if __name__ == "__main__":
    main()
