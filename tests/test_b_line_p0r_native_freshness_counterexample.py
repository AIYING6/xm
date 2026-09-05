from __future__ import annotations

import csv
import json
from pathlib import Path

from scripts.run_b_line_p0r_native_freshness_counterexample import analyze, write_outputs


def test_native_freshness_pair_has_same_physics_and_different_native_feasibility(tmp_path: Path) -> None:
    result, rows = analyze()

    assert result["verdict"] == "B_P0R_GO"
    assert result["environment_steps_for_state_construction"] == 14
    assert result["evaluation_episodes"] == 0
    assert result["ppo_updates"] == 0
    assert result["checks"]["same_current_physical_snapshot"] is True
    assert result["checks"]["only_native_freshness_differs"] is True
    assert result["checks"]["native_action_masks_differ"] is True
    assert result["checks"]["fresh_objective_action_legal"] is True
    assert result["checks"]["stale_objective_action_illegal"] is True
    assert result["checks"]["cache_threshold_overridden"] is False
    assert result["checks"]["environment_modified"] is False
    assert result["checks"]["new_action_added"] is False
    assert all(row["fresh_cache_age"] == 0 for row in rows)
    assert all(row["stale_cache_age"] == 6 for row in rows)

    output_dir = tmp_path / "p0r"
    write_outputs(output_dir, result, rows)
    saved = json.loads((output_dir / "B_P0R_NATIVE_FRESHNESS_RESULT.json").read_text(encoding="utf-8"))
    assert saved == result
    with (output_dir / "B_P0R_NATIVE_FRESHNESS_ACTION_LEDGER.csv").open(encoding="utf-8", newline="") as handle:
        assert len(list(csv.DictReader(handle))) == 2
