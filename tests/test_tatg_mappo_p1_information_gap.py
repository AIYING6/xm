from __future__ import annotations

import numpy as np

from scripts.run_tatg_mappo_p1_information_gap import ambiguity_count, cohort_summary, topology_snapshot_code, transition_label


def _graph(comm: int, age: int) -> dict[str, np.ndarray]:
    relation = np.zeros((3, 3, 3), dtype=np.float32)
    relation[1] = np.eye(3, dtype=np.float32)
    relation[1, 2, 1] = comm
    relation[2] = np.eye(3, dtype=np.float32)
    edge = np.zeros((3, 3, 17), dtype=np.float32)
    edge[:, :, 15] = age / 40.0
    return {"relation_adj": relation, "edge_feat": edge, "node_feat": np.zeros((4, 20), dtype=np.float32)}


def test_transition_labels_are_derived_from_consecutive_legal_relations() -> None:
    up = np.ones((3, 3), dtype=np.float32)
    down = up.copy()
    down[2, 1] = 0.0
    assert transition_label(up, down) == "loss"
    assert transition_label(down, up) == "recovery"
    assert transition_label(up, up) == "stable"


def test_topology_code_retains_existing_edge_age_proxy() -> None:
    assert topology_snapshot_code(_graph(comm=1, age=0), 40) != topology_snapshot_code(_graph(comm=1, age=1), 40)


def test_history_can_disambiguate_a_current_topology_collision() -> None:
    snapshot = topology_snapshot_code(_graph(comm=1, age=0), 40)
    rows = [
        {"snapshot_code": snapshot, "history_code": "up=>up", "transition_label": "stable"},
        {"snapshot_code": snapshot, "history_code": "down=>up", "transition_label": "recovery"},
    ]
    assert ambiguity_count(rows, "snapshot_code") == (1, 2)
    assert ambiguity_count(rows, "history_code") == (0, 0)


def test_cohort_gate_requires_both_events_ambiguity_and_pure_history() -> None:
    decision = {
        "per_cohort_required_loss_events": 1,
        "per_cohort_required_recovery_events": 1,
        "per_cohort_required_ambiguous_snapshot_rows": 2,
        "per_cohort_required_history_mixed_code_count": 0,
    }
    rows = [
        {"snapshot_code": "down", "history_code": "up=>down", "transition_label": "loss"},
        {"snapshot_code": "up", "history_code": "down=>up", "transition_label": "recovery"},
        {"snapshot_code": "up", "history_code": "up=>up", "transition_label": "stable"},
    ]
    assert cohort_summary(rows, decision)["pass"] is True
