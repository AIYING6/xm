import numpy as np

from envs.pscr_adversarial_service_env import PSCRConfig
from envs.pscr_role_commitment_env import PSCRRoleCommitmentEnv
from envs.pscr_service_reconfiguration_env import FORECAST_STAGE, PRIMARY_SERVICE


def test_role_resolved_commitment_is_public_and_locked():
    env = PSCRRoleCommitmentEnv(PSCRConfig(seed=7, commitment_start_step=2, commitment_lock_steps=3))
    env.reset()
    for _ in range(2):
        env.step(np.full(3, PRIMARY_SERVICE, dtype=np.int64))
    _, _, _, _, _, info = env.step(np.full(3, FORECAST_STAGE, dtype=np.int64))
    assert info["role_commitment_locked"] == 1.0
    assert env._last_macro_actions.tolist() == [FORECAST_STAGE] * 3
    env.step(np.full(3, PRIMARY_SERVICE, dtype=np.int64))
    assert env._last_macro_actions.tolist() == [FORECAST_STAGE] * 3
    assert env.actor_observation().shape[0] == env.num_agents
