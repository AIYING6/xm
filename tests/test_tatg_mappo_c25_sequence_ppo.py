from __future__ import annotations

import json

from scripts.audit_tatg_mappo_c25_sequence_ppo import FREEZE_PATH, RUNNER_PATH, collect_checks


def test_c25_freeze_detects_the_required_sequence_runner_boundary() -> None:
    freeze = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    assert all(collect_checks(freeze, RUNNER_PATH.read_text(encoding="utf-8")).values())
