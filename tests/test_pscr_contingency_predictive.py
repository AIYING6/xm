from __future__ import annotations

import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from algorithms.pscr_contingency_predictive_mappo import PSCRContingencyPredictiveMAPPO


def main() -> None:
    obs = torch.zeros((2, 3, 27), dtype=torch.float32)
    obs[..., 20] = 1.0
    masks = torch.ones((2, 3, 5), dtype=torch.float32)
    for mode in ("direct", "robust", "masked"):
        model = PSCRContingencyPredictiveMAPPO(planning_mode=mode)
        distribution = model.action_distribution(obs, masks)
        assert distribution.logits.shape == (2, 3, 5)
        assert torch.allclose(distribution.probs.sum(dim=-1), torch.ones((2, 3)))
    robust = PSCRContingencyPredictiveMAPPO(planning_mode="robust")
    assert torch.allclose(robust.plan_distribution(obs, masks).probs[:, 0], robust.plan_distribution(obs, masks).probs[:, 1])
    print("PSCR_CONTINGENCY_PREDICTIVE_SMOKE_PASS")


if __name__ == "__main__":
    main()
