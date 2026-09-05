from __future__ import annotations

import csv
import json
from pathlib import Path

from scripts.run_b_line_p05_environment_semantic_audit import audit, write_outputs


def test_p05_static_audit_is_partial_and_zero_training(tmp_path: Path) -> None:
    result, rows = audit()

    assert result["verdict"] == "B_P05_SEMANTIC_PARTIAL"
    assert result["environment_steps"] == 0
    assert result["ppo_updates"] == 0
    assert result["checks"]["native_time_dependent_information_semantics"] is True
    assert result["checks"]["actor_legal_age_or_topology_signal_exists"] is True
    assert result["checks"]["native_maximum_consecutive_route_outage_requirement"] is False
    assert result["checks"]["native_mandatory_relay_reconfiguration_action"] is False
    assert {row["classification"] for row in rows} == {
        "environment_native_semantics",
        "legally_derivable_internal_state",
        "newly_introduced_assumption",
    }

    output_dir = tmp_path / "p05"
    write_outputs(output_dir, result, rows)
    saved = json.loads((output_dir / "B_P05_ENVIRONMENT_SEMANTIC_AUDIT_RESULT.json").read_text(encoding="utf-8"))
    assert saved == result
    with (output_dir / "B_P05_ENVIRONMENT_SEMANTIC_LEDGER.csv").open(encoding="utf-8", newline="") as handle:
        assert len(list(csv.DictReader(handle))) == len(rows)
