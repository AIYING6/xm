import json

import pytest
import torch

from scripts.run_epistemic_commitment_p2_pilot import (
    CommitmentPilotRunner,
    load_freeze,
    run_evaluate,
    run_train,
)


def _state_equal(left, right):
    if isinstance(left, torch.Tensor):
        return torch.equal(left, right)
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(_state_equal(left[k], right[k]) for k in left)
    if isinstance(left, (list, tuple)):
        return len(left) == len(right) and all(_state_equal(a, b) for a, b in zip(left, right))
    return left == right


def test_freeze_budget_and_capacity_are_exact():
    freeze = load_freeze()
    assert freeze["physical_steps_per_run"] == 1_000_000
    assert freeze["episodes_per_run"] * freeze["physical_steps_per_episode"] == 1_000_000
    counts = [
        sum(p.numel() for p in CommitmentPilotRunner(method, 98101, freeze).actor.parameters())
        for method in freeze["methods"]
    ]
    assert counts == [7272, 7272]


def test_formal_runner_checkpoint_continuation_is_exact():
    freeze = load_freeze()
    runner = CommitmentPilotRunner(freeze["methods"][0], 98101, freeze)
    runner.update(6)
    state = runner.state_dict()
    expected = runner.update(6)
    expected_state = runner.state_dict()
    resumed = CommitmentPilotRunner(freeze["methods"][0], 98101, freeze)
    resumed.load_state_dict(state)
    actual = resumed.update(6)
    assert actual == expected
    assert _state_equal(resumed.actor.state_dict(), expected_state["actor"])
    assert _state_equal(resumed.critic.state_dict(), expected_state["critic"])


def test_smoke_is_not_accepted_as_fixed_endpoint(tmp_path):
    freeze = load_freeze()
    method = freeze["methods"][0]
    manifest = run_train(method, 98101, tmp_path, True, True)
    assert manifest["physics_steps"] == 48
    assert manifest["scientific_evidence"] is False
    with pytest.raises(ValueError, match="run manifest mismatch"):
        run_evaluate(method, 98101, tmp_path, True)


def test_seed_registry_and_overwrite_protection(tmp_path):
    freeze = load_freeze()
    with pytest.raises(ValueError, match="outside frozen registry"):
        run_train(freeze["methods"][0], 99999, tmp_path, False, False)
    run_train(freeze["methods"][0], 98101, tmp_path, True, True)
    with pytest.raises(FileExistsError):
        run_train(freeze["methods"][0], 98101, tmp_path, True, True)
    manifest = json.loads(
        (tmp_path / "runs" / freeze["methods"][0] / "seed98101" / "run_manifest.json").read_text()
    )
    assert manifest["status"] == "smoke_complete"
