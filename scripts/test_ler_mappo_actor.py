import torch

from algorithms.mappo.legal_evidence_role_actor import LegalEvidenceRoleActor


def main():
    torch.manual_seed(1)
    actor = LegalEvidenceRoleActor(obs_dim=12)
    obs = torch.randn(3, 12)
    roles = torch.tensor([0, 1, 2])
    valid = torch.tensor([1.0, 0.0, 1.0])
    action, logp = actor(obs, roles, valid, deterministic=True)
    assert action.shape == (3, 2) and logp.shape == (3,)
    assert torch.isfinite(action).all() and torch.isfinite(logp).all()
    try:
        actor(obs, roles, torch.ones(2))
    except ValueError:
        pass
    else:
        raise AssertionError("mismatched evidence mask must fail closed")
    print("LER actor smoke: PASS")


if __name__ == "__main__":
    main()
