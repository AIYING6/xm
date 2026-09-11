"""Zero-training G0 audit for the C1 latent-capability teaming candidate.

This script uses the public Level-Based Foraging (LBF) environment.  It
constructs two states with identical observation for player 0 after teammate
levels are hidden.  Only player 1's latent level differs.  The audit compares
two short, fixed joint plans: cooperative loading of a high-value food item
and solo collection of a lower-value item.

Run it with a separate environment containing ``lbforaging==2.0.0``.  It is
not part of the existing UAV training stack and never trains a policy.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from lbforaging.foraging.environment import Action, ForagingEnv


def make_state(teammate_level: int) -> ForagingEnv:
    env = ForagingEnv(
        players=2,
        min_player_level=1,
        max_player_level=3,
        min_food_level=1,
        max_food_level=3,
        field_size=(5, 5),
        max_num_food=2,
        sight=5,
        max_episode_steps=4,
        force_coop=False,
        normalize_reward=False,
        observe_agent_levels=False,
    )
    env.reset(seed=17)
    env.field.fill(0)
    env.field[2, 2] = 3  # needs both agents only in the high-capability state
    env.field[1, 1] = 1  # player 0 can collect this alone after moving north
    env.players[0].position = (2, 1)
    env.players[0].level = 1
    env.players[1].position = (2, 3)
    env.players[1].level = teammate_level
    for player in env.players:
        player.score = 0
        player.reward = 0
        player.history = []
    # Positions were set manually for this deterministic counterexample, so
    # refresh the public environment's action mask before evaluating a plan.
    env._gen_valid_moves()
    return env


def run_plan(env: ForagingEnv, actions: list[tuple[Action, Action]]) -> float:
    for joint_action in actions:
        _, rewards, _, _, _ = env.step(tuple(action.value for action in joint_action))
    return float(env.players[0].score)


def main() -> None:
    high = make_state(teammate_level=2)
    low = make_state(teammate_level=1)
    high_obs = high._make_gym_obs()[0]
    low_obs = low._make_gym_obs()[0]

    cooperative_plan = [(Action.LOAD, Action.LOAD)]
    solo_plan = [(Action.NORTH, Action.NONE), (Action.LOAD, Action.NONE)]
    results = {}
    for label, teammate_level in (("teammate_level_2", 2), ("teammate_level_1", 1)):
        results[label] = {
            # LBF's mask maps are keyed by player objects, so independently
            # recreate the same deterministic state rather than deepcopy it.
            "cooperative_high_food": run_plan(make_state(teammate_level), cooperative_plan),
            "solo_low_food": run_plan(make_state(teammate_level), solo_plan),
        }
        results[label]["preferred_plan"] = max(
            results[label], key=lambda key: results[label][key]
        )

    report = {
        "protocol": "C1-LBF-INFORMATION-VALUE-G0-V1",
        "training_started": False,
        "environment": "Level-Based Foraging 2.0.0",
        "player_0_observation_equal_after_teammate_level_mask": bool(
            np.array_equal(high_obs, low_obs)
        ),
        "hidden_variable": "player_1_level",
        "plans": {
            "cooperative_high_food": ["LOAD,LOAD"],
            "solo_low_food": ["NORTH,NONE", "LOAD,NONE"],
        },
        "outcomes": results,
    }
    report["different_preferred_plan"] = (
        results["teammate_level_2"]["preferred_plan"]
        != results["teammate_level_1"]["preferred_plan"]
    )
    report["verdict"] = (
        "C1_LBF_G0_PASS"
        if report["player_0_observation_equal_after_teammate_level_mask"]
        and report["different_preferred_plan"]
        else "C1_LBF_G0_STOP"
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
