"""Regression for M2R's real policy-step expiry and residual contract."""
from __future__ import annotations

import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.acquisition_residual import IdentityPreservingResidualPolicy  # noqa: E402
from envs.uav_intercept_3d_env import OBS3D_FIELD_NAMES  # noqa: E402
from scripts.run_m2_acquisition_oriented_pilot import policy_step  # noqa: E402


def _step(policy, obs, valid, role, state):
    return policy_step(
        policy,
        obs,
        torch.zeros(obs.shape[0], 3),
        torch.as_tensor(valid),
        role,
        state,
        torch.ones(obs.shape[0]),
        deterministic=True,
    )


def main() -> None:
    torch.manual_seed(2401)
    full = IdentityPreservingResidualPolicy(len(OBS3D_FIELD_NAMES), full=True)
    b1 = IdentityPreservingResidualPolicy(len(OBS3D_FIELD_NAMES), full=False)
    b1.load_state_dict(full.state_dict())
    role = torch.tensor([2])  # Attacker: the only role with a live commit action.
    empty = torch.zeros(1, len(OBS3D_FIELD_NAMES))

    # Directly changing the residual branch cannot modify the commit logit.
    with torch.no_grad():
        full.progress_residual_heads[2].bias.fill_(5.0)
    state_full = full.core.initial_state(empty)
    state_b1 = b1.core.initial_state(empty)
    full_logits, _progress, _ = full.forward_step(empty, torch.zeros(1, 3), torch.tensor([False]), role, state_full)
    b1_logits, _progress, _ = b1.forward_step(empty, torch.zeros(1, 3), torch.tensor([False]), role, state_b1)
    assert torch.equal(full_logits[..., 2:], b1_logits[..., 2:])
    assert torch.all((full_logits[..., :2] - b1_logits[..., :2]).abs() <= 0.25 + 1e-7)

    # This follows the same policy_step used by the collector. A legal target
    # claim creates history; expiry clears it, and illegal payload variation
    # cannot alter the reset target/progress state.
    fresh = empty.clone(); fresh[:, 8:15] = 0.25; fresh[:, 31] = 1.0
    _a, _lp, _e, state = _step(full, fresh, [True], role, full.core.initial_state(empty))
    assert torch.any(state.target != 0)
    expired_a = empty.clone(); expired_a[:, 8:15] = 10_000.0; expired_a[:, 31] = 0.0
    expired_b = empty.clone(); expired_b[:, 8:15] = -10_000.0; expired_b[:, 31] = 0.0
    _a, _lp, _e, state_a = _step(full, expired_a, [False], role, state)
    _a, _lp, _e, state_b = _step(full, expired_b, [False], role, state)
    assert torch.equal(state_a.target, torch.zeros_like(state_a.target))
    assert torch.equal(state_a.target, state_b.target)
    # A new legal packet restarts target history from legal evidence.
    refreshed = empty.clone(); refreshed[:, 8:15] = -0.5; refreshed[:, 31] = 0.8
    _a, _lp, _e, refreshed_state = _step(full, refreshed, [True], role, state_a)
    assert torch.any(refreshed_state.target != 0)
    print("M2R_COLLECTOR_ROLLOUT_CONTRACT_PASS: expiry resets target history; residual is bounded and cannot alter commit")


if __name__ == "__main__":
    main()
