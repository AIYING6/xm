"""Multi-split, multi-context stress audit for the ACFID shared interaction model."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from itertools import combinations
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from envs.acfid_compound_fault_env import ACTIONS, ACFIDCompoundFaultEnv, fault_sets
from scripts.p8b_acfid_shared_interaction_gate import fit_shared, predict_interaction, relative_gain


def build_seed_data(seed: int, contexts_count: int, rollouts: int):
    rng = np.random.default_rng(seed); env = ACFIDCompoundFaultEnv()
    contexts = [env.sample_context(rng) for _ in range(contexts_count)]
    noise = [rng.lognormal(0.0, 0.055, size=(rollouts, 2)) for _ in contexts]
    all_sets = [frozenset()] + fault_sets(1) + fault_sets(2) + fault_sets(3) + fault_sets(4)
    q = {(cid, faults): env.q_values(context, faults, noise[cid]) for cid, context in enumerate(contexts) for faults in all_sets}
    interactions = {}
    for cid in range(len(contexts)):
        for pair in fault_sets(2):
            a, b = tuple(pair)
            interactions[(cid, pair)] = {action: q[cid, pair][action] - q[cid, frozenset([a])][action]
                                         - q[cid, frozenset([b])][action] + q[cid, frozenset()][action]
                                         for action in ACTIONS}
    return contexts, all_sets, q, interactions


def evaluate(contexts, all_sets, q, interactions, train_pairs, ridge):
    models = {"type_only": fit_shared(interactions, contexts, train_pairs, False, ridge),
              "structured": fit_shared(interactions, contexts, train_pairs, True, ridge)}
    scores = {name: {order: [] for order in (2, 3, 4)} for name in ("additive", "type_only", "structured")}
    for cid, context in enumerate(contexts):
        q0 = q[cid, frozenset()]
        for faults in all_sets:
            order = len(faults)
            if order < 2 or (order == 2 and faults in train_pairs): continue
            additive = {action: q0[action] + sum(q[cid, frozenset([fault])][action] - q0[action] for fault in faults) for action in ACTIONS}
            estimates = {"additive": additive}
            for name, structured in (("type_only", False), ("structured", True)):
                estimate = dict(additive)
                for pair_tuple in combinations(sorted(faults), 2):
                    effect = predict_interaction(models[name], frozenset(pair_tuple), context, structured)
                    estimate = {action: estimate[action] + effect[action] for action in ACTIONS}
                estimates[name] = estimate
            oracle = max(q[cid, faults], key=q[cid, faults].get)
            for name, estimate in estimates.items():
                chosen = max(estimate, key=estimate.get)
                scores[name][order].append(q[cid, faults][oracle] - q[cid, faults][chosen])
    mean = {name: {order: float(np.mean(values)) for order, values in by_order.items()} for name, by_order in scores.items()}
    high_add = np.mean([mean["additive"][3], mean["additive"][4]])
    high_struct = np.mean([mean["structured"][3], mean["structured"][4]])
    return {
        "pair_regret_additive": mean["additive"][2], "pair_regret_type_only": mean["type_only"][2],
        "pair_regret_structured": mean["structured"][2],
        "pair_gain_over_additive": relative_gain(mean["additive"][2], mean["structured"][2]),
        "pair_gain_over_type_only": relative_gain(mean["type_only"][2], mean["structured"][2]),
        "higher_order_regret_ratio": float(high_struct / max(high_add, 1e-9)),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=ROOT / "configs/p8c_acfid_shared_interaction_stress_20260910.json")
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute: raise SystemExit("explicit --execute is required")
    if args.output_root.exists(): raise FileExistsError(f"refusing to overwrite {args.output_root}")
    cfg = json.loads(args.config.read_text(encoding="utf-8")); rows = []
    for seed in cfg["context_seeds"]:
        contexts, all_sets, q, interactions = build_seed_data(seed, cfg["contexts_per_seed"], cfg["noise_rollouts_per_action"])
        for split_id, raw_split in enumerate(cfg["pair_splits"], 1):
            train_pairs = {frozenset(pair) for pair in raw_split}
            row = evaluate(contexts, all_sets, q, interactions, train_pairs, cfg["ridge"])
            rows.append({"seed": seed, "split": split_id, **row})
    t = cfg["thresholds"]; total = len(rows)
    pair_fraction = np.mean([row["pair_gain_over_additive"] >= t["cell_pair_regret_gain_min"] for row in rows])
    structure_fraction = np.mean([row["pair_gain_over_type_only"] > 0.0 for row in rows])
    high_fraction = np.mean([row["higher_order_regret_ratio"] <= 1.05 for row in rows])
    seed_medians = {str(seed): float(np.median([row["pair_gain_over_additive"] for row in rows if row["seed"] == seed])) for seed in cfg["context_seeds"]}
    checks = {
        "pair_gain_replicates_across_cells": pair_fraction >= t["pair_regret_gain_pass_fraction_min"],
        "structure_replicates_over_type_only": structure_fraction >= t["structure_beats_type_only_fraction_min"],
        "higher_order_noninferiority_replicates": high_fraction >= t["higher_order_noninferior_fraction_min"],
        "median_pair_gain_is_material": np.median([row["pair_gain_over_additive"] for row in rows]) >= t["median_pair_regret_gain_min"],
        "every_context_seed_has_positive_median_gain": min(seed_medians.values()) >= t["minimum_seed_median_gain"],
    }
    checks = {key: bool(value) for key, value in checks.items()}
    verdict = "ACFID_P0C_STRESS_PASS" if all(checks.values()) else "ACFID_P0C_STRESS_STOP"
    payload = {"protocol": cfg["protocol"], "verdict": verdict, "checks": checks, "cells": total,
               "aggregate": {"pair_gain_pass_fraction": float(pair_fraction), "structure_win_fraction": float(structure_fraction),
                             "higher_order_noninferior_fraction": float(high_fraction),
                             "median_pair_regret_gain": float(np.median([r["pair_gain_over_additive"] for r in rows])),
                             "seed_median_pair_gains": seed_medians},
               "diagnostic_only": True, "environment_steps": 0, "ppo_updates": 0, "training_authorized": False}
    args.output_root.mkdir(parents=True)
    (args.output_root / "ACFID_P0C_STRESS_REPORT.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    with (args.output_root / "ACFID_P0C_STRESS_CELLS.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__": main()
