"""Counterfactual decision-relevance audit in the native six-UAV V3.1 task."""
from __future__ import annotations

import argparse
import csv
import itertools
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from envs.redundant_topology_uav_env import RedundantTopologyConfig
from envs.sustained_support_topology_uav_env import SustainedSupportTopologyConfig
from envs.sustained_support_topology_uav_v31_env import SustainedSupportTopologyV31UAVEnv


def make_env(seed: int, cfg: dict) -> SustainedSupportTopologyV31UAVEnv:
    base = RedundantTopologyConfig(
        scouts=2, relays=2, terminals=2, deadline_steps=cfg["deadline_steps"],
        scout_sense_range=120.0, relay_radio_range=70.0, terminal_speed=10.0,
        tau_max=1, comm_dropout=cfg["comm_dropout"], assignment_observation=True,
        scout_assignment_observation=True, seed_env=seed, seed_comm=seed + 100000,
        seed_topology=seed + 200000,
    )
    return SustainedSupportTopologyV31UAVEnv(SustainedSupportTopologyConfig(base=base, fault_transition=cfg["fault_transition"]))


def actor_legal_continuation(env: SustainedSupportTopologyV31UAVEnv) -> np.ndarray:
    """Deterministic continuation using action masks and role-local assignments only."""
    masks = env.graph_observation()["action_masks"]; actions = np.zeros(env.n, dtype=np.int64)
    for agent in range(env.n):
        legal = np.flatnonzero(masks[agent] > 0)
        positive = legal[legal > 0]
        if len(positive): actions[agent] = int(positive[(env.step_count + agent) % len(positive)])
    return actions


def rollout_from(env, state, first_action) -> tuple[float, bool, bool]:
    env.load_runtime_state_dict(state); total = 0.0
    _, _, _, reward, _, info = env.step(np.asarray(first_action, dtype=np.int64)); total += float(reward[0, 0])
    while not env.done:
        _, _, _, reward, _, info = env.step(actor_legal_continuation(env)); total += float(reward[0, 0])
    return total, bool(info["success"]), bool(info["timeout"])


def q_vector(seed, faults, actions, cfg):
    env = make_env(seed, cfg); env.reset(); env.step(actor_legal_continuation(env)); env.set_failure(edges=faults)
    state = env.runtime_state_dict(); values = []; outcomes = []
    for action in actions:
        value, success, timeout = rollout_from(env, state, action); values.append(value); outcomes.append((success, timeout))
    return np.asarray(values), outcomes


def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--config", type=Path, default=ROOT / "configs/p8j_real_v31_compound_decision_audit_20260910.json"); parser.add_argument("--output-root", type=Path, required=True); parser.add_argument("--execute", action="store_true"); args = parser.parse_args()
    if not args.execute: raise SystemExit("explicit --execute required")
    if args.output_root.exists(): raise FileExistsError(f"refusing to overwrite {args.output_root}")
    cfg = json.loads(args.config.read_text(encoding="utf-8")); primitives = [tuple(x) for x in cfg["primitive_edges"]]
    actions = list(itertools.product(range(3), repeat=6)); rows = []
    for seed in cfg["seeds"]:
        nominal, _ = q_vector(seed, [], actions, cfg); singles = {edge: q_vector(seed, [edge], actions, cfg)[0] for edge in primitives}
        for first, second in itertools.combinations(primitives, 2):
            actual, outcomes = q_vector(seed, [first, second], actions, cfg); additive = singles[first] + singles[second] - nominal
            predicted = int(np.argmax(additive)); oracle = int(np.argmax(actual)); regret = float(actual[oracle] - actual[predicted])
            rows.append({"seed": seed, "first": str(first), "second": str(second), "oracle_action": str(actions[oracle]), "additive_action": str(actions[predicted]), "oracle_value": float(actual[oracle]), "additive_selected_value": float(actual[predicted]), "additive_action_regret": regret, "decision_relevant": int(regret >= cfg["thresholds"]["decision_relevant_regret"]), "oracle_success": int(outcomes[oracle][0]), "oracle_timeout": int(outcomes[oracle][1])})
    relevant = float(np.mean([row["decision_relevant"] for row in rows])); median_regret = float(np.median([row["additive_action_regret"] for row in rows])); recoverable = float(np.mean([row["oracle_success"] for row in rows])); t = cfg["thresholds"]
    checks = {"native_runtime_clone_available": True, "native_joint_action_enumerated_exactly": len(actions) == 729, "compound_faults_use_only_legal_native_edges": all(tuple(edge) in make_env(cfg["seeds"][0], cfg).legal_edges() for edge in primitives), "decision_relevant_compound_fraction": relevant >= t["minimum_decision_relevant_pair_fraction"], "additive_policy_regret_is_material": median_regret >= t["minimum_median_additive_action_regret"], "compound_cases_are_partly_recoverable": t["minimum_recoverable_pair_fraction"] <= recoverable <= t["maximum_recoverable_pair_fraction"]}
    verdict = "REAL_V31_COMPOUND_DECISION_GAP_PASS" if all(checks.values()) else "REAL_V31_COMPOUND_DECISION_GAP_STOP"
    payload = {"protocol": cfg["protocol"], "verdict": verdict, "checks": checks, "metrics": {"joint_actions": len(actions), "pair_cases": len(rows), "decision_relevant_pair_fraction": relevant, "median_additive_action_regret": median_regret, "mean_additive_action_regret": float(np.mean([r["additive_action_regret"] for r in rows])), "oracle_recoverable_pair_fraction": recoverable}, "training_started": False, "method_implemented": False}
    args.output_root.mkdir(parents=True)
    with (args.output_root / "P8J_PAIR_CASES.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    (args.output_root / "P8J_REAL_V31_COMPOUND_AUDIT.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8"); print(json.dumps(payload, indent=2))


if __name__ == "__main__": main()
