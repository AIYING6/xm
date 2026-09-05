from __future__ import annotations

import json
from pathlib import Path

from scripts.run_b_line_p15_native_decision_expressiveness_audit import analyze, write_outputs


def test_current_native_interface_is_not_high_ceiling_reconfiguration_control(tmp_path: Path) -> None:
    result = analyze()

    assert result["verdict"] == "B_P15_NO_GO_CURRENT_INTERFACE"
    capabilities = result["capabilities"]
    assert capabilities["p0r_problem_premise_retained"] is True
    assert capabilities["main_has_as_many_scouts_as_objectives"] is True
    assert capabilities["all_main_scout_objective_pairs_senseable_at_reset"] is True
    assert capabilities["all_main_legal_routes_active_at_reset"] is True
    assert capabilities["sensing_has_no_direct_native_reward_cost"] is True
    assert capabilities["relay_actions_are_transition_effective"] is False
    assert capabilities["previous_mask_closed_under_joint_transition"] is False
    assert capabilities["nontrivial_native_reconfiguration_variable_exists"] is False
    assert result["environment_steps"] == 12
    assert result["evaluation_episodes"] == 0
    assert result["ppo_updates"] == 0

    output_dir = tmp_path / "p15"
    write_outputs(output_dir, result)
    assert json.loads((output_dir / "B_P15_NATIVE_DECISION_EXPRESSIVENESS_RESULT.json").read_text(encoding="utf-8")) == result
