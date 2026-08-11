"""Deterministic pre-training gates for M2R residual acquisition control."""
from __future__ import annotations

import torch

from algorithms.ri_gmappo.acquisition_oriented import TARGET_HISTORY_INDICES
from algorithms.ri_gmappo.acquisition_residual import IdentityPreservingResidualPolicy
from envs.uav_intercept_3d_env import OBS3D_FIELD_NAMES


def same(a, b): return torch.allclose(a, b, atol=1e-7, rtol=0)


def main():
    torch.manual_seed(17)
    obs = torch.randn(2, 4, len(OBS3D_FIELD_NAMES)); previous = torch.randn(2, 4, 3); evidence = torch.tensor([[True, True, False, True], [True, False, True, True]])
    role = torch.tensor([[0, 1, 2, 3], [0, 1, 2, 3]])
    full = IdentityPreservingResidualPolicy(len(OBS3D_FIELD_NAMES), full=True); b1 = IdentityPreservingResidualPolicy(len(OBS3D_FIELD_NAMES), full=False)
    b1.load_state_dict(full.state_dict())
    full_logits, progress, full_state = full.forward_step(obs, previous, evidence, role)
    b1_logits, _progress, b1_state = b1.forward_step(obs, previous, evidence, role)
    assert same(full_logits, b1_logits), "zero residual initialization must give Full=B1"
    assert same(full_state.target[~evidence], torch.zeros_like(full_state.target[~evidence]))
    print("PASS zero_residual_initialization_is_exact_identity")
    print("PASS expired_evidence_resets_target_history")
    with torch.no_grad():
        full.progress_residual_heads[0].bias.fill_(20.0)
    changed, changed_progress, _ = full.forward_step(obs, previous, evidence, role)
    delta = changed[..., :2] - b1_logits[..., :2]
    assert float(delta.abs().max()) <= full.residual_limit + 1e-7
    assert same(changed[..., 2:], b1_logits[..., 2:]), "residual must not alter logstd or commit"
    assert not same(delta, torch.zeros_like(delta))
    print("PASS residual_is_bounded_and_changes_only_turn_climb")
    assert sum(p.numel() for p in full.parameters()) == sum(p.numel() for p in b1.parameters())
    print("PASS full_b1_parameter_counts_match")
    altered = obs.clone(); altered[..., TARGET_HISTORY_INDICES] += 1000.0
    _, _, expiry_state = full.forward_step(altered, previous, torch.zeros_like(evidence), role)
    assert same(expiry_state.target, torch.zeros_like(expiry_state.target))
    print("PASS target_truth_cannot_persist_after_evidence_expiry")
    print("M2R_IDENTITY_PRESERVING_RESIDUAL_REPORT: PASS (5 tests)")


if __name__ == "__main__": main()
