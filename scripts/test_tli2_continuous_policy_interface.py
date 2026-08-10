"""Synthetic, no-training gate for the TLI2 hybrid PPO action interface."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.hybrid_action import HybridActionHead  # noqa: E402


OUT = ROOT / "results" / "tli2_continuous_policy_interface_validation"


def main() -> None:
    torch.manual_seed(1702)
    head = HybridActionHead(input_dim=16, hidden_dim=32)
    features = torch.randn(64, 16)
    dist = head.distribution(features)
    continuous, commit, old_log_prob = dist.sample(deterministic=False)
    recomputed = dist.log_prob(continuous, commit)
    deterministic_continuous, deterministic_commit, deterministic_lp = dist.sample(deterministic=True)
    checks = {
        "sample_finite_and_bounded": bool(torch.isfinite(continuous).all() and torch.isfinite(commit).all() and (continuous.abs() < 1.0).all()),
        "sample_log_prob_matches_recompute": bool(torch.allclose(old_log_prob, recomputed, atol=2e-5, rtol=2e-5)),
        "joint_ratio_is_finite": bool(torch.isfinite(torch.exp(recomputed - old_log_prob)).all()),
        "deterministic_uses_distribution_center": bool(torch.allclose(deterministic_continuous, torch.tanh(dist.mean), atol=1e-6)),
        "commit_head_is_binary": bool(torch.all((deterministic_commit == 0) | (deterministic_commit == 1))),
        "no_boundary_collapse_in_synthetic_batch": bool(float((continuous.abs() > 0.999).float().mean()) < 0.5),
    }

    # One actual PPO-style ratio update on a synthetic batch.  This validates
    # gradient flow without touching the environment or formal training code.
    advantages = torch.randn(64)
    new_dist = head.distribution(features)
    new_log_prob = new_dist.log_prob(continuous.detach(), commit.detach())
    ratio = torch.exp(new_log_prob - old_log_prob.detach())
    loss = -(torch.minimum(ratio * advantages, ratio.clamp(0.8, 1.2) * advantages)).mean()
    optimizer = torch.optim.Adam(head.parameters(), lr=3e-4)
    optimizer.zero_grad(set_to_none=True)
    loss.backward()
    grad_norm = torch.nn.utils.clip_grad_norm_(head.parameters(), 10.0)
    optimizer.step()
    checks["synthetic_ppo_update_finite"] = bool(torch.isfinite(loss) and torch.isfinite(grad_norm))
    checks["continuous_and_commit_heads_separate"] = bool(
        dist.mean.shape[-1] == 2 and dist.commit.logits.shape == (64,)
    )
    if not all(checks.values()):
        raise AssertionError(checks)
    payload = {
        "status": "TLI2_CONTINUOUS_POLICY_INTERFACE_PASS",
        "no_training": True,
        "distribution": "tanh_squashed_gaussian_plus_bernoulli",
        "jacobian_correction": True,
        "checks": checks,
        "loss": float(loss.detach()),
        "grad_norm": float(grad_norm),
        "performance_use_prohibited": True,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "TLI2_CONTINUOUS_POLICY_INTERFACE.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    for name in checks:
        print(f"PASS {name}")
    print("TLI2_CONTINUOUS_POLICY_INTERFACE_REPORT: PASS (8 tests)")


if __name__ == "__main__":
    main()
