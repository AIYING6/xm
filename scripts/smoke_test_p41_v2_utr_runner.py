"""Forward-path test for the P41 UTR runner; it does not perform optimization."""
from __future__ import annotations

import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from algorithms.p41_utr_ppo import P41UTRPPO
from envs.recoverable_service_chain_v2_env import P41_V2_SCENARIOS, RecoverableServiceChainV2Env


def main() -> None:
    env = RecoverableServiceChainV2Env(P41_V2_SCENARIOS[0])
    obs, critic, _ = env.reset()
    agent = P41UTRPPO()
    dist = agent.action_distribution(torch.as_tensor(obs[None], dtype=torch.float32))
    value = agent.value(torch.as_tensor(critic[None], dtype=torch.float32))
    assert dist.logits.shape == (1, 3, 3)
    assert value.shape == (1,)
    print("P41_V2_UTR_RUNNER_SMOKE_PASS")


if __name__ == "__main__":
    main()
