"""Preflight for temporal semantics, split isolation, and action learnability."""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from envs.acfid_compound_fault_env import ACTIONS, FAULTS, ACFIDCompoundFaultEnv
from envs.acfid_sequential_recovery_env import ACFIDSequentialConfig, ACFIDSequentialRecoveryEnv, all_sets_of_orders


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--config", type=Path, default=ROOT / "configs/p8e_acfid_sequential_preflight_20260910.json"); parser.add_argument("--output-root", type=Path, required=True); parser.add_argument("--execute", action="store_true"); args = parser.parse_args()
    if not args.execute: raise SystemExit("explicit --execute required")
    if args.output_root.exists(): raise FileExistsError(f"refusing to overwrite {args.output_root}")
    cfg = json.loads(args.config.read_text(encoding="utf-8")); rng = np.random.default_rng(cfg["seed"]); model = ACFIDCompoundFaultEnv()
    train_pairs = {frozenset(pair) for pair in cfg["train_pairs"]}; singles = set(all_sets_of_orders(1)); nominal = {frozenset()}
    train = nominal | singles | train_pairs; test = set(all_sets_of_orders(2, 3, 4)) - train_pairs
    env = ACFIDSequentialRecoveryEnv(ACFIDSequentialConfig(tuple(sorted(train, key=lambda x: (len(x), sorted(x)))), seed=cfg["seed"]))
    pre = env.reset(fault_set=next(iter(train_pairs))); pre_active = float(env._observation()["active_faults"].sum())
    env.step(0); env.step(0); detected = float(env._observation()["active_faults"].sum())
    state = env.runtime_state(); env.step(2); first = env.terminal_value; env.restore_runtime_state(state); env.step(2); clone_equal = first == env.terminal_value

    counts = Counter(); single_values = []; test_success = []; action_spreads = []
    for _ in range(cfg["contexts"]):
        context = model.sample_context(rng); noise = rng.lognormal(0.0, 0.055, size=(32, 2))
        for faults in list(train) + list(test):
            q = model.q_values(context, faults, noise); counts[max(q, key=q.get)] += 1
            if len(faults) == 1: single_values.append(max(q.values()))
            if faults in test: test_success.append(float(max(q.values()) >= 0.85))
            action_spreads.append(max(q.values()) - min(q.values()))
    total = sum(counts.values()); t = cfg["thresholds"]
    checks = {
        "train_test_fault_sets_disjoint": train.isdisjoint(test),
        "faults_hidden_before_detection": pre_active == 0.0,
        "primitive_signatures_visible_after_detection": detected == 2.0,
        "counterfactual_clone_is_exact": clone_equal,
        "all_recovery_actions_have_optimal_regions": all(counts[action] / total >= t["minimum_optimal_action_fraction"] for action in ACTIONS),
        "single_faults_are_nontrivial_and_nonsaturated": t["single_value_min"] <= float(np.mean(single_values)) <= t["single_value_max"],
        "heldout_combinations_are_not_global_success_or_failure": t["test_success_min"] <= float(np.mean(test_success)) <= t["test_success_max"],
        "recovery_actions_change_outcomes": float(np.mean(action_spreads)) >= t["action_effect_min"],
    }
    checks = {key: bool(value) for key, value in checks.items()}; verdict = "ACFID_SEQUENTIAL_PREFLIGHT_PASS" if all(checks.values()) else "ACFID_SEQUENTIAL_PREFLIGHT_STOP"
    payload = {"protocol": cfg["protocol"], "verdict": verdict, "checks": checks,
               "metrics": {"optimal_action_counts": dict(counts), "single_value_mean": float(np.mean(single_values)),
                           "heldout_oracle_success": float(np.mean(test_success)), "mean_action_value_spread": float(np.mean(action_spreads)),
                           "train_fault_sets": len(train), "test_fault_sets": len(test)},
               "training_started": False, "ppo_updates": 0, "training_authorized": False}
    args.output_root.mkdir(parents=True); (args.output_root / "ACFID_SEQUENTIAL_PREFLIGHT.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8"); print(json.dumps(payload, indent=2))


if __name__ == "__main__": main()
