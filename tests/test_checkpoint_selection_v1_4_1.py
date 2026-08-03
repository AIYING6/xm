"""Regression tests for the v1.4 Case-C checkpoint-selection adjudication
(eval-ops-v1.4.1).

Frozen rule (single weighted-score algorithm):
  Eligibility      : collision_rate <= 0.0 (higher -> excluded)
  Selection score  : 1000 * legacy_recovery + 100 * success_mean
                     - legacy_recovery_steps
  Ranking          : maximise selection_score
  Final tie-break  : larger checkpoint_update
  Grouping         : each train_seed independent
  Eligible         : 100, 200, ..., 900, 977
  HAPPO            : identical selector
  Test mode        : consumes only the selection CSV
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.evaluate_3d_checkpoint_sweep import (  # noqa: E402
    SELECTION_COLUMNS,
    candidates_from_selection,
    selection_score,
    select_checkpoints,
)
import scripts.evaluate_happo_checkpoint_sweep as happo_sweep  # noqa: E402
from scripts.generate_paper_commands import happo_sweep_command, method_sweep_command  # noqa: E402
from scripts.audit_checkpoint_selection_schema import audit_policy, audit_selection_csv  # noqa: E402

ELIGIBLE = [100, 200, 300, 400, 500, 600, 700, 800, 900, 977]


def make_row(
    seed: int,
    update: int,
    score: float,
    *,
    metric: str = "legacy_recovery",
    weight: str = "100",
    recovered: str = "0.5",
    steps: str = "10",
    success: str = "0.8",
    collision: str = "0.0",
) -> dict:
    """A summary-format row (summary_columns shape) for select_checkpoints."""
    return {
        "split": "validation",
        "scenario": "relay_failure",
        "graph_encoder": "multi_relation",
        "graph_relation_ablation": "none",
        "graph_message_ablation": "none",
        "graph_input_ablation": "none",
        "train_seed": str(seed),
        "checkpoint_update": str(update),
        "checkpoint": f"runs/multi_relation/bc_ppo_seed{seed}_1m/actor_critic_update_{update:04d}.pt",
        "strict_target_sensing": "True",
        "agent_target_info_bottleneck": "True",
        "target_prior_position": "10000;0;5000",
        "max_target_message_age_steps": "80",
        "min_target_confidence": "0.2",
        "episodes": "50",
        "success_mean": success,
        "post_failure_chain_recovered_mean": recovered,
        "post_failure_chain_recovered_after_loss_mean": "0.0",
        "pre_failure_chain_established_mean": "0.0",
        "pre_failure_chain_maintained_mean": "0.0",
        "pre_failure_chain_recovered_after_loss_mean": "0.0",
        "post_failure_chain_first_established_mean": "0.0",
        "post_failure_chain_never_established_mean": "0.0",
        "post_failure_fresh_info_recovered_mean": "0.1",
        "post_failure_fresh_info_acquired_without_prior_loss_mean": "0.0",
        "post_failure_fresh_info_first_established_mean": "0.0",
        "post_failure_fresh_direct_recovered_mean": "0.0",
        "post_failure_fresh_comm_recovered_mean": "0.0",
        "post_failure_post_delivered_old_info_recovered_mean": "0.0",
        "post_failure_stale_cache_recovered_mean": "0.0",
        "delayed_recovery_min_step": "80",
        "delayed_recovery_mean": "0.0",
        "post_failure_chain_recovery_steps_mean": steps,
        "post_failure_fresh_info_recovery_steps_mean": "inf",
        "delayed_recovery_steps_mean": "inf",
        "chain_closed_during_failure_rate_mean": "0.0",
        "tracking_during_failure_rate_mean": "0.0",
        "connectivity_during_failure_mean": "0.0",
        "episode_min_blue_red_distance_mean": "0.0",
        "episode_min_blue_blue_distance_mean": "0.0",
        "steps_mean": "0.0",
        "timeout_mean": "0.0",
        "collision_mean": collision,
        "constraint_violation_mean": "0.0",
        "selection_score": f"{score:.6g}",
        "selection_metric": metric,
        "selection_success_weight": weight,
    }


def make_selection_row(
    seed: int,
    update: int,
    score: float,
    *,
    metric: str = "legacy_recovery",
    weight: str = "100",
    checkpoint: str = "",
    sha: str = "",
) -> dict:
    """A selection-format row (selection_columns shape) for audit tests."""
    return {
        "split": "validation",
        "scenario": "relay_failure",
        "graph_encoder": "multi_relation",
        "graph_relation_ablation": "none",
        "graph_message_ablation": "none",
        "graph_input_ablation": "none",
        "train_seed": str(seed),
        "selected_checkpoint_update": str(update),
        "selected_checkpoint": checkpoint or f"runs/multi_relation/bc_ppo_seed{seed}_1m/actor_critic_update_{update:04d}.pt",
        "checkpoint_sha256": sha,
        "strict_target_sensing": "True",
        "agent_target_info_bottleneck": "True",
        "target_prior_position": "10000;0;5000",
        "max_target_message_age_steps": "80",
        "min_target_confidence": "0.2",
        "selection_score": f"{score:.6g}",
        "selection_metric": metric,
        "selection_success_weight": weight,
        "post_failure_chain_recovered_mean": "0.5",
        "post_failure_chain_recovered_after_loss_mean": "0.0",
        "pre_failure_chain_established_mean": "0.0",
        "pre_failure_chain_maintained_mean": "0.0",
        "pre_failure_chain_recovered_after_loss_mean": "0.0",
        "post_failure_chain_first_established_mean": "0.0",
        "post_failure_chain_never_established_mean": "0.0",
        "post_failure_fresh_info_recovered_mean": "0.1",
        "post_failure_fresh_info_acquired_without_prior_loss_mean": "0.0",
        "post_failure_fresh_info_first_established_mean": "0.0",
        "post_failure_fresh_direct_recovered_mean": "0.0",
        "post_failure_fresh_comm_recovered_mean": "0.0",
        "post_failure_post_delivered_old_info_recovered_mean": "0.0",
        "post_failure_stale_cache_recovered_mean": "0.0",
        "delayed_recovery_min_step": "80",
        "delayed_recovery_mean": "0.0",
        "post_failure_chain_recovery_steps_mean": "10",
        "post_failure_fresh_info_recovery_steps_mean": "inf",
        "delayed_recovery_steps_mean": "inf",
        "success_mean": "0.8",
        "collision_mean": "0.0",
        "episode_min_blue_red_distance_mean": "0.0",
        "episode_min_blue_blue_distance_mean": "0.0",
        "constraint_violation_mean": "0.0",
        "episodes": "50",
    }


def make_args(group: str = "scenario") -> SimpleNamespace:
    return SimpleNamespace(
        split="validation",
        scenarios=["relay_failure"],
        selection_group=group,
        selection_metric="legacy_recovery",
        selection_success_weight=100.0,
        max_selection_collision_rate=0.0,
        delayed_recovery_min_step=80,
        graph_relation_ablation="none",
        graph_message_ablation="none",
        graph_input_ablation="none",
    )


def select_best(rows: list[dict]) -> dict:
    selected = select_checkpoints(make_args("scenario"), rows)
    assert len(selected) == 1
    return selected[0]


def _write_selection_csv(tmp_path: Path, rows: list[dict]) -> Path:
    path = tmp_path / "validation_selected_checkpoints.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(SELECTION_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)
    return path


# ---- selector: weighted score ----

def test_higher_score_wins() -> None:
    best = select_best([make_row(0, 200, 700.0), make_row(0, 400, 600.0)])
    assert best["selected_checkpoint_update"] == "200"


def test_tie_prefers_later_update() -> None:
    best = select_best([make_row(0, 200, 600.0), make_row(0, 900, 600.0)])
    assert best["selected_checkpoint_update"] == "900"


def test_0977_can_win() -> None:
    best = select_best([make_row(0, 800, 600.0), make_row(0, 977, 700.0)])
    assert best["selected_checkpoint_update"] == "977"


def test_collision_above_threshold_excluded() -> None:
    assert selection_score(0.5, 10.0, 0.8, 0.05, 0.0, 100.0) == -1_000_000_000.0
    assert selection_score(0.5, 10.0, 0.8, 0.0, 0.0, 100.0) != -1_000_000_000.0
    best = select_best([make_row(0, 200, 700.0), make_row(0, 400, -1_000_000_000.0)])
    assert best["selected_checkpoint_update"] == "200"


def test_all_candidates_collide_hard_fail() -> None:
    # Every eligible checkpoint violates the collision gate: the selector must
    # raise instead of silently picking one of the -1e9 rows.
    rows = [
        make_row(0, 900, -1_000_000_000.0, collision="0.05"),
        make_row(0, 977, -1_000_000_000.0, collision="0.08"),
    ]
    with pytest.raises(RuntimeError, match="no collision-eligible checkpoint"):
        select_checkpoints(make_args("scenario"), rows)


def test_all_candidates_collide_hard_fail_suite() -> None:
    rows = [
        make_row(0, 900, -1_000_000_000.0, collision="0.05"),
        make_row(0, 977, -1_000_000_000.0, collision="0.08"),
    ]
    with pytest.raises(RuntimeError, match="no collision-eligible checkpoint"):
        select_checkpoints(make_args("suite"), rows)


def test_success_weight_is_100() -> None:
    assert selection_score(0.5, 10.0, 0.8, 0.0, 0.0, 100.0) == pytest.approx(570.0)
    # with weight 0 the score would be 490, proving 100 is actually applied
    assert selection_score(0.5, 10.0, 0.8, 0.0, 0.0, 0.0) == pytest.approx(490.0)


def test_score_not_lexicographic_recovery_first() -> None:
    # Higher recovery but lower score must lose; ranking is by selection_score.
    rows = [
        make_row(0, 200, 600.0, recovered="0.90", steps="300", success="0.0"),
        make_row(0, 400, 700.0, recovered="0.50", steps="10", success="0.8"),
    ]
    best = select_best(rows)
    assert best["selected_checkpoint_update"] == "400"


def test_each_train_seed_independent() -> None:
    rows = [
        make_row(0, 200, 600.0),
        make_row(0, 900, 500.0),
        make_row(1, 200, 300.0),
        make_row(1, 900, 800.0),
    ]
    selected = select_checkpoints(make_args("scenario"), rows)
    by_seed = {int(r["train_seed"]): r for r in selected}
    assert set(by_seed) == {0, 1}
    assert by_seed[0]["selected_checkpoint_update"] == "200"
    assert by_seed[1]["selected_checkpoint_update"] == "900"


def test_happo_uses_same_selector() -> None:
    assert happo_sweep.select_checkpoints is select_checkpoints


# ---- generator: explicit args ----

def test_generator_emits_explicit_selection_args() -> None:
    main_cfg = {
        "scenario": {
            "target_policy": "straight",
            "strict_target_sensing": True,
            "agent_target_info_bottleneck": True,
            "target_prior_position": [10000.0, 0.0, 5000.0],
            "max_target_message_age_steps": 80,
            "min_target_confidence": 0.2,
        },
        "seeds": {
            "validation_base_seed": 120000,
            "test_base_seed": 900000,
            "validation_episodes_per_seed": 50,
            "test_episodes_per_seed": 100,
        },
    }
    out_root = Path("results/paper_config_runs/dummy")
    commands = [
        method_sweep_command(
            main_cfg=main_cfg,
            method_name="ea_rg_mappo_gate_prior",
            method_cfg={"graph_encoder": "multi_relation"},
            mode="formal_bstar",
            split="validation",
            seeds=[0, 1, 2],
            device="cuda",
            out_root=out_root,
        ),
        happo_sweep_command(
            main_cfg=main_cfg,
            method_name="happo",
            mode="formal_bstar",
            split="validation",
            seeds=[0, 1, 2],
            device="cuda",
            out_root=out_root,
        ),
    ]
    for cmd in commands:
        assert cmd[cmd.index("--selection-metric") + 1] == "legacy_recovery"
        assert cmd[cmd.index("--selection-success-weight") + 1] == "100"
        assert cmd[cmd.index("--max-selection-collision-rate") + 1] == "0.0"


# ---- audit: policy and row checks ----

def test_audit_rejects_wrong_metric(tmp_path: Path) -> None:
    path = _write_selection_csv(tmp_path, [make_selection_row(0, 977, 700.0, metric="fresh_info_recovery")])
    with pytest.raises(SystemExit):
        audit_selection_csv(path, tmp_path, {"selection_policy": {"eligible_snapshots": ELIGIBLE}})


def test_audit_rejects_wrong_weight(tmp_path: Path) -> None:
    path = _write_selection_csv(tmp_path, [make_selection_row(0, 977, 700.0, weight="0.0")])
    with pytest.raises(SystemExit):
        audit_selection_csv(path, tmp_path, {"selection_policy": {"eligible_snapshots": ELIGIBLE}})


def test_audit_rejects_non_eligible_update(tmp_path: Path) -> None:
    path = _write_selection_csv(tmp_path, [make_selection_row(0, 150, 700.0)])
    with pytest.raises(SystemExit):
        audit_selection_csv(path, tmp_path, {"selection_policy": {"eligible_snapshots": ELIGIBLE}})


def test_audit_rejects_duplicate_group(tmp_path: Path) -> None:
    import hashlib

    # create real dummy checkpoint files so audit reaches the uniqueness check
    for upd in (200, 900):
        cp = tmp_path / "runs" / "multi_relation" / "bc_ppo_seed0_1m" / f"actor_critic_update_{upd:04d}.pt"
        cp.parent.mkdir(parents=True, exist_ok=True)
        cp.write_bytes(b"x")
    sha = hashlib.sha256(b"x").hexdigest().upper()
    rows = [
        make_selection_row(0, 200, 600.0, checkpoint="runs/multi_relation/bc_ppo_seed0_1m/actor_critic_update_0200.pt", sha=sha),
        make_selection_row(0, 900, 700.0, checkpoint="runs/multi_relation/bc_ppo_seed0_1m/actor_critic_update_0900.pt", sha=sha),
    ]
    path = _write_selection_csv(tmp_path, rows)
    with pytest.raises(SystemExit, match="duplicate selection"):
        audit_selection_csv(path, tmp_path, {"selection_policy": {"eligible_snapshots": ELIGIBLE}})


def test_audit_policy_frozen_values_pass() -> None:
    schema = {
        "selection_policy": {
            "selection_metric": "legacy_recovery",
            "selection_success_weight": 100,
            "tie_breaker": "larger checkpoint_update",
            "collision_threshold": 0.0,
            "collision_above_threshold_is_ineligible": True,
            "selection_per_train_seed": True,
            "happo_same_rule": True,
            "checkpoint_sha256_recorded": True,
            "test_must_use_selection_csv": True,
            "validation_must_not_use_test_results": True,
            "eligible_snapshots": ELIGIBLE,
            "score": "legacy_recovery: 1000 * post_failure_chain_recovered_mean + 100 * success_mean - post_failure_chain_recovery_steps_mean",
            "ranking": "maximise selection_score; on an exact tie prefer larger checkpoint_update",
        }
    }
    audit_policy(schema)


def test_audit_policy_rejects_bad_tiebreak() -> None:
    schema = {
        "selection_policy": {
            "selection_metric": "legacy_recovery",
            "selection_success_weight": 100,
            "tie_breaker": "smaller checkpoint_update",
            "collision_threshold": 0.0,
            "collision_above_threshold_is_ineligible": True,
            "selection_per_train_seed": True,
            "happo_same_rule": True,
            "checkpoint_sha256_recorded": True,
            "test_must_use_selection_csv": True,
            "validation_must_not_use_test_results": True,
            "eligible_snapshots": ELIGIBLE,
            "score": "legacy_recovery: 1000 * post_failure_chain_recovered_mean + 100 * success_mean - post_failure_chain_recovery_steps_mean",
            "ranking": "maximise selection_score; on an exact tie prefer larger checkpoint_update",
        }
    }
    with pytest.raises(SystemExit):
        audit_policy(schema)


# ---- test mode consumes only selection CSV ----

def test_test_only_consumes_selection_csv(tmp_path: Path, monkeypatch) -> None:
    import scripts.evaluate_3d_checkpoint_sweep as sweep_mod

    monkeypatch.setattr(sweep_mod, "ROOT", tmp_path)
    ckpt = tmp_path / "runs" / "multi_relation" / "bc_ppo_seed0_1m" / "actor_critic_update_0977.pt"
    ckpt.parent.mkdir(parents=True, exist_ok=True)
    ckpt.write_bytes(b"dummy")
    row = make_selection_row(0, 977, 700.0, checkpoint=ckpt.relative_to(tmp_path).as_posix())
    path = _write_selection_csv(tmp_path, [row])
    args = SimpleNamespace(selection_csv=path, graph_encoders=["multi_relation"], seeds=[0], allow_missing=False)
    candidates = candidates_from_selection(args)
    assert len(candidates) == 1
    assert candidates[0].update == 977
    assert candidates[0].checkpoint == ckpt
