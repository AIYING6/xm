"""Audit deterministic fixed-endpoint and common-noise ACFID evaluation."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from algorithms.acfid_fixed_endpoint_evaluator import EvaluationCase, evaluate_fixed_endpoint
from algorithms.acfid_recovery_policy import ACFIDRecoveryPolicy, AdditiveRecoveryPolicy, DirectFaultAwareRecoveryPolicy
from envs.acfid_sequential_recovery_env import all_sets_of_orders


def hash_rows(rows) -> str:
    return hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--config", type=Path, default=ROOT / "configs/p8g_acfid_evaluator_audit_20260910.json"); parser.add_argument("--output-root", type=Path, required=True); parser.add_argument("--execute", action="store_true"); args = parser.parse_args()
    if not args.execute: raise SystemExit("explicit --execute required")
    if args.output_root.exists(): raise FileExistsError(f"refusing to overwrite {args.output_root}")
    cfg = json.loads(args.config.read_text(encoding="utf-8")); rng = np.random.default_rng(cfg["seed"])
    train_pairs = {frozenset(value) for value in cfg["train_pairs"]}; heldout = sorted(set(all_sets_of_orders(2, 3, 4)) - train_pairs, key=lambda x: (len(x), sorted(x)))
    cases = [EvaluationCase(int(rng.integers(2**31 - 1)), int(rng.integers(2**31 - 1)), faults) for faults in heldout for _ in range(cfg["cases_per_fault_set"])]
    torch.manual_seed(cfg["seed"]); models = {
        "direct_fault_aware": DirectFaultAwareRecoveryPolicy(7, 5, hidden=100),
        "additive": AdditiveRecoveryPolicy(7, 5, hidden=81),
        "acfid": ACFIDRecoveryPolicy(7, 5, 3, hidden=64),
    }
    before = {name: [p.detach().clone() for p in model.parameters()] for name, model in models.items()}
    outputs = {name: evaluate_fixed_endpoint(model, cases) for name, model in models.items()}
    repeat = evaluate_fixed_endpoint(models["acfid"], cases)
    tape_hashes = {name: hash_rows([{"context_seed": row["context_seed"], "noise_seed": row["noise_seed"], "faults": row["faults"]} for row in rows]) for name, rows in outputs.items()}
    unchanged = all(all(torch.equal(old, new) for old, new in zip(before[name], model.parameters())) for name, model in models.items())
    checks = {
        "evaluation_contains_only_heldout_combinations": all(frozenset(row["faults"].split("+")) in set(heldout) for row in outputs["acfid"]),
        "all_methods_share_exact_evaluation_tape": len(set(tape_hashes.values())) == 1,
        "evaluation_is_deterministic": outputs["acfid"] == repeat,
        "evaluation_does_not_update_parameters": unchanged,
        "regret_is_nonnegative": all(row["action_regret"] >= -1e-10 for rows in outputs.values() for row in rows),
        "oracle_and_selected_use_common_noise": all(row["oracle_value"] + 1e-10 >= row["selected_value"] for rows in outputs.values() for row in rows),
        "fixed_endpoint_is_preregistered": cfg["fixed_endpoint"] == 1000000,
        "test_is_reporting_only": "reporting only" in cfg["test_data_role"],
    }
    verdict = "ACFID_FIXED_ENDPOINT_EVALUATOR_PASS" if all(checks.values()) else "ACFID_FIXED_ENDPOINT_EVALUATOR_STOP"
    summary = {name: {"n": len(rows), "mean_regret": float(np.mean([r["action_regret"] for r in rows])), "success": float(np.mean([r["success"] for r in rows])), "timeout": float(np.mean([r["timeout"] for r in rows]))} for name, rows in outputs.items()}
    payload = {"protocol": cfg["protocol"], "verdict": verdict, "checks": checks, "metrics": {"heldout_fault_sets": len(heldout), "evaluation_cases": len(cases), "tape_sha256": next(iter(tape_hashes.values())), "untrained_smoke_summary_not_performance_evidence": summary}, "training_started": False, "full_pilot_authorized": False, "short_pilot_contract_freeze_authorized": verdict.endswith("PASS"), "next_gate": "P8H_SHORT_LEARNING_PILOT_CONTRACT_FREEZE"}
    args.output_root.mkdir(parents=True); (args.output_root / "ACFID_EVALUATOR_AUDIT.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8"); print(json.dumps(payload, indent=2))


if __name__ == "__main__": main()
