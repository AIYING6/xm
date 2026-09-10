import numpy as np

from envs.dve_async_uav_env import DVEAsyncUAVEnv, DVECase


def test_standard_interface_and_valid_accept():
    env = DVEAsyncUAVEnv(DVECase(80.0, 1.0, True, False))
    obs, share_obs, graph_obs = env.reset()
    assert obs.shape == (2, 4)
    assert share_obs.shape == (8,)
    assert graph_obs["edge_index"].shape == (2, 2)
    _, _, _, rewards, dones, infos = env.step(np.asarray([1, 0]))
    assert rewards.tolist() == [8.0, 8.0]
    assert dones.all()
    assert not infos[0]["stale_accept"]


def test_joint_conflict_is_detected():
    env = DVEAsyncUAVEnv(DVECase(20.0, 1.0, True, False))
    env.reset()
    _, _, _, rewards, _, infos = env.step(np.asarray([1, 1]))
    assert rewards.tolist() == [-10.0, -10.0]
    assert infos[0]["joint_conflict"]

