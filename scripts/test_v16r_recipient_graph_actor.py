"""Forward/gradient smoke for the transparent B2 graph baseline."""
from __future__ import annotations

import torch

from algorithms.mappo.recipient_graph_guidance_policy import RecipientGraphGuidanceActor


def main() -> int:
    torch.manual_seed(17069)
    actor = RecipientGraphGuidanceActor(obs_dim=34, hidden_dim=32)
    obs = torch.randn(3, 34)
    node = torch.randn(3, 4, 20)
    relation = torch.rand(3, 2, 4, 4)
    action, logp = actor(obs, node, relation)
    loss = -logp.mean()
    loss.backward()
    failures = []
    if action.shape != (3, 2) or not torch.isfinite(action).all():
        failures.append("graph actor action invalid")
    if not torch.isfinite(logp).all():
        failures.append("graph actor logp invalid")
    if any(p.grad is None or not torch.isfinite(p.grad).all() for p in actor.parameters()):
        failures.append("graph actor gradient invalid")
    print(f"checks=3, failed={len(failures)}")
    for failure in failures:
        print(f"FAIL: {failure}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
