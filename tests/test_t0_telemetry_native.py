from __future__ import annotations

import json

import pytest

from scripts.telemetry_native_t0 import (
    F0,
    NOMINAL,
    read_jsonl,
    run_episode,
    run_episode_without_logger,
    write_evidence_bundle,
)


def test_t0_aggregate_is_rederived_from_raw_steps(tmp_path):
    output = tmp_path / "bundle"
    manifest = write_evidence_bundle(output, [(910000, NOMINAL), (910000, F0)])
    assert manifest["source_closure_pass"] is True
    assert manifest["historical_aggregate_reuse"] is False
    raw = read_jsonl(output / "raw_step_telemetry.jsonl")
    aggregates = read_jsonl(output / "episode_aggregates.jsonl")
    assert len(raw) == manifest["step_count"]
    assert len(aggregates) == 2
    assert all(row["actor"]["classification"] == "actor_legal" for row in raw)
    assert all(row["diagnostic"]["classification"] == "diagnostic_only" for row in raw)


def test_t0_same_seed_and_policy_are_deterministic():
    first_steps, first = run_episode(910001, F0)
    second_steps, second = run_episode(910001, F0)
    assert first == second
    assert json.dumps(first_steps, default=lambda value: value.tolist() if hasattr(value, "tolist") else value, sort_keys=True) == json.dumps(
        second_steps, default=lambda value: value.tolist() if hasattr(value, "tolist") else value, sort_keys=True
    )


def test_t0_raw_logger_does_not_change_episode_aggregate():
    _, logged = run_episode(910001, F0)
    unlogged = run_episode_without_logger(910001, F0)
    assert logged == unlogged


def test_t0_refuses_to_overwrite_existing_evidence_root(tmp_path):
    output = tmp_path / "bundle"
    write_evidence_bundle(output, [(910000, NOMINAL)])
    with pytest.raises(FileExistsError):
        write_evidence_bundle(output, [(910000, NOMINAL)])
