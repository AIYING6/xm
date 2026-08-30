from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]

import freeze_drtp_b5_observational_tape as tape_module  # noqa: E402
import run_drtp_b5_observational_single as runner  # noqa: E402


def test_tape_is_deterministic_and_independent() -> None:
    tape = tape_module.build()
    payload = dict(tape)
    digest = payload.pop("tape_hash")
    assert digest == hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    assert tape["episode_ids"] == list(range(600000, 600100))
    assert len(tape["conditions"]) == 5
    assert tape["training_seed_namespace"] == [3601, 3602, 3603, 3604, 3605]


def test_training_config_is_observational_and_exact(tmp_path: Path) -> None:
    for arm, sampler in runner.ARMS.items():
        for seed in runner.SEEDS:
            cfg = runner.training_config(arm, seed, tmp_path / arm / str(seed))
            assert cfg.seed == seed
            assert cfg.updates == 3907
            assert cfg.drtp_sampler_mode == sampler
            assert cfg.drtp_sampler_seed == seed
            assert cfg.group_credit_telemetry is True
            assert cfg.group_credit_telemetry_interval == 20
            assert cfg.failure_aware_telemetry is True
            assert cfg.runtime_state_checkpointing is True
            assert cfg.evaluation_enabled is False


def test_freeze_forbids_adaptive_research_behavior() -> None:
    freeze = json.loads((ROOT / "configs" / "drtp_b5_observational_freeze.json").read_text(encoding="utf-8"))
    assert freeze["status"] == "PREPARED_NOT_AUTHORIZED"
    assert freeze["training_authorized"] is False
    assert freeze["algorithm_modification_authorized"] is False
    assert freeze["gates"]["500k"] == "DESCRIPTIVE_ONLY_NO_STOP"
    assert len(freeze["gates"]["mechanism_go_all_required"]) == 6
    assert freeze["mainline_a_modified"] is False
