"""Regression tests for the separate V3 sustained-support task semantics."""
from scripts.run_drtp_6uav_v3_q0 import GROUPS, run_group


def test_v3_nominal_and_recoverable_faults_complete() -> None:
    outcomes = {group: run_group(93001, group) for group in GROUPS}
    assert outcomes["nominal"]["success"]
    assert outcomes["R_upstream"]["success"]
    assert outcomes["R_downstream"]["success"]
    assert outcomes["C_balanced"]["success"]


def test_v3_capacity_faults_are_partial_not_cutsets() -> None:
    outcomes = {group: run_group(93001, group) for group in GROUPS}
    for group in ("C_relay_node", "C_cross", "C_same_relay"):
        assert outcomes[group]["fault_injected"]
        assert outcomes[group]["completed"] in ([1, 0], [0, 1])
        assert not outcomes[group]["success"]
