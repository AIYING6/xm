"""One-shot zero-training test of shared structured fault-interaction prediction."""
from __future__ import annotations

import argparse
import json
import sys
from itertools import combinations
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from envs.acfid_compound_fault_env import ACTIONS, FAULTS, ACFIDCompoundFaultEnv, fault_sets

TYPES = ("sense", "relay", "act")
TYPE_PAIRS = tuple((a, b) for i, a in enumerate(TYPES) for b in TYPES[i:])


def fault_parts(fault: str) -> tuple[str, int]:
    name, branch = fault.rsplit("_", 1)
    return name, int(branch)


def pair_features(pair: frozenset[str], context, structured: bool) -> np.ndarray:
    first, second = sorted(pair); type_a, branch_a = fault_parts(first); type_b, branch_b = fault_parts(second)
    type_key = tuple(sorted((type_a, type_b), key=TYPES.index))
    semantic = [1.0] + [float(type_key == key) for key in TYPE_PAIRS]
    if structured:
        same = float(branch_a == branch_b)
        branch_values = sorted({branch_a, branch_b})
        demand = [context.demand[b] for b in branch_values]; urgency = [context.urgency[b] for b in branch_values]
        local = [1.0, same, float(np.mean(demand)), float(np.ptp(demand) if len(demand) > 1 else 0.0),
                 float(np.mean(urgency)), float(np.ptp(urgency) if len(urgency) > 1 else 0.0),
                 context.cross_link, context.reserve]
    else:
        local = [1.0]
    return np.kron(np.asarray(semantic), np.asarray(local))


def fit_shared(records, contexts, train_pairs, structured: bool, ridge: float):
    x = np.stack([pair_features(pair, contexts[cid], structured) for cid, pair in records if pair in train_pairs])
    gram = x.T @ x + ridge * np.eye(x.shape[1])
    models = {}
    for action in ACTIONS:
        y = np.asarray([records[(cid, pair)][action] for cid, pair in records if pair in train_pairs])
        models[action] = np.linalg.solve(gram, x.T @ y)
    return models


def predict_interaction(models, pair, context, structured):
    x = pair_features(pair, context, structured)
    return {action: float(x @ models[action]) for action in ACTIONS}


def relative_gain(base: float, candidate: float) -> float:
    return (base - candidate) / max(abs(base), 1e-9)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=ROOT / "configs/p8b_acfid_shared_interaction_gate_20260910.json")
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute: raise SystemExit("explicit --execute is required")
    if args.output_root.exists(): raise FileExistsError(f"refusing to overwrite {args.output_root}")
    cfg = json.loads(args.config.read_text(encoding="utf-8")); rng = np.random.default_rng(cfg["seed"])
    env = ACFIDCompoundFaultEnv(); contexts = [env.sample_context(rng) for _ in range(cfg["contexts"])]
    noise = [rng.lognormal(0.0, 0.055, size=(cfg["noise_rollouts_per_action"], 2)) for _ in contexts]
    all_sets = [frozenset()] + fault_sets(1) + fault_sets(2) + fault_sets(3) + fault_sets(4)
    q = {(cid, faults): env.q_values(context, faults, noise[cid]) for cid, context in enumerate(contexts) for faults in all_sets}
    interactions = {}
    for cid in range(len(contexts)):
        for pair in fault_sets(2):
            a, b = tuple(pair)
            interactions[(cid, pair)] = {action: q[cid, pair][action] - q[cid, frozenset([a])][action]
                                         - q[cid, frozenset([b])][action] + q[cid, frozenset()][action]
                                         for action in ACTIONS}
    train_pairs = {frozenset(pair) for pair in cfg["training_pairs"]}
    structured = fit_shared(interactions, contexts, train_pairs, True, cfg["ridge"])
    type_only = fit_shared(interactions, contexts, train_pairs, False, cfg["ridge"])

    metrics = {name: {order: {"errors": [], "regrets": []} for order in (2, 3, 4)}
               for name in ("additive", "type_only", "structured")}
    for cid, context in enumerate(contexts):
        q0 = q[cid, frozenset()]
        for faults in all_sets:
            order = len(faults)
            if order < 2 or (order == 2 and faults in train_pairs): continue
            additive = {action: q0[action] + sum(q[cid, frozenset([f])][action] - q0[action] for f in faults) for action in ACTIONS}
            predictions = {"additive": additive}
            for name, model, use_structure in (("type_only", type_only, False), ("structured", structured, True)):
                estimate = dict(additive)
                for pair_tuple in combinations(sorted(faults), 2):
                    interaction = predict_interaction(model, frozenset(pair_tuple), context, use_structure)
                    estimate = {action: estimate[action] + interaction[action] for action in ACTIONS}
                predictions[name] = estimate
            oracle_action = max(q[cid, faults], key=q[cid, faults].get)
            for name, prediction in predictions.items():
                chosen = max(prediction, key=prediction.get)
                metrics[name][order]["errors"].append(np.mean([abs(prediction[a] - q[cid, faults][a]) for a in ACTIONS]))
                metrics[name][order]["regrets"].append(q[cid, faults][oracle_action] - q[cid, faults][chosen])
    summary = {name: {str(order): {"mae": float(np.mean(values["errors"])), "regret": float(np.mean(values["regrets"]))}
                      for order, values in by_order.items()} for name, by_order in metrics.items()}
    t = cfg["thresholds"]
    pair_add = summary["additive"]["2"]; pair_type = summary["type_only"]["2"]; pair_struct = summary["structured"]["2"]
    higher_add = np.mean([summary["additive"][str(o)]["regret"] for o in (3, 4)])
    higher_struct = np.mean([summary["structured"][str(o)]["regret"] for o in (3, 4)])
    checks = {
        "shared_structure_improves_pair_mae": relative_gain(pair_add["mae"], pair_struct["mae"]) >= t["heldout_pair_mae_gain_over_additive_min"],
        "shared_structure_improves_pair_regret": relative_gain(pair_add["regret"], pair_struct["regret"]) >= t["heldout_pair_regret_gain_over_additive_min"],
        "task_structure_beats_type_only": relative_gain(pair_type["regret"], pair_struct["regret"]) >= t["heldout_pair_regret_gain_over_type_only_min"],
        "higher_order_noninferior_to_additive": higher_struct <= t["higher_order_regret_ratio_max"] * higher_add,
    }
    checks = {key: bool(value) for key, value in checks.items()}
    verdict = "ACFID_SHARED_INTERACTION_GATE_PASS" if all(checks.values()) else "ACFID_SHARED_INTERACTION_GATE_STOP"
    payload = {"protocol": cfg["protocol"], "verdict": verdict, "checks": checks, "summary": summary,
               "gains": {"pair_mae_over_additive": relative_gain(pair_add["mae"], pair_struct["mae"]),
                         "pair_regret_over_additive": relative_gain(pair_add["regret"], pair_struct["regret"]),
                         "pair_regret_over_type_only": relative_gain(pair_type["regret"], pair_struct["regret"]),
                         "higher_order_regret_ratio": float(higher_struct / max(higher_add, 1e-9))},
               "diagnostic_only": True, "environment_steps": 0, "ppo_updates": 0, "training_authorized": False}
    args.output_root.mkdir(parents=True)
    (args.output_root / "ACFID_SHARED_INTERACTION_REPORT.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    (args.output_root / "ACFID_SHARED_INTERACTION_REPORT.md").write_text(
        f"# ACFID shared-interaction gate\n\n`{verdict}`\n\n" +
        "\n".join(f"- {key}: {'PASS' if value else 'FAIL'}" for key, value in checks.items()) +
        "\n\nNo policy training was performed.\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__": main()
