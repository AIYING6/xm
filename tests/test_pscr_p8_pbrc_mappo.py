import torch

from algorithms.pscr_p8_pbrc_mappo import PSCRPBRCRoleCommitmentMAPPO
from envs.pscr_service_reconfiguration_env import FORECAST_STAGE, PRIMARY_SERVICE


def test_pbrc_plan_mapping_and_semantic_controls():
    plans = torch.tensor([0, 1])
    actions = PSCRPBRCRoleCommitmentMAPPO.plan_actions(plans)
    assert actions.tolist() == [
        [PRIMARY_SERVICE, PRIMARY_SERVICE, PRIMARY_SERVICE],
        [FORECAST_STAGE, FORECAST_STAGE, PRIMARY_SERVICE],
    ]
    context = torch.tensor([[0.1, -1.0, 0.2, 1.0, 1.0], [0.9, 1.0, 0.2, 1.0, 1.0]])
    assert torch.allclose(PSCRPBRCRoleCommitmentMAPPO.transform_context(context, "pbrc"), context)
    assert torch.allclose(PSCRPBRCRoleCommitmentMAPPO.transform_context(context, "plan_no_reliability")[:, 0], torch.tensor([0.5, 0.5]))
    assert torch.allclose(PSCRPBRCRoleCommitmentMAPPO.transform_context(context, "permuted_pbrc")[:, 0], torch.tensor([0.9, 0.1]))
