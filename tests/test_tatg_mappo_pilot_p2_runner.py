from __future__ import annotations

from scripts.audit_tatg_mappo_pilot_p2_runner import collect_checks
from scripts.run_tatg_mappo_pilot_single import ALL_ARMS, BASELINE_ARM, FROZEN_SEEDS, NUM_ENVS, ROLLOUT_STEPS, UPDATES, pilot_config
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
