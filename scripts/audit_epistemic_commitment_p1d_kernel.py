"""Audit the P1D commitment kernel without training or PPO integration."""

from __future__ import annotations

import argparse
import inspect
import json
from pathlib import Path
import sys

import numpy as np
import torch


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from algorithms.epistemic_commitment import (
    CapacityMatchedRecurrentActor,
    CommitmentActorConfig,
    InformationSetCommitmentActor,
    MODE_COMMIT,
    MODE_DEFER,
    MODE_FALLBACK,
    MODE_NAMES,
    parameter_count,
    select_robust_mode,
)
from envs.epistemic_commitment_uav_shadow_env import EpistemicCommitmentUAVShadowEnv


def run_kernel_audit(seed: int = 20260909) -> dict:
    torch.manual_seed(seed)
    config = CommitmentActorConfig(input_dim=37, hidden_dim=32)
    candidate = InformationSetCommitmentActor(config)
    baseline = CapacityMatchedRecurrentActor(config)

    delivered = EpistemicCommitmentUAVShadowEnv(True, seed).actor_observation()[0]
    lost = EpistemicCommitmentUAVShadowEnv(False, seed).actor_observation()[0]
    delivered_history = torch.as_tensor(delivered, dtype=torch.float32).reshape(1, 1, -1)
    lost_history = torch.as_tensor(lost, dtype=torch.float32).reshape(1, 1, -1)
    candidate.eval()
    with torch.no_grad():
        delivered_output = candidate(delivered_history)
        lost_output = candidate(lost_history)

    endpoint_values = torch.tensor(
        [[[-8.0, 10.0], [1.0, 5.0], [2.0, 2.0]]], dtype=torch.float32
    )
    intervals = {
        "low": torch.tensor([[0.10, 0.20]], dtype=torch.float32),
        "middle": torch.tensor([[0.40, 0.50]], dtype=torch.float32),
        "high": torch.tensor([[0.80, 0.90]], dtype=torch.float32),
    }
    decisions: dict[str, dict] = {}
    for name, interval in intervals.items():
        mode, values = select_robust_mode(endpoint_values, interval)
        decisions[name] = {
            "interval": interval[0].tolist(),
            "mode": MODE_NAMES[int(mode.item())],
            "robust_values": values[0].tolist(),
        }

    forward_parameters = set(inspect.signature(candidate.forward).parameters)
    forbidden = {"delivered", "delivery", "ack", "share_obs", "teammate_belief", "global_state"}
    candidate_count = parameter_count(candidate)
    baseline_count = parameter_count(baseline)
    checks = {
        "leader_input_exact_across_delivery_states": bool(np.array_equal(delivered, lost)),
        "candidate_output_exact_for_identical_legal_history": all(
            torch.equal(delivered_output[key], lost_output[key])
            for key in ("interval", "endpoint_values", "mode_values", "mode")
        ),
        "forward_interface_contains_no_hidden_truth": not bool(forward_parameters & forbidden),
        "probability_intervals_valid": all(
            bool(torch.all(interval[:, 0] <= interval[:, 1]))
            and bool(torch.all(interval >= 0.0))
            and bool(torch.all(interval <= 1.0))
            for interval in intervals.values()
        ),
        "counterfactual_low_prior_selects_fallback": decisions["low"]["mode"] == MODE_NAMES[MODE_FALLBACK],
        "counterfactual_middle_prior_selects_defer": decisions["middle"]["mode"] == MODE_NAMES[MODE_DEFER],
        "counterfactual_high_prior_selects_commit": decisions["high"]["mode"] == MODE_NAMES[MODE_COMMIT],
        "candidate_and_recurrent_baseline_parameter_counts_exact": candidate_count == baseline_count,
        "candidate_decision_uses_interval_values": "smooth_robust_mode_values" in inspect.getsource(candidate.forward),
        "baseline_decision_is_direct_recurrent_policy": "mode_logits" in inspect.getsource(baseline.forward),
        "all_matched_baseline_head_outputs_affect_decision": bool(
            torch.all(torch.any(baseline.mode_projection != 0.0, dim=0))
        ),
    }
    passed = all(checks.values())
    return {
        "protocol": "EPISTEMIC-COMMITMENT-P1D-KERNEL-AUDIT-V1",
        "verdict": "P1D_COMMITMENT_KERNEL_AUDIT_PASS" if passed else "P1D_COMMITMENT_KERNEL_AUDIT_FAIL",
        "checks": checks,
        "parameter_counts": {"candidate": candidate_count, "matched_recurrent": baseline_count},
        "counterfactual_decisions": decisions,
        "actor_forward_parameters": sorted(forward_parameters),
        "evidence_boundary": (
            "This audit validates the isolated decision kernel, legal interface, analytic decision ordering, "
            "and exact parameter-count match. It does not validate calibration, PPO integration, learnability, "
            "or empirical advantage."
        ),
        "training_started": False,
        "environment_steps": 0,
        "ppo_updates": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = run_kernel_audit()
    payload = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(payload + "\n")
    print(payload)
    if report["verdict"].endswith("FAIL"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
