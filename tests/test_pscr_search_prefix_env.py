import numpy as np

from envs.pscr_search_prefix_env import P8SearchPrefixConfig, PSCRSearchPrefixEnv
from envs.pscr_service_reconfiguration_env import FORECAST_STAGE, PRIMARY_SERVICE


def test_p8_actor_hides_future_truth_before_arrival():
    env = PSCRSearchPrefixEnv(P8SearchPrefixConfig(seed=19))
    obs, critic, graph = env.reset()
    assert obs.shape[0] == env.num_agents
    assert critic.ndim == 1
    assert graph["action_masks"][:, 2].sum() == 0
    for _ in range(env.config.future_arrival_step - 1):
        obs, critic, graph, rewards, dones, info = env.step(np.full(env.num_agents, PRIMARY_SERVICE, dtype=np.int64))
        assert info["future_request_truth_exposed_to_actor"] is False
        assert info["future_request_active"] == 0.0


def test_p8_stage_action_preserves_executor_primary_goal():
    env = PSCRSearchPrefixEnv(P8SearchPrefixConfig(seed=23, commitment_start_step=0, commitment_lock_steps=3))
    env.reset()
    env.step(np.full(env.num_agents, FORECAST_STAGE, dtype=np.int64))
    assert env._committed_intents is not None
    assert env._last_macro_actions.tolist() == [FORECAST_STAGE] * env.num_agents
