from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_p4_freeze_and_tape_are_independent() -> None:
    freeze = json.loads((ROOT / "configs" / "pp_drtp_p4_validation_freeze.json").read_text())
    tape = json.loads((ROOT / "configs" / "pp_drtp_p4_validation_tape.json").read_text())
    p3 = json.loads((ROOT / "configs" / "pp_drtp_p3_pilot_tape.json").read_text())
    assert freeze["training_seeds"] == [3501, 3502, 3503, 3504, 3505]
    assert freeze["updates"] == 1953
    assert freeze["pp_probe_count"] == 4
    assert freeze["max_parallel"] == 15
    assert freeze["automatic_continuation"] is False
    assert len(tape["episode_ids"]) == 100 == len(set(tape["episode_ids"]))
    assert set(tape["episode_ids"]).isdisjoint(p3["episode_ids"])
    assert [condition["name"] for condition in tape["conditions"]] == [
        "nominal", "F0_44_80", "T28_28_80", "D120_44_120", "C28_120"
    ]


def test_p4_training_configs_keep_pp_as_only_method_change(tmp_path: Path) -> None:
    module = load_module(ROOT / "scripts" / "run_pp_drtp_p4_single.py", "pp_p4_single")
    configs = {arm: module.training_config(arm, 3501, tmp_path / arm)
               for arm in module.ARMS}
    assert configs["utr_sg"].drtp_sampler_mode == "utr"
    assert configs["drtp_sg"].drtp_sampler_mode == "drtp"
    assert configs["pp_drtp_sg"].drtp_sampler_mode == "pp_drtp"
    assert configs["pp_drtp_sg"].pp_drtp_probe_count == 4
    ignored = {"out_dir", "drtp_sampler_mode"}
    base = configs["drtp_sg"].__dict__
    candidate = configs["pp_drtp_sg"].__dict__
    assert {key: value for key, value in base.items() if key not in ignored} == {
        key: value for key, value in candidate.items() if key not in ignored
    }


def test_p4_contract_binds_runner_protocol_and_hashes() -> None:
    module = load_module(ROOT / "scripts" / "run_pp_drtp_p4_single.py", "pp_p4_single_hash")
    assert module.PROTOCOL == "PP-DRTP-P4-INDEPENDENT-VALIDATION-V1"
    assert module.SEEDS == (3501, 3502, 3503, 3504, 3505)
    assert hashlib.sha256(module.TAPE.read_bytes()).hexdigest()
    assert hashlib.sha256(module.FREEZE.read_bytes()).hexdigest()


def test_p4_catastrophic_gate_handles_signed_reference_endpoints() -> None:
    module = load_module(ROOT / "scripts" / "aggregate_pp_drtp_p4.py", "pp_p4_gate")
    reference = {"J_F0": -2.0, "J_pert_worst": -4.0, "timeout": 0.5}
    candidate = {"J_F0": -1.0, "J_pert_worst": -3.0, "timeout": 0.5}
    assert module.catastrophic(candidate, reference, 7.874919837916801) is False
