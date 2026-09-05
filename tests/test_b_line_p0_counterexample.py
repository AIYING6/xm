from __future__ import annotations

import hashlib
import json
from pathlib import Path

from scripts.run_b_line_p0_counterexample import analyze, load_freeze, write_outputs


def test_same_snapshot_different_history_requires_different_preferred_actions() -> None:
    result, rows = analyze(load_freeze())
    assert result["verdict"] == "B_P0_CONDITIONAL"
    assert result["same_current_snapshot"] is True
    assert result["different_history_changes_preferred_decision"] is True
    assert result["preferred_actions"] == {
        "newly_disconnected": "continue_mission",
        "persistent_disconnected": "reconfigure_relay",
    }
    persistent_continue = next(
        row for row in rows if row["history_id"] == "persistent_disconnected" and row["decision_id"] == "continue_mission"
    )
    assert persistent_continue["continuity_feasible"] is False


def test_artifacts_are_byte_reproducible(tmp_path: Path) -> None:
    result, rows = analyze(load_freeze())
    first = tmp_path / "first"
    second = tmp_path / "second"
    write_outputs(first, result, rows)
    write_outputs(second, result, rows)
    for name in [
        "B_LINE_P0_COUNTEREXAMPLE_RESULT.json",
        "B_LINE_P0_COUNTEREXAMPLE_ROWS.csv",
        "B_LINE_P0_COUNTEREXAMPLE_REPORT.md",
    ]:
        assert hashlib.sha256((first / name).read_bytes()).hexdigest() == hashlib.sha256((second / name).read_bytes()).hexdigest()
    assert json.loads((first / "B_LINE_P0_COUNTEREXAMPLE_RESULT.json").read_text(encoding="utf-8"))["environment_steps"] == 0
