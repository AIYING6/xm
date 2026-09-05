from __future__ import annotations

import json

from scripts.create_drtp_stabilization_development_v1_tape import payload
from scripts.run_drtp_stabilization_development_v1_single import ARMS, SEEDS, STEPS, UPDATES, training_config
from scripts import aggregate_drtp_stabilization_development_v1 as assessment


def test_v1_freeze_has_a_bounded_development_surface() -> None:
    freeze = json.loads(open("configs/drtp_stabilization_development_v1_freeze.json", encoding="utf-8").read())
    assert freeze["training"]["seeds"] == list(SEEDS)
    assert freeze["training"]["updates"] == UPDATES
    assert freeze["training"]["environment_steps_per_trajectory"] == STEPS
    assert freeze["anchored_egtr"]["alpha_candidates"] == [0.35, 0.55, 0.75]
    assert set(freeze["arms"]) == set(ARMS)
    assert freeze["development_policy"]["maximum_major_algorithm_versions"] == 2
    assert freeze["development_policy"]["automatic_v2_or_confirmation"] is False


def test_v1_arms_only_change_the_sampler_mechanism() -> None:
    common = None
    for arm, (mode, alpha) in ARMS.items():
        cfg = training_config(arm, SEEDS[0], "unused-output")
        assert cfg.drtp_sampler_mode == mode
        assert cfg.drtp_sampler_anchor_alpha == (1.0 if alpha is None else alpha)
        assert cfg.evaluation_enabled is False
        current = dict(cfg.__dict__)
        for key in ("drtp_sampler_mode", "drtp_sampler_anchor_alpha", "seed", "drtp_sampler_seed", "out_dir", "device"):
            current.pop(key)
        if common is None:
            common = current
        else:
            assert current == common, arm


def test_v1_tape_is_clean_and_training_inaccessible() -> None:
    tape = payload()
    assert tape["development_only"] is True
    assert tape["canonical"] is False
    assert tape["training_access"] == "forbidden"
    assert tape["episode_ids"] == list(range(760000, 760100))
    assert len(tape["conditions"]) == 5


def test_v1_launcher_chains_fixed_endpoint_evaluation_without_auto_v2() -> None:
    launcher = open("scripts/launch_drtp_stabilization_development_v1_autodl.sh", encoding="utf-8").read()
    assert "run_drtp_stabilization_development_v1_evaluation.py" in launcher
    assert "aggregate_drtp_stabilization_development_v1.py" in launcher
    assert "automatic_v2_or_confirmation\":false" in launcher


def test_v1_integrated_assessment_needs_a_balanced_case_to_be_promising() -> None:
    methods = {}
    for arm in ARMS:
        methods[arm] = {
            "min_J_perturbed": 0.0, "range_J_perturbed": 10.0,
            "median_J_perturbed": 5.0, "sampler_adapted_updates_total": 1,
            "sampler_uniform_l1_max": 0.1,
        }
    paired = []
    for candidate in assessment.CANDIDATES:
        for baseline in assessment.BASELINES:
            for seed in SEEDS:
                paired.append({
                    "candidate": candidate, "baseline": baseline, "train_seed": seed,
                    "delta_J_perturbed": -20.0, "delta_J_nominal": -20.0,
                    "delta_collision_perturbed": 0.3, "delta_timeout_perturbed": 0.3,
                })
    verdict, _, rows = assessment.development_verdict(methods, paired)
    assert verdict == "V1_WEAK"
    assert all(row["disposition"] == "weak" for row in rows)
