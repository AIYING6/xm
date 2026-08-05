"""Regression tests for the frozen v1.5 checkpoint-selection policy
(docs/V1_5_CHECKPOINT_SELECTOR_ADJUDICATION.md, tag formal-ablation-selector-v1.5.1).

Frozen rule:
  Eligibility : collision_rate == 0 AND failure_exposed_count > 0
  Rank        : (wilson95 lower bound up, success up, recovery-time down,
                 success-time down, checkpoint_update up)
  Grouping    : each (method, train_seed) independent
  N < 10      : flagged estimate_unstable (still selectable)
  Unexposed episodes are NOT counted as recovery failures.
  HAPPO       : identical selector (shared select_checkpoints)
"""
from __future__ import annotations

import math
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.evaluate_3d_checkpoint_sweep import (  # noqa: E402
    aggregate_suite_rows,
    select_checkpoints,
    wilson_lower_95,
)
import scripts.evaluate_happo_checkpoint_sweep as happo_sweep  # noqa: E402


def wilson_manual(k: int, n: int, z: float = 1.96) -> float:
    if n <= 0:
        return 0.0
    p = k / n
    denom = 1 + z * z / n
    center = p + z * z / (2 * n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (center - half) / denom


def make_row(
    seed: int,
    update: int,
    *,
    exposed: int = 20,
    recovered: int = 15,
    success: str = "0.8",
    rec_time: str = "10",
    succ_time: str = "50",
    collision: str = "0.0",
    scenario: str = "relay_failure",
) -> dict:
    wilson = wilson_lower_95(float(recovered), float(exposed))
    return {
        "split": "validation",
        "scenario": scenario,
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
        "post_failure_chain_recovered_mean": f"{recovered / exposed:.6g}" if exposed else "nan",
        "post_failure_chain_recovery_steps_mean": "10",
        "collision_mean": collision,
        "constraint_violation_mean": "0.0",
        "selection_score": "0",
        "selection_metric": "legacy_recovery",
        "selection_success_weight": "100",
        "selection_policy": "v1_5_wilson",
        "failure_exposed_count": str(exposed),
        "recovered_given_exposure_count": str(recovered),
        "recovery_given_exposure": f"{recovered / exposed:.6g}" if exposed else "nan",
        "wilson_lower_95": f"{wilson:.6g}",
        "estimate_unstable": "1" if exposed < 10 else "0",
        "time_to_recovery_given_exposure": rec_time,
        "time_to_success": succ_time,
    }


def make_args(group: str = "scenario", scenarios: list[str] | None = None) -> SimpleNamespace:
    return SimpleNamespace(
        split="validation",
        scenarios=scenarios or ["relay_failure"],
        selection_group=group,
        selection_metric="legacy_recovery",
        selection_success_weight=100.0,
        max_selection_collision_rate=0.0,
        delayed_recovery_min_step=80,
        graph_relation_ablation="none",
        graph_message_ablation="none",
        graph_input_ablation="none",
        selection_policy="v1_5_wilson",
    )


def select_best(rows: list[dict]) -> dict:
    selected = select_checkpoints(make_args("scenario"), rows)
    assert len(selected) == 1, f"expected 1 selected row, got {len(selected)}"
    return selected[0]


def test_wilson_lower_95_matches_formula() -> None:
    for k, n in ((15, 20), (50, 50), (1, 2), (0, 10), (10, 10)):
        assert wilson_lower_95(float(k), float(n)) == pytest.approx(wilson_manual(k, n))
    assert wilson_lower_95(0.0, 0.0) == 0.0


def test_wilson_penalises_small_n() -> None:
    # same point estimate, far larger n -> strictly higher lower bound
    a = wilson_lower_95(10.0, 20.0)   # 0.5, n=20
    b = wilson_lower_95(1.0, 2.0)     # 0.5, n=2
    assert a > b


def test_higher_wilson_wins() -> None:
    best = select_best(
        [
            make_row(0, 200, recovered=10, exposed=20),   # wilson ~0.30
            make_row(0, 300, recovered=19, exposed=20),   # wilson ~0.79
        ]
    )
    assert best["selected_checkpoint_update"] == "300"


def test_tie_wilson_higher_success_wins() -> None:
    r1 = make_row(0, 200, recovered=15, exposed=20, success="0.8")
    r2 = dict(make_row(0, 300, recovered=15, exposed=20, success="0.9"))
    best = select_best([r1, r2])
    assert best["selected_checkpoint_update"] == "300"


def test_tie_all_shorter_recovery_time_wins() -> None:
    r1 = make_row(0, 200, recovered=15, exposed=20, success="0.8", rec_time="30")
    r2 = dict(make_row(0, 300, recovered=15, exposed=20, success="0.8", rec_time="10"))
    best = select_best([r1, r2])
    assert best["selected_checkpoint_update"] == "300"


def test_tie_all_shorter_success_time_wins() -> None:
    r1 = make_row(0, 200, recovered=15, exposed=20, success="0.8", rec_time="10", succ_time="60")
    r2 = dict(make_row(0, 300, recovered=15, exposed=20, success="0.8", rec_time="10", succ_time="40"))
    best = select_best([r1, r2])
    assert best["selected_checkpoint_update"] == "300"


def test_complete_tie_larger_update_wins() -> None:
    r1 = make_row(0, 200, recovered=15, exposed=20)
    r2 = dict(make_row(0, 977, recovered=15, exposed=20))
    best = select_best([r1, r2])
    assert best["selected_checkpoint_update"] == "977"


def test_collision_above_zero_excluded() -> None:
    r1 = dict(make_row(0, 200, recovered=15, exposed=20, collision="0.05"))
    r2 = make_row(0, 300, recovered=10, exposed=20)
    best = select_best([r1, r2])
    assert best["selected_checkpoint_update"] == "300"


def test_no_failure_exposure_hard_fail() -> None:
    rows = [
        make_row(0, 200, exposed=0, recovered=0),
        make_row(0, 300, exposed=0, recovered=0),
    ]
    with pytest.raises(RuntimeError, match="no v1.5-eligible"):
        select_best(rows)


def test_unexposed_not_counted_as_failure() -> None:
    # Low unconditional recovery (many pre-failure successes) but perfect
    # conditional recovery must rank ABOVE a checkpoint with mediocre both.
    low_uncond = dict(make_row(0, 200, exposed=4, recovered=4, success="1.0", rec_time="5"))
    mediocre = dict(make_row(0, 300, exposed=40, recovered=20, success="0.8", rec_time="20"))
    best = select_best([low_uncond, mediocre])
    # 4/4 has wilson ~0.51; 20/40 has wilson ~0.37 -> low_uncond wins despite low n
    assert best["selected_checkpoint_update"] == "200"
    assert best["estimate_unstable"] == "1"


def test_estimate_unstable_flag() -> None:
    # small-n 100% (5/5) has wilson lower ~0.72; 38/40 (95%) has ~0.84 -> big wins
    r_small = make_row(0, 200, exposed=5, recovered=5)
    r_big = make_row(0, 300, exposed=40, recovered=38)
    assert select_best([r_small, r_big])["selected_checkpoint_update"] == "300"
    assert r_small["estimate_unstable"] == "1"
    assert r_big["estimate_unstable"] == "0"


def test_suite_pooled_exposure_counts() -> None:
    # 3 scenarios of the same checkpoint: pooled counts drive the Wilson bound.
    scs = ["relay_failure_early", "relay_failure", "relay_failure_delayed"]
    rows = [
        make_row(0, 200, exposed=5, recovered=5, scenario=scs[0]),
        make_row(0, 200, exposed=5, recovered=5, scenario=scs[1]),
        make_row(0, 200, exposed=5, recovered=5, scenario=scs[2]),
    ]
    suite = aggregate_suite_rows(make_args("suite", scenarios=scs), rows)
    assert len(suite) == 1
    assert suite[0]["failure_exposed_count"] == "15"
    assert suite[0]["recovered_given_exposure_count"] == "15"
    assert suite[0]["estimate_unstable"] == "0"
    assert float(suite[0]["wilson_lower_95"]) == pytest.approx(wilson_lower_95(15.0, 15.0))


def test_happo_uses_identical_selector() -> None:
    # HAPPO imports the exact same select_checkpoints function.
    assert happo_sweep.select_checkpoints is select_checkpoints
