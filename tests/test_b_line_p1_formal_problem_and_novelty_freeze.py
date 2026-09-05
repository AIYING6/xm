from __future__ import annotations

import json
from pathlib import Path

from scripts.run_b_line_p1_formal_problem_and_novelty_freeze import analyze, write_outputs


def test_p1_freeze_preserves_native_boundary_and_stops_before_solver(tmp_path: Path) -> None:
    result = analyze()

    assert result["verdict"] == "B_P1_CONDITIONAL"
    assert result["upstream_p0r_verdict"] == "B_P0R_GO"
    assert result["checks"]["p0r_native_snapshot_insufficiency_established"] is True
    assert result["checks"]["native_freshness_is_hard_feasibility_not_soft_penalty"] is True
    assert result["checks"]["only_native_scout_and_terminal_actions_frozen"] is True
    assert result["checks"]["relay_control_not_misrepresented_as_native"] is True
    assert result["checks"]["current_native_interface_lacks_controllable_reconfiguration"] is True
    assert result["checks"]["selected_solver_implemented"] is False
    assert result["environment_steps"] == 0
    assert result["ppo_updates"] == 0
    assert result["evaluation_episodes"] == 0

    output_dir = tmp_path / "p1"
    write_outputs(output_dir, result)
    assert json.loads((output_dir / "B_P1_FORMAL_PROBLEM_NOVELTY_RESULT.json").read_text(encoding="utf-8")) == result
