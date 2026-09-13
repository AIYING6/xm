import numpy as np

from envs.pscr_full_team_commitment_env import PSCRFullTeamCommitmentEnv
from envs.pscr_search_prefix_env import P8SearchPrefixConfig
from envs.pscr_service_reconfiguration_env import FORECAST_STAGE


def test_p9_full_team_forecast_intent_moves_executor_to_public_forecast_goal():
    env = PSCRFullTeamCommitmentEnv(P8SearchPrefixConfig(seed=123))
    env.reset()
    assert np.array_equal(env._role_goal(env.executor, FORECAST_STAGE), env._forecast_position)


def test_p9_retains_standard_environment_interface():
    env = PSCRFullTeamCommitmentEnv(P8SearchPrefixConfig(seed=456))
    obs, critic, graph = env.reset()
    assert obs.shape[0] == env.num_agents
    assert critic.ndim == 1
    assert graph["task_contract"].tolist() == [1]
