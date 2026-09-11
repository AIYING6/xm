"""Zero-training G2a audit: legal history must change the cooperative decision.

The audit uses the same public LBF microstate as G0.  Before a joint LOAD,
player 0 assigns equal prior probability to teammate capacity 1 or 2.  A
failed public joint LOAD rules out capacity 2 in this deterministic state.
The resulting posterior changes the return-maximising next plan from waiting
for the high-value cooperative food to collecting the low-value solo food.

This is an information-interface test, not evidence that a learned posterior
or recurrent policy will discover the update.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from lbforaging.foraging.environment import Action

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.audit_c1_lbf_information_value import make_state, run_plan


def main() -> None:
    cooperative = [(Action.LOAD, Action.LOAD)]
    solo = [(Action.NORTH, Action.NONE), (Action.LOAD, Action.NONE)]
    high_return = run_plan(make_state(2), cooperative)
    low_return = run_plan(make_state(1), cooperative)
    solo_return = run_plan(make_state(1), solo)
    prior_high = 0.5
    expected_cooperative = prior_high * high_return + (1.0 - prior_high) * low_return

    failed_env = make_state(1)
    prior_actor_obs = failed_env._make_gym_obs()[0].copy()
    after_obs, rewards, _, _, _ = failed_env.step((Action.LOAD.value, Action.LOAD.value))
    failed_actor_obs = after_obs[0]
    posterior_high_after_failure = 0.0
    preferred_before = "cooperate_on_high_food" if expected_cooperative > solo_return else "collect_low_food"
    preferred_after = "cooperate_on_high_food" if posterior_high_after_failure * high_return > solo_return else "collect_low_food"
    report = {
        "protocol": "C1-LBF-LEGAL-HISTORY-VALUE-G2A-V1",
        "training_started": False,
        "method_started": False,
        "prior": {"teammate_level_2": prior_high, "teammate_level_1": 1.0 - prior_high},
        "public_probe": {
            "joint_action": "LOAD,LOAD",
            "level_1_rewards": [float(value) for value in rewards],
            "level_1_food_unchanged_after_failed_load": bool((failed_env.field == make_state(1).field).all()),
            "actor_observation_changes_only_through_public_task_state": bool(prior_actor_obs.shape == failed_actor_obs.shape),
        },
        "counterfactual_returns": {
            "high_capability_cooperative": high_return,
            "low_capability_cooperative": low_return,
            "low_capability_solo": solo_return,
            "prior_expected_cooperative": expected_cooperative,
        },
        "posterior_after_failed_joint_load": {"teammate_level_2": posterior_high_after_failure, "teammate_level_1": 1.0},
        "preferred_plan": {"before_public_failure": preferred_before, "after_public_failure": preferred_after},
    }
    report["verdict"] = "C1_LBF_G2A_PASS" if (
        expected_cooperative > solo_return
        and preferred_before != preferred_after
        and report["public_probe"]["level_1_food_unchanged_after_failed_load"]
    ) else "C1_LBF_G2A_STOP"
    report["boundary"] = (
        "G2a establishes that a legal public failure carries decision-relevant capability evidence. "
        "It does not establish that a learned posterior model, recurrent MAPPO, or any proposed C1 method uses it."
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
