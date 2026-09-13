import numpy as np

from envs.pscr_capacity_coupled_service_env import P10CapacityCoupledConfig, PSCRCapacityCoupledServiceEnv
from envs.pscr_service_reconfiguration_env import PRIMARY_SERVICE


def test_p10_standard_interface_and_workload_state():
    env = PSCRCapacityCoupledServiceEnv(P10CapacityCoupledConfig(seed=777))
    obs, critic, graph = env.reset()
    assert obs.shape[0] == env.num_agents
    assert critic.ndim == 1
    _, _, _, rewards, dones, info = env.step(np.full(env.num_agents, PRIMARY_SERVICE))
    assert rewards.shape == (env.num_agents, 1)
    assert dones.shape == (env.num_agents, 1)
    assert info["primary_backlog"] >= 0.0
    assert info["future_request_truth_exposed_before_arrival"] is False


def test_p10_future_deadline_is_public_and_fixed():
    env = PSCRCapacityCoupledServiceEnv(P10CapacityCoupledConfig(seed=888, future_deadline_step=99))
    env.reset()
    assert env._deadline("future") == 99
