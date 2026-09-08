import torch

from algorithms.sustained_support_role_sg_mappo import SustainedSupportRoleSharedSGMPPO
from scripts.run_drtp_6uav_v3_q0 import make_env


def test_v3_policy_emits_legal_relay_actions() -> None:
    env = make_env(93001)
    _, share, graph = env.reset()
    policy = SustainedSupportRoleSharedSGMPPO(env.obs_dim, env.share_obs_dim)
    actions, _, _, values = policy.action_value(
        torch.tensor(graph["node_features"][None], dtype=torch.float32), torch.tensor(graph["roles"][None]),
        torch.tensor(graph["active_adj"][None], dtype=torch.float32), torch.tensor(graph["action_masks"][None], dtype=torch.float32),
        torch.tensor(share[None], dtype=torch.float32), deterministic=True,
    )
    assert actions.shape == (1, 6)
    assert values.shape == (1, 6)
    assert all(graph["action_masks"][i, int(actions[0, i])] for i in range(env.n))
