"""Training-free technical audit for the frozen TC-SAM-UTR implementation.

This module deliberately constructs only synthetic PPO batches.  It neither
creates an environment evaluation tape nor calls ``env.step`` / a training
rollout.  The JSON artifact is a provenance record for D0, not experiment data.
"""
from __future__ import annotations

import copy
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.simple_ri_gmappo import make_optimizer, update_policy
from tests.test_tc_sam import agent, batch, config, parameters


def _run_pytest(*paths: str) -> dict:
    command = [sys.executable, "-m", "pytest", "-q", *paths]
    completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    return {
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
        "passed": completed.returncode == 0,
    }


def _max_parameter_difference(left: torch.nn.Module, right: torch.nn.Module) -> float:
    return max(float((a.detach() - b.detach()).abs().max()) for a, b in zip(left.parameters(), right.parameters()))


def _rho_zero_equivalence() -> dict:
    torch.manual_seed(601)
    utr, sam = agent(), agent()
    sam.load_state_dict(utr.state_dict())
    utr_cfg = config(sam_enabled=False)
    sam_cfg = config(sam_enabled=True, rho=0.0)
    torch.manual_seed(602)
    update_policy(utr, make_optimizer(utr, utr_cfg), copy.deepcopy(batch()), utr_cfg, torch.device("cpu"), 1)
    torch.manual_seed(602)
    sam_info = update_policy(sam, make_optimizer(sam, sam_cfg), copy.deepcopy(batch()), sam_cfg, torch.device("cpu"), 1)
    return {
        "max_abs_parameter_difference": _max_parameter_difference(utr, sam),
        "sam_perturbation_norm": float(sam_info["sam_perturbation_norm"]),
        "tolerance": 2.0e-6,
    }


def _sam_update_audit() -> dict:
    torch.manual_seed(603)
    model = agent()
    cfg = config(sam_enabled=True, rho=0.05)
    optimizer = make_optimizer(model, cfg)
    before = parameters(model)
    info = update_policy(model, optimizer, copy.deepcopy(batch()), cfg, torch.device("cpu"), 1)
    after = parameters(model)
    rows = info["actor_gradient_rows"]
    states = [int(state["step"].item()) for state in optimizer.state.values() if "step" in state]
    return {
        "parameter_count": sum(parameter.numel() for parameter in model.parameters()),
        "sam_rho": cfg.sam_rho,
        "sam_epsilon": cfg.sam_epsilon,
        "reported_perturbation_norm": float(info["sam_perturbation_norm"]),
        "perturbation_relative_error": abs(float(info["sam_perturbation_norm"]) - cfg.sam_rho) / cfg.sam_rho,
        "first_gradient_norm": float(info["sam_first_gradient_norm"]),
        "second_gradient_norm": float(info["sam_second_gradient_norm"]),
        "actor_parameters_changed_after_single_update": any(not torch.equal(a, b) for a, b in zip(before, after)),
        "optimizer_state_steps": sorted(set(states)),
        "all_values_finite": all(np.isfinite(float(value)) for value in info.values() if isinstance(value, (int, float))),
        "stratified_actor_samples": {
            "nominal": int(info["actor_nominal_sample_count"]),
            "failure": int(info["actor_failure_sample_count"]),
        },
        "same_minibatch_hash_for_both_sam_passes": all(
            row["sam_first_minibatch_hash"]
            and row["sam_first_minibatch_hash"] == row["sam_second_minibatch_hash"]
            for row in rows
        ),
        "sam_gradient_rows": len(rows),
    }


def _synthetic_compute_multiplier() -> dict:
    # This is deliberately a CPU-only local proxy.  It quantifies the extra
    # backward pass but is not represented as a cloud/GPU wall-time forecast.
    elapsed = {}
    for enabled, label in ((False, "utr"), (True, "tc_sam")):
        trials = []
        for trial in range(3):
            torch.manual_seed(700 + trial)
            model = agent()
            cfg = config(sam_enabled=enabled)
            optimizer = make_optimizer(model, cfg)
            start = time.perf_counter()
            update_policy(model, optimizer, copy.deepcopy(batch()), cfg, torch.device("cpu"), 1)
            trials.append(time.perf_counter() - start)
        elapsed[label] = trials
    utr_mean = float(np.mean(elapsed["utr"]))
    sam_mean = float(np.mean(elapsed["tc_sam"]))
    return {
        "scope": "synthetic_cpu_one_update_only_not_training_or_rollout",
        "utr_seconds": elapsed["utr"],
        "tc_sam_seconds": elapsed["tc_sam"],
        "utr_mean_seconds": utr_mean,
        "tc_sam_mean_seconds": sam_mean,
        "observed_multiplier": sam_mean / utr_mean,
    }


def _static_contract_audit() -> dict:
    source = (ROOT / "algorithms/ri_gmappo/simple_ri_gmappo.py").read_text(encoding="utf-8")
    sam_start = source.index("if sam_enabled:", source.index("def _update_policy_conditioned_actor"))
    sam_end = source.index("        else:\n            nominal_gradients", sam_start)
    sam_block = source[sam_start:sam_end]
    return {
        "sam_is_actor_only": "actor_parameters = [parameter for parameter in agent.actor.parameters()" in source and "(cfg.value_coef * value_loss).backward()" in source,
        "sam_reuses_same_minibatch_indices": "obs[mb]" in sam_block and "mb.detach().cpu().numpy().tobytes()" in sam_block,
        "sam_restores_exact_parameter_copies": "_restore_parameter_copies(actor_parameters, base_parameters)" in sam_block,
        "sam_has_no_optimizer_step_in_first_pass": "optimizer.step()" not in sam_block,
        "no_drtp_adaptive_state_in_sam_block": not any(token in sam_block.lower() for token in (
            "drtp", "difficulty", "sampler.q", "completed_return", "adaptive sampling",
        )),
        "logging_has_sam_norms_and_hashes": all(token in source for token in (
            "sam_first_gradient_norm", "sam_perturbation_norm", "sam_second_gradient_norm",
            "sam_first_minibatch_hash", "sam_second_minibatch_hash",
        )),
    }


def main() -> None:
    output_dir = ROOT / "artifacts" / "tc_sam_d0"
    output_dir.mkdir(parents=True, exist_ok=True)
    result = {
        "audit": "TC-SAM-D0",
        "training_or_rollout_started": False,
        "evaluation_tape_created": False,
        "tests": {
            "tc_sam_unit": _run_pytest("tests/test_tc_sam.py"),
            "actor_information_boundary_no_step": _run_pytest("tests/test_phase2h_information_boundary.py"),
        },
        "rho_zero_equivalence": _rho_zero_equivalence(),
        "sam_update": _sam_update_audit(),
        "synthetic_compute": _synthetic_compute_multiplier(),
        "static_contract": _static_contract_audit(),
    }
    result["overall_pass"] = (
        all(test["passed"] for test in result["tests"].values())
        and result["rho_zero_equivalence"]["max_abs_parameter_difference"] <= result["rho_zero_equivalence"]["tolerance"]
        and result["sam_update"]["parameter_count"] == 116_728
        and result["sam_update"]["perturbation_relative_error"] <= 1e-5
        and result["sam_update"]["same_minibatch_hash_for_both_sam_passes"]
        and result["sam_update"]["optimizer_state_steps"] == [1]
        and result["sam_update"]["all_values_finite"]
        and all(result["static_contract"].values())
    )
    output_path = output_dir / "tc_sam_d0_audit.json"
    output_path.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"overall_pass": result["overall_pass"], "artifact": str(output_path)}, indent=2))
    if not result["overall_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
