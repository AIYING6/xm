from __future__ import annotations

import math
from pathlib import Path

from algorithms.ri_gmappo.drtp_topology_sampler import (
    ALL_GROUPS,
    FAILURE_GROUPS,
    Q_MAX,
    Q_MIN,
    UNIFORM_Q,
    AnchoredEGTRTopologySampler,
    DRTPSelection,
    EGTRTopologySampler,
)
from algorithms.ri_gmappo.simple_ri_gmappo import RIGMAPPOConfig, train_ri_gmappo


def _selection(group: str) -> DRTPSelection:
    return DRTPSelection(group, group, -1 if group == "N" else 44, 0 if group == "N" else 80, -1 if group == "N" else 1)


def _feed(sampler, repeats: int = 8) -> None:
    for group in ALL_GROUPS:
        value = 100.0 if group == "N" else float(10 * FAILURE_GROUPS.index(group))
        for _ in range(repeats):
            sampler.record_completed_return(_selection(group), value)


def _sequence(sampler):
    rows = []
    for update in (32, 64, 96, 128, 160, 192):
        _feed(sampler)
        row = sampler.maybe_update(update)
        assert row is not None
        rows.append(row)
    return rows


def _valid(q: dict[str, float]) -> bool:
    return math.isclose(sum(q.values()), 1.0, rel_tol=0.0, abs_tol=1e-10) and all(
        Q_MIN - 1e-12 <= q[group] <= Q_MAX + 1e-12 for group in FAILURE_GROUPS
    )


def test_anchor_alpha_zero_is_utr_and_alpha_one_recovers_egtr() -> None:
    zero = AnchoredEGTRTopologySampler(701, 3907, anchor_alpha=0.0)
    one = AnchoredEGTRTopologySampler(701, 3907, anchor_alpha=1.0)
    egtr = EGTRTopologySampler(701, 3907)
    _sequence(zero)
    _sequence(one)
    _sequence(egtr)
    assert all(math.isclose(zero.q[group], UNIFORM_Q, abs_tol=1e-12) for group in FAILURE_GROUPS)
    assert all(math.isclose(one.q[group], egtr.q[group], abs_tol=1e-12) for group in FAILURE_GROUPS)


def test_anchor_preserves_simplex_bounds_and_absolute_utr_bound() -> None:
    alpha = 0.55
    sampler = AnchoredEGTRTopologySampler(702, 3907, anchor_alpha=alpha)
    rows = _sequence(sampler)
    assert _valid(sampler.q)
    for row in rows:
        post_l1 = float(row["post_anchor_uniform_l1"])
        pre_l1 = float(row["pre_anchor_uniform_l1"])
        assert post_l1 <= alpha * pre_l1 + 1e-12
        assert post_l1 <= 2.0 * alpha + 1e-12
        assert math.isclose(
            sum(float(row[f"post_anchor_q_{group}"]) for group in FAILURE_GROUPS), 1.0, abs_tol=1e-10
        )


def test_anchor_state_restore_and_replay_are_exact() -> None:
    left = AnchoredEGTRTopologySampler(703, 3907, anchor_alpha=0.35)
    _feed(left, repeats=5)
    right = AnchoredEGTRTopologySampler(703, 3907, anchor_alpha=0.35)
    right.load_state_dict(left.state_dict())
    _feed(left, repeats=3)
    _feed(right, repeats=3)
    assert left.maybe_update(32) == right.maybe_update(32)
    assert left.state_dict() == right.state_dict()
    assert all(field in AnchoredEGTRTopologySampler.log_fields() for field in (
        "anchor_alpha", "pre_anchor_uniform_l1", "post_anchor_uniform_l1",
        "global_anchor_l1_bound", "egtr_q_step_l1",
        *[f"cumulative_exposure_deviation_{group}" for group in FAILURE_GROUPS],
    ))


def test_anchor_sampler_completes_one_real_cpu_ppo_update(tmp_path: Path) -> None:
    output = tmp_path / "one-update"
    cfg = RIGMAPPOConfig(
        env_name="3d_intercept", seed=704, num_envs=1, rollout_steps=2, updates=1,
        hidden_dim=16, role_dim=4, intent_dim=4, graph_encoder="single", role_gate_mode="none",
        target_policy="straight", strict_target_sensing=True, agent_target_info_bottleneck=True,
        relay_dependent_task=True, business_grounded_geometry=True,
        failed_blue_agent=-1, node_failure_start_step=0, node_failure_duration_steps=0,
        evaluation_enabled=False, save_interval=1, save_snapshots=False,
        milestone_updates={1: "smoke"}, out_dir=str(output), device="cpu",
        drtp_sampler_mode="anchored_egtr", drtp_sampler_seed=704,
        drtp_sampler_anchor_alpha=0.55, drtp_sampler_logging=True,
        runtime_state_checkpointing=True, runtime_state_save_interval=1,
        ppo_epochs=1, minibatch_graphs=2,
    )
    train_ri_gmappo(cfg)
    assert (output / "actor_critic_latest.pt").is_file()
    assert (output / "drtp_topology_sampler_manifest.json").is_file()
    assert (output / "drtp_topology_sampler_log.csv").read_text(encoding="utf-8").count("\n") >= 2
