from __future__ import annotations

from scripts.audit_tatg_mappo_pilot_p2_runner import collect_checks
from scripts.run_tatg_mappo_pilot_single import ALL_ARMS, BASELINE_ARM, FROZEN_SEEDS, NUM_ENVS, ROLLOUT_STEPS, UPDATES, pilot_config


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
