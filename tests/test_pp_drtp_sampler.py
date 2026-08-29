from __future__ import annotations

from algorithms.ri_gmappo.drtp_topology_sampler import (
    ALL_GROUPS,
    FAILURE_GROUPS,
    PairedProbeTopologySampler,
)


def probe_records(update: int, count: int = 4) -> list[dict]:
    records = []
    for base_id in range(count):
        for group_index, group in enumerate(ALL_GROUPS):
            records.append({
                "base_id": base_id,
                "group": group,
                "episode_return": 100.0 - 10.0 * group_index - float(base_id),
            })
    return records


def test_pp_drtp_requires_balanced_same_base_id_probe_batch():
    sampler = PairedProbeTopologySampler(seed=1, total_updates=200, probe_count=4)
    records = probe_records(160)
    records.pop()
    try:
        sampler.record_probe_batch(160, records)
    except ValueError as exc:
        assert "incorrect group count" in str(exc)
    else:
        raise AssertionError("unbalanced PP-DRTP probe batch must fail")


def test_pp_drtp_probe_update_preserves_simplex_and_logs_summary():
    sampler = PairedProbeTopologySampler(seed=1, total_updates=200, probe_count=4)
    sampler.record_probe_batch(160, probe_records(160))
    row = sampler.maybe_update(160)
    assert row is not None
    assert row["adapted"] is True
    assert row["reason"] == "paired_probe_bounded_exponentiated_gradient"
    assert row["probe_base_id_count"] == 4
    assert all(row[f"probe_count_{group}"] == 4 for group in ALL_GROUPS)
    assert abs(sum(sampler.q.values()) - 1.0) < 1e-10
    assert all(0.05 <= sampler.q[group] <= 0.35 for group in FAILURE_GROUPS)
    assert sampler.uses_completed_return_feedback is False


def test_pp_drtp_mid_boundary_save_reload_is_exact():
    left = PairedProbeTopologySampler(seed=2, total_updates=200, probe_count=4)
    left.record_probe_batch(160, probe_records(160))
    state = left.state_dict()
    right = PairedProbeTopologySampler(seed=2, total_updates=200, probe_count=4)
    right.load_state_dict(state)
    assert left.maybe_update(160) == right.maybe_update(160)
    assert left.state_dict() == right.state_dict()
