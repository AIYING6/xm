"""Predeclared audit for the frozen V8 relation-value development pilot.

This gate distinguishes structural candidate evidence from formal performance
evidence. It neither pools endpoint episodes as training replicates nor turns
development pilot output into a paper claim.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "configs" / "commitment_handoff_v8_relation_value_g3_pilot_freeze_20260914.json"
PROFILES = ("current_compact", "current_delayed", "future_fresh", "future_durable")
CURRENT = set(PROFILES[:2])
FUTURE = set(PROFILES[2:])


def load_arm(seed_dir: Path, arm: str, spec: dict[str, object], task: dict[str, object]) -> dict[str, object]:
    manifest = json.loads((seed_dir / "run_manifest.json").read_text(encoding="utf-8"))
    if int(manifest["seed"]) <= 0 or manifest.get("status") != "completed":
        raise ValueError(f"incomplete run: {seed_dir}")
    relation_mode = manifest.get("relation_value_mode", manifest.get("fixed_task", {}).get("relation_value_mode"))
    if relation_mode != spec["relation_value_mode"]:
        raise ValueError(f"wrong relation mode in {seed_dir}")
    if int(manifest.get("fixed_task", {}).get("branch_step", -1)) != int(task["branch_step"]):
        raise ValueError(f"wrong V8 branch task in {seed_dir}")
    if manifest.get("fixed_task", {}).get("commitment_decision_mode") != "branch_value_v8":
        raise ValueError(f"wrong commitment mode in {seed_dir}")
    endpoint = json.loads((seed_dir / "profile_stratified_endpoint.json").read_text(encoding="utf-8"))
    summary = endpoint.get("summary", {})
    if set(summary) != set(PROFILES):
        raise ValueError(f"incomplete endpoint profiles in {seed_dir}")
    return summary


def metrics(summary: dict[str, object]) -> dict[str, float]:
    success = np.asarray([float(summary[p]["success_rate"]) for p in PROFILES])
    timeout = np.asarray([float(summary[p]["timeout_rate"]) for p in PROFILES])
    collision = np.asarray([float(summary[p]["collision_rate"]) for p in PROFILES])
    choices = {p: float(summary[p]["mean_branch_decision_reconstruct"]) for p in PROFILES}
    correctness = [1.0 - choices[p] if p in CURRENT else choices[p] for p in PROFILES]
    return {
        "balanced_success": float(np.mean(success)),
        "balanced_timeout": float(np.mean(timeout)),
        "balanced_collision": float(np.mean(collision)),
        "directional_branch_accuracy": float(np.mean(correctness)),
        "current_mean_reconstruct": float(np.mean([choices[p] for p in CURRENT])),
        "future_mean_reconstruct": float(np.mean([choices[p] for p in FUTURE])),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pilot-root", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("pass --execute")
    if args.out_dir.exists():
        raise FileExistsError(f"refusing to overwrite {args.out_dir}")
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    copied = json.loads((args.pilot_root / "pilot_freeze_contract.json").read_text(encoding="utf-8"))
    if copied != contract:
        raise ValueError("pilot contract differs from the maintained frozen G3 contract")

    per_seed: dict[str, dict[str, object]] = {}
    for seed in contract["training_seeds"]:
        arm_metrics = {}
        for arm, spec in contract["arms"].items():
            summary = load_arm(args.pilot_root / arm / f"seed{seed}", arm, spec, contract["frozen_task"])
            arm_metrics[arm] = metrics(summary)
        plain = arm_metrics["plain_mlp_capacity_matched"]
        aligned = arm_metrics["relation_value_aligned"]
        shuffled = arm_metrics["relation_value_semantic_shuffle"]
        reliability_signal = (
            aligned["balanced_success"] - plain["balanced_success"] >= 0.10
            or aligned["balanced_timeout"] - plain["balanced_timeout"] <= -0.10
        ) and aligned["balanced_collision"] - plain["balanced_collision"] <= 0.05
        semantic_degradation = (
            aligned["directional_branch_accuracy"] - shuffled["directional_branch_accuracy"] >= 0.15
            or aligned["balanced_success"] - shuffled["balanced_success"] >= 0.10
        )
        per_seed[str(seed)] = {
            "arms": arm_metrics,
            "plain_is_intermediate": bool(0.10 <= plain["balanced_success"] <= 0.90),
            "aligned_directional_behavior": bool(aligned["directional_branch_accuracy"] >= 0.75),
            "candidate_control_reliability_signal": bool(reliability_signal),
            "semantic_shuffle_degradation": bool(semantic_degradation),
        }

    gate = contract["predeclared_gate"]
    aligned_directional = sum(cell["aligned_directional_behavior"] for cell in per_seed.values()) >= 2
    reliability = sum(cell["candidate_control_reliability_signal"] for cell in per_seed.values()) >= gate["minimum_seeds_showing_candidate_control_reliability_signal"]
    semantic = sum(cell["semantic_shuffle_degradation"] for cell in per_seed.values()) >= gate["minimum_seeds_showing_semantic_shuffle_degradation"]
    ordinary_intermediate = all(cell["plain_is_intermediate"] for cell in per_seed.values())
    passed = all((aligned_directional, reliability, semantic, ordinary_intermediate))
    report = {
        "protocol": "COMMITMENT-HANDOFF-3D-V8-RELATION-VALUE-G3-PILOT-AUDIT-V1",
        "artifact_class": "DEVELOPMENT_ONLY_CANDIDATE_IDENTIFICATION_GATE",
        "paper_evidence": False,
        "training_seeds": contract["training_seeds"],
        "per_seed": per_seed,
        "requirements": {
            "aligned_candidate_has_directional_public_branch_behavior_in_at_least_two_seeds": aligned_directional,
            "candidate_has_predeclared_control_reliability_signal_in_at_least_two_seeds": reliability,
            "semantic_shuffle_degrades_candidate_signal_in_at_least_two_seeds": semantic,
            "capacity_matched_plain_control_remains_intermediate_in_all_seeds": ordinary_intermediate,
        },
        "does_not_establish": [
            "a formal performance effect or a paper-ready effect size",
            "generalization beyond this frozen V8 task",
            "causal necessity of every relation-head operation beyond the registered semantic shuffle",
        ],
        "verdict": "V8_G3_CANDIDATE_IDENTIFICATION_PASS" if passed else "V8_G3_CANDIDATE_IDENTIFICATION_NOT_ESTABLISHED",
    }
    args.out_dir.mkdir(parents=True)
    (args.out_dir / "v8_g3_pilot_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
