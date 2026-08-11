"""Collector-path regression: legal evidence -> expiry -> fresh evidence."""
from __future__ import annotations

import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.acquisition_oriented import AcquisitionOrientedHybridPolicy  # noqa: E402
from envs.uav_intercept_3d_env import OBS3D_FIELD_NAMES  # noqa: E402
from scripts.run_m2_acquisition_oriented_pilot import policy_step  # noqa: E402


def main() -> None:
    torch.manual_seed(2203)
    policy = AcquisitionOrientedHybridPolicy(len(OBS3D_FIELD_NAMES), num_roles=4, full=True)
    obs = torch.zeros(1, len(OBS3D_FIELD_NAMES)); previous = torch.zeros(1, 3)
    role = torch.tensor([2]); attack = torch.ones(1)
    state = policy.core.initial_state(obs)
    # Delivered/cache-valid target claim: target values + confidence are legal.
    fresh = obs.clone(); fresh[:, 8:15] = 0.25; fresh[:, 31] = 1.0
    _a, _lp, _e, state = policy_step(policy, fresh, previous, torch.tensor([True]), role, state, attack)
    assert torch.any(state.target != 0)
    # The next collector timestep marks expiry.  Altering the now-illegal
    # payload cannot keep or reintroduce target memory.
    expired = obs.clone(); expired[:, 8:15] = 9_999.0; expired[:, 31] = 0.0
    _a, _lp, _e, state = policy_step(policy, expired, previous, torch.tensor([False]), role, state, attack)
    assert torch.equal(state.target, torch.zeros_like(state.target))
    refreshed = obs.clone(); refreshed[:, 8:15] = -0.5; refreshed[:, 31] = 0.8
    _a, _lp, _e, state = policy_step(policy, refreshed, previous, torch.tensor([True]), role, state, attack)
    assert torch.any(state.target != 0)
    print("M2_COLLECTOR_EXPIRY_ROLLOUT_PASS: nonzero -> zero on expiry -> nonzero after fresh legal evidence")


if __name__ == "__main__":
    main()
