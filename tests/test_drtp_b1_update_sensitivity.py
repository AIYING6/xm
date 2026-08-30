from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import pytest

from algorithms.ri_gmappo.rng_streams import RNGStreams
from algorithms.ri_gmappo.simple_ri_gmappo import RIGMAPPOConfig, train_ri_gmappo
from scripts.run_drtp_b1_update_sensitivity_branch import seed_tuple


def test_b1_default_is_inert() -> None:
    cfg = RIGMAPPOConfig()
    assert cfg.diagnostic_rng_branch_mode == "none"
    assert cfg.diagnostic_rng_branch_seed is None


def test_b1_branch_requires_runtime_checkpoint(tmp_path: Path) -> None:
    cfg = RIGMAPPOConfig(
        out_dir=str(tmp_path / "out"),
        diagnostic_rng_branch_mode="rollout",
        diagnostic_rng_branch_seed=1,
        rng_decomposition=True,
        rng_seed_tuple={
            "init_seed": 1, "env_seed": 2, "action_seed": 3,
            "minibatch_seed": 4, "topology_seed": 5, "eval_seed": 6,
        },
    )
    with pytest.raises(ValueError, match="require a frozen runtime checkpoint"):
        train_ri_gmappo(cfg)


def test_b1_rollout_and_minibatch_factorization() -> None:
    rollout0, _ = seed_tuple(3001, "rollout", 0)
    rollout1, _ = seed_tuple(3001, "rollout", 1)
    minibatch0, _ = seed_tuple(3001, "minibatch", 0)
    minibatch1, _ = seed_tuple(3001, "minibatch", 1)
    assert rollout0["minibatch_seed"] == rollout1["minibatch_seed"]
    assert any(rollout0[key] != rollout1[key] for key in ("env_seed", "action_seed", "topology_seed"))
    assert minibatch0["minibatch_seed"] != minibatch1["minibatch_seed"]
    assert all(minibatch0[key] == minibatch1[key] for key in ("env_seed", "action_seed", "topology_seed"))
    assert set(rollout0) == set(asdict(RNGStreams.from_master(1).seeds))
