from __future__ import annotations

from types import SimpleNamespace

import numpy as np

from scripts.audit_tatg_mappo_pilot_p2_runner import collect_checks
from scripts.run_tatg_mappo_pilot_single import ALL_ARMS, BASELINE_ARM, FROZEN_SEEDS, NUM_ENVS, ROLLOUT_STEPS, UPDATES, _build_snapshot, _temporal_gae, pilot_config, train_temporal_arm
from scripts.build_tatg_mappo_pilot_cloud_bundle import sources
from scripts.audit_tatg_mappo_pilot_p3_cloud_package import collect_checks as collect_package_checks


def test_tatg_pilot_runner_matches_the_frozen_static_contract() -> None:
    checks, details = collect_checks()
    assert all(checks.values())
    assert details["environment_steps_executed"] == 0
    assert details["ppo_updates_executed"] == 0
    assert details["evaluation_episodes_executed"] == 0
    assert len(ALL_ARMS) == 4
    for arm in ALL_ARMS:
        for seed in FROZEN_SEEDS:
            cfg = pilot_config(arm, seed, "unused-output-root")
            assert cfg.num_envs == NUM_ENVS == 4
            assert cfg.rollout_steps == ROLLOUT_STEPS == 64
            assert cfg.updates == UPDATES == 3907
            assert cfg.evaluation_enabled is False
            assert cfg.fixed_stratified_topology_sampler is True
            assert cfg.fixed_stratified_topology_sampler_seed == seed
            assert cfg.drtp_sampler_mode == "none"
            assert cfg.actor_gradient_mode == "standard"
    assert BASELINE_ARM in ALL_ARMS


def test_tatg_cloud_bundle_contains_only_the_frozen_training_interface() -> None:
    paths = {path.as_posix() for path in sources()}
    assert any(path.endswith("scripts/launch_tatg_mappo_pilot_autodl.sh") for path in paths)
    assert any(path.endswith("scripts/run_tatg_mappo_pilot_single.py") for path in paths)
    assert not any("results/" in path for path in paths)


def test_tatg_cloud_package_is_training_only() -> None:
    checks, details = collect_package_checks()
    assert all(checks.values())
    assert details["training_started"] is False
    assert details["evaluation_started"] is False


def test_tatg_snapshot_builder_uses_the_common_3d_num_agents_interface() -> None:
    cfg = pilot_config("tatg_cetm_utr", 75011, "unused-output-root")
    graph = {
        "node_feat": np.zeros((4, 4, 20), dtype=np.float32),
        "edge_feat": np.zeros((4, 4, 4, 17), dtype=np.float32),
        "role": np.zeros((4, 4), dtype=np.int64),
    }
    snapshot = _build_snapshot(
        graph,
        np.zeros((4, 3, 10), dtype=np.float32),
        np.zeros((4, 3, 12), dtype=np.float32),
        SimpleNamespace(action_dim=5, num_agents=3),
        cfg,
    )
    assert snapshot.num_agents == 3


def test_tatg_temporal_gae_broadcasts_episode_completion_over_agents() -> None:
    cfg = pilot_config("tatg_cetm_utr", 75011, "unused-output-root")
    batch = {
        "rewards": np.ones((2, 4, 3), dtype=np.float32),
        "values": np.zeros((2, 4, 3), dtype=np.float32),
        "dones": np.array([[False, True, False, False], [False, False, False, True]]),
    }
    advantages, returns = _temporal_gae(batch, np.zeros((4, 3), dtype=np.float32), cfg)
    assert advantages.shape == (2, 4, 3)
    assert returns.shape == (2, 4, 3)
    assert np.isfinite(advantages).all()
    assert np.isfinite(returns).all()


def test_tatg_temporal_arm_completes_one_cpu_update(tmp_path) -> None:
    output = train_temporal_arm("tatg_cetm_utr", 75011, tmp_path, updates=1)
    assert output.exists()
    assert (output / "actor_critic_latest.pt").is_file()
    assert '"status": "completed"' in (output / "run_manifest.json").read_text(encoding="utf-8")
    assert (output / "train_log.csv").read_text(encoding="utf-8").count("\n") == 2
