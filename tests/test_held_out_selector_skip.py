# Held-out (split=test) must NOT run the validation selector, even when a
# locked checkpoint has collision>0 (no collision-eligible candidate).
#
# This guards the FORMAL_HELD_OUT_TEST_PROTOCOL_V1_5 fix:
#   evaluate_3d_checkpoint_sweep.py / evaluate_happo_checkpoint_sweep.py /
#   evaluate_mappo_v1_5.py now skip select_checkpoints on split=test and write
#   an EMPTY selection CSV as a mechanical artifact (never used for decisions).
#
# The frozen validation path (split=validation) must still call the selector.
from __future__ import annotations

import csv
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
AB_ROOT = Path(r"D:/Code/Codex/ri_gmappo_uav_ablation_v1.5")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(AB_ROOT))

import scripts.evaluate_3d_checkpoint_sweep as sweep_mod  # noqa: E402
import scripts.evaluate_happo_checkpoint_sweep as happo_mod  # noqa: E402
import scripts.evaluate_mappo_v1_5 as mappo_mod  # noqa: E402

SCEN = "dropout030_delay2_relay_failure"


def run_main(module, monkeypatch, tmp_path, split, selector_calls):
    # Deterministic args (no dependency on pytest's sys.argv).
    args = type(
        "A", (),
        {
            "split": split, "episodes": 2, "base_seed": 745669,
            "out_dir": tmp_path, "seeds": (0,), "scenarios": (SCEN,),
            "resume": False, "max_new_evals": None,
            "selection_group": "suite", "selection_policy": "v1_5_wilson",
            "selection_metric": "legacy_recovery", "selection_success_weight": 100.0,
            "delayed_recovery_min_step": 80, "max_selection_collision_rate": 0.0,
            "selection_csv": None,
            "target_policy": "straight", "strict_target_sensing": True,
            "agent_target_info_bottleneck": True,
            "target_prior_position": (10_000.0, 0.0, 5_000.0),
            "graph_encoders": ("multi_relation",),
            "graph_relation_ablation": "none", "graph_message_ablation": "none",
            "graph_input_ablation": "none", "multi_relation_global_residual_weight": 1.0,
            "role_gate_prior_strength": 0.0, "role_pair_gate_fixed_value": 0.5,
            "max_target_message_age_steps": 80, "min_target_confidence": 0.2,
            "single_root": tmp_path / "s", "multi_root": tmp_path / "m",
            "no_graph_root": tmp_path / "n", "checkpoint_glob": "actor_critic_update_*.pt",
            "run_dir_template": "ppo_seed{seed}_1m", "checkpoint_updates": (100,),
            "device": "cpu", "allow_missing": True, "min_success_step": 0,
            "attack_hold_steps": 4,
        },
    )()
    monkeypatch.setattr(module, "parse_args", lambda: args)
    monkeypatch.setattr(module, "candidates_from_selection", lambda args: [])
    monkeypatch.setattr(
        module, "select_checkpoints",
        lambda args, rows: (selector_calls.append(True), [])[1],
    )
    module.main()


def assert_held_out_outputs(tmp_path, split):
    ep = tmp_path / f"{split}_episode_metrics.csv"
    su = tmp_path / f"{split}_checkpoint_summary.csv"
    sel = tmp_path / f"{split}_selected_checkpoints.csv"
    assert ep.exists(), ep
    assert su.exists(), su
    assert sel.exists(), sel
    with sel.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    assert rows == [], "selection CSV must be empty on held-out split"


# 1. sweep entrypoint: held-out must not call the selector
def test_sweep_test_split_skips_selector(monkeypatch, tmp_path) -> None:
    calls: list[bool] = []
    run_main(sweep_mod, monkeypatch, tmp_path, "test", calls)
    assert calls == [], "selector must not run on split=test"
    assert_held_out_outputs(tmp_path, "test")


# 2. sweep entrypoint: validation still runs the selector (frozen behavior)
def test_sweep_validation_still_runs_selector(monkeypatch, tmp_path) -> None:
    calls: list[bool] = []
    run_main(sweep_mod, monkeypatch, tmp_path, "validation", calls)
    assert calls == [True], "selector must still run on split=validation"


# 3. happo entrypoint: held-out must not call the selector
def test_happo_test_split_skips_selector(monkeypatch, tmp_path) -> None:
    calls: list[bool] = []
    run_main(happo_mod, monkeypatch, tmp_path, "test", calls)
    assert calls == [], "happo selector must not run on split=test"
    assert_held_out_outputs(tmp_path, "test")


# 4. happo entrypoint: validation still runs the selector
def test_happo_validation_still_runs_selector(monkeypatch, tmp_path) -> None:
    calls: list[bool] = []
    run_main(happo_mod, monkeypatch, tmp_path, "validation", calls)
    assert calls == [True], "happo selector must still run on split=validation"


# 5. mappo entrypoint: held-out must not call the selector
def test_mappo_test_split_skips_selector(monkeypatch, tmp_path) -> None:
    calls: list[bool] = []
    run_main(mappo_mod, monkeypatch, tmp_path, "test", calls)
    assert calls == [], "mappo selector must not run on split=test"
    assert_held_out_outputs(tmp_path, "test")


# 6. mappo entrypoint: validation still runs the selector
def test_mappo_validation_still_runs_selector(monkeypatch, tmp_path) -> None:
    calls: list[bool] = []
    run_main(mappo_mod, monkeypatch, tmp_path, "validation", calls)
    assert calls == [True], "mappo selector must still run on split=validation"


# 7. root-cause regression: a suite summary with collision>0 must raise on the
#    validation selector path (exactly why held-out must skip the selector)
def test_selector_still_raises_on_collision_for_validation() -> None:
    scen_keys = [
        "dropout030_delay2_relay_failure_early",
        "dropout030_delay2_relay_failure",
        "dropout030_delay2_relay_failure_delayed",
        "dropout030_delay2_relay_failure_late",
    ]
    summary = []
    for i, s in enumerate(scen_keys):
        # scenario 0 has a collision (collision_mean=0.01 > 0.0 gate);
        # the suite aggregation pools exposures across the 4 scenarios, so the
        # pooled collision remains > 0 and no candidate can be eligible.
        summary.append({
            "split": "validation", "scenario": s,
            "graph_encoder": "multi_relation", "graph_relation_ablation": "none",
            "graph_message_ablation": "none", "graph_input_ablation": "none",
            "train_seed": "2", "checkpoint_update": "977",
            "selection_score": "-1.0",
            "selection_metric": "legacy_recovery",
            "selection_success_weight": "100",
            "selection_policy": "v1_5_wilson",
            "failure_exposed_count": "50", "recovered_given_exposure_count": "40",
            "recovery_given_exposure": "0.8", "wilson_lower_95": "0.67",
            "estimate_unstable": "0",
            "collision_mean": "0.01" if i == 0 else "0",
            "success_mean": "0.8", "time_to_recovery_given_exposure": "60",
            "time_to_success": "70", "episodes": "100",
            "post_failure_chain_recovered_mean": "0.8",
            "post_failure_chain_recovery_steps_mean": "60",
        })
    args = type("A", (), {
        "selection_group": "suite", "selection_policy": "v1_5_wilson",
        "scenarios": tuple(scen_keys), "max_selection_collision_rate": 0.0,
        "selection_metric": "legacy_recovery", "selection_success_weight": 100.0,
        "delayed_recovery_min_step": 80,
    })()
    with pytest.raises(RuntimeError, match="no .*-eligible checkpoint"):
        sweep_mod.select_checkpoints(args, summary)
