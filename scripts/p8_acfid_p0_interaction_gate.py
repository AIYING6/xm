"""Run the preregistered zero-training ACFID interaction gate."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from envs.acfid_compound_fault_env import ACTIONS, FAULTS, ACFIDCompoundFaultEnv, fault_sets


def features(faults: frozenset[str], second_order: bool) -> np.ndarray:
    main = [float(fault in faults) for fault in FAULTS]
    pair = [float(a in faults and b in faults) for i, a in enumerate(FAULTS) for b in FAULTS[i + 1:]]
    return np.asarray([1.0, *main, *(pair if second_order else [])])


def fit_predict(train, test, second_order: bool):
    models = {}
    for action in ACTIONS:
        x = np.stack([features(row["faults"], second_order) for row in train])
        y = np.asarray([row["q"][action] for row in train])
        models[action] = np.linalg.lstsq(x, y, rcond=1e-8)[0]
    output = []
    for row in test:
        prediction = {a: float(features(row["faults"], second_order) @ models[a]) for a in ACTIONS}
        best = max(prediction, key=prediction.get)
        oracle = max(row["q"], key=row["q"].get)
        output.append({"mae": np.mean([abs(prediction[a] - row["q"][a]) for a in ACTIONS]),
                       "regret": row["q"][oracle] - row["q"][best]})
    return float(np.mean([x["mae"] for x in output])), float(np.mean([x["regret"] for x in output]))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=ROOT / "configs/p8_acfid_p0_interaction_gate_20260910.json")
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("explicit --execute is required")
    if args.output_root.exists():
        raise FileExistsError(f"refusing to overwrite {args.output_root}")
    cfg = json.loads(args.config.read_text(encoding="utf-8")); threshold = cfg["thresholds"]
    rng = np.random.default_rng(cfg["seed"]); env = ACFIDCompoundFaultEnv()
    contexts = [env.sample_context(rng) for _ in range(cfg["contexts"])]
    noises = [rng.lognormal(0.0, 0.055, size=(cfg["noise_rollouts_per_action"], 2)) for _ in contexts]
    sets = [frozenset()] + fault_sets(1) + fault_sets(2) + fault_sets(3) + fault_sets(4)
    rows = []
    for context_id, (context, noise) in enumerate(zip(contexts, noises)):
        for faults in sets:
            rows.append({"context": context_id, "faults": faults, "q": env.q_values(context, faults, noise)})
    index = {(row["context"], row["faults"]): row for row in rows}

    pair_summary = []
    for pair in fault_sets(2):
        a, b = tuple(pair); interactions = []; rank_changes = 0
        for cid in range(len(contexts)):
            q0 = index[cid, frozenset()]["q"]; qa = index[cid, frozenset([a])]["q"]
            qb = index[cid, frozenset([b])]["q"]; qab = index[cid, pair]["q"]
            interaction = {action: qab[action] - qa[action] - qb[action] + q0[action] for action in ACTIONS}
            interactions.append(max(abs(value) for value in interaction.values()))
            additive = {action: qa[action] + qb[action] - q0[action] for action in ACTIONS}
            rank_changes += max(additive, key=additive.get) != max(qab, key=qab.get)
        pair_summary.append({"pair": "+".join(sorted(pair)), "mean_max_abs_interaction": float(np.mean(interactions)),
                             "rank_change_rate": rank_changes / len(contexts),
                             "dependency_distance": env.dependency_distance(a, b)})

    train_pairs = {frozenset(pair) for pair in cfg["training_pairs"]}
    train_sets = {frozenset()} | set(fault_sets(1)) | train_pairs
    train = [row for row in rows if row["faults"] in train_sets]
    heldout = [row for row in rows if len(row["faults"]) >= 2 and row["faults"] not in train_pairs]
    add_mae, add_regret = fit_predict(train, heldout, False)
    int_mae, int_regret = fit_predict(train, heldout, True)
    single_values = [max(index[cid, single]["q"].values()) for cid in range(len(contexts)) for single in fault_sets(1)]
    strong = [row for row in pair_summary if row["mean_max_abs_interaction"] >= threshold["G2_interaction_abs_min"]]
    decision = [row for row in pair_summary if row["rank_change_rate"] >= 0.05]
    same = np.mean([r["mean_max_abs_interaction"] for r in pair_summary if r["dependency_distance"] == 1])
    cross = np.mean([r["mean_max_abs_interaction"] for r in pair_summary if r["dependency_distance"] == 3])
    mae_gain = (add_mae - int_mae) / max(add_mae, 1e-9)
    regret_gain = (add_regret - int_regret) / max(add_regret, 1e-9)
    checks = {
        "G1_learnability": bool(np.mean(single_values) >= threshold["G1_single_optimal_value_min"] and np.mean(single_values) <= threshold["G1_single_optimal_value_max"]),
        "G2_nonadditivity": len(strong) >= threshold["G2_min_pairs"],
        "G3_decision_relevance": len(decision) >= threshold["G3_min_pairs"],
        "G4_additive_insufficiency": mae_gain >= threshold["G4_relative_mae_reduction_min"],
        "G5_low_order_generalization": regret_gain >= threshold["G5_relative_regret_reduction_min"],
        "G6_structural_alignment": same - cross >= threshold["G6_same_branch_excess_min"],
    }
    checks = {key: bool(value) for key, value in checks.items()}
    verdict = "ACFID_P0_PASS" if all(checks.values()) else "ACFID_P0_STOP"
    payload = {"protocol": cfg["protocol"], "verdict": verdict, "checks": checks,
               "metrics": {"single_optimal_value_mean": float(np.mean(single_values)), "strong_interaction_pairs": len(strong),
                           "decision_relevant_pairs": len(decision), "additive_mae": add_mae, "interaction_mae": int_mae,
                           "mae_relative_gain": mae_gain, "additive_regret": add_regret,
                           "interaction_regret": int_regret, "regret_relative_gain": regret_gain,
                           "same_branch_interaction": float(same), "cross_branch_interaction": float(cross)},
               "diagnostic_only": True, "environment_steps": 0, "ppo_updates": 0, "training_authorized": False}
    args.output_root.mkdir(parents=True)
    (args.output_root / "ACFID_P0_REPORT.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    with (args.output_root / "ACFID_P0_PAIR_INTERACTIONS.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(pair_summary[0])); writer.writeheader(); writer.writerows(pair_summary)
    (args.output_root / "ACFID_P0_REPORT.md").write_text(
        f"# ACFID P0 interaction gate\n\n`{verdict}`\n\n" +
        "\n".join(f"- {key}: {'PASS' if value else 'FAIL'}" for key, value in checks.items()) +
        "\n\nThis is a zero-training task-identifiability audit, not a learned-policy result.\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
