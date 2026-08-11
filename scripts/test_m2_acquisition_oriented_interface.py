"""Deterministic no-training M2 gate for the paired acquisition policy."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.acquisition_oriented import (  # noqa: E402
    AcquisitionOrientedHybridPolicy,
    TARGET_HISTORY_INDICES,
)
from algorithms.ri_gmappo.hybrid_action import TanhGaussianBernoulli  # noqa: E402
from envs.uav_intercept_3d_env import OBS3D_FIELD_NAMES  # noqa: E402

OUT = ROOT / "results" / "m2_acquisition_oriented_interface"


def count_params(module: torch.nn.Module) -> int:
    return sum(parameter.numel() for parameter in module.parameters())


def main() -> None:
    torch.manual_seed(2202)
    obs_dim, batch = len(OBS3D_FIELD_NAMES), 6
    full = AcquisitionOrientedHybridPolicy(obs_dim, num_roles=4, full=True)
    b1 = AcquisitionOrientedHybridPolicy(obs_dim, num_roles=4, full=False)
    # Equalise common initialisation so the counterfactuals isolate validity,
    # not arbitrary sampled weight differences.
    b1.load_state_dict(full.state_dict())
    obs = torch.randn(batch, obs_dim)
    previous_action = torch.zeros(batch, 3)
    role = torch.tensor([0, 1, 2, 3, 2, 1])
    valid = torch.ones(batch, dtype=torch.bool)
    logits, progress, state = full.forward_step(obs, previous_action, valid, role)
    invalid = torch.zeros(batch, dtype=torch.bool)
    expired_a = obs.clone(); expired_b = obs.clone()
    expired_b[:, list(TARGET_HISTORY_INDICES)] += 10_000.0
    logits_a, _, state_a = full.forward_step(expired_a, previous_action, invalid, role, state)
    logits_b, _, state_b = full.forward_step(expired_b, previous_action, invalid, role, state)
    b1_logits, b1_progress, _ = b1.forward_step(obs, previous_action, valid, role)
    dist = TanhGaussianBernoulli(logits[..., :2], logits[..., 2:4], logits[..., 4])
    continuous, commit, old_lp = dist.sample()
    recomputed = dist.log_prob(continuous, commit)
    ratio = torch.exp(recomputed - old_lp)
    checks = {
        "legal_evidence_updates_target_memory": bool(torch.any(state.target.abs() > 0)),
        "expired_evidence_resets_target_memory": bool(torch.equal(state_a.target, torch.zeros_like(state_a.target))),
        "expired_payload_cannot_change_actor_output": bool(torch.allclose(logits_a, logits_b, atol=1e-6, rtol=0.0)),
        "expired_payload_cannot_change_target_memory": bool(torch.equal(state_a.target, state_b.target)),
        "full_b1_have_exact_parameter_match": count_params(full) == count_params(b1),
        "full_b1_use_same_legal_history_shapes": tuple(progress.shape) == tuple(b1_progress.shape),
        "hybrid_log_prob_is_exact_for_executed_action": bool(torch.allclose(old_lp, recomputed, atol=2e-5, rtol=2e-5)),
        "hybrid_ratio_is_finite": bool(torch.isfinite(ratio).all()),
        "full_b1_are_structurally_distinct": bool(not torch.allclose(logits, b1_logits)),
    }
    if not all(checks.values()):
        raise AssertionError(checks)
    payload = {
        "status": "M2_IMPLEMENTATION_INTERFACE_GATE_PASS",
        "performance_use_prohibited": True,
        "no_training": True,
        "full_parameters": count_params(full),
        "b1_parameters": count_params(b1),
        "parameter_relative_gap": 0.0,
        "target_history_indices": list(TARGET_HISTORY_INDICES),
        "checks": checks,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "M2_ACQUISITION_ORIENTED_INTERFACE_REPORT.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    for check in checks:
        print(f"PASS {check}")
    print(f"M2_ACQUISITION_ORIENTED_INTERFACE_REPORT: PASS ({len(checks)} tests)")


if __name__ == "__main__":
    main()
