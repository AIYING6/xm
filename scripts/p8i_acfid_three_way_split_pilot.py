"""Three-way split pilot for identifiable ACFID compositional evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from itertools import combinations, cycle
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torch.distributions import Categorical

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from algorithms.acfid_clipped_ppo import InvariantRecoveryCritic, PPOBatch, ppo_loss
from algorithms.acfid_fixed_endpoint_evaluator import EvaluationCase, evaluate_fixed_endpoint
from algorithms.acfid_recovery_policy import ACFIDRecoveryPolicy, AdditiveRecoveryPolicy, DirectFaultAwareRecoveryPolicy
from envs.acfid_compound_fault_env import ACTIONS, FAULTS, ACFIDCompoundFaultEnv
from envs.acfid_sequential_recovery_env import ACFIDSequentialRecoveryEnv, all_sets_of_orders


def build_policy(name, hidden):
    if name == "direct_fault_aware": return DirectFaultAwareRecoveryPolicy(7, 5, hidden=hidden)
    if name == "additive": return AdditiveRecoveryPolicy(7, 5, hidden=hidden)
    if name == "acfid": return ACFIDRecoveryPolicy(7, 5, 3, hidden=hidden)
    raise ValueError(name)


def tensors(contexts, fault_sets):
    context = torch.tensor([[*c.demand, *c.urgency, c.cross_link, c.reserve, 5 / 7] for c in contexts], dtype=torch.float32)
    descriptors = torch.tensor(ACFIDSequentialRecoveryEnv.fault_descriptors(), dtype=torch.float32)
    faults = descriptors[None].expand(len(contexts), -1, -1).clone()
    active = torch.tensor([[float(fault in value) for fault in FAULTS] for value in fault_sets], dtype=torch.float32)
    relations = torch.tensor(ACFIDSequentialRecoveryEnv.pair_relations(), dtype=torch.float32)[None].expand(len(contexts), -1, -1, -1).clone()
    return context, faults, active, relations


def cases(seed, support, per_set, offset):
    rng = np.random.default_rng(seed + offset)
    return [EvaluationCase(int(rng.integers(2**31 - 1)), int(rng.integers(2**31 - 1)), faults) for faults in support for _ in range(per_set)]


def mean_regret(policy, evaluation_cases):
    rows = evaluate_fixed_endpoint(policy, evaluation_cases)
    return float(np.mean([row["action_regret"] for row in rows]))


class NoInteractionView(nn.Module):
    def __init__(self, policy): super().__init__(); self.policy = policy
    def forward(self, context, fault_features, active, pair_relations):
        return AdditiveRecoveryPolicy.forward(self.policy, context, fault_features, active, pair_relations)


def train(method, hidden, cfg, seed, support):
    torch.manual_seed(seed); policy = build_policy(method, hidden); critic = InvariantRecoveryCritic(7, 5)
    optimizer = torch.optim.Adam([*policy.parameters(), *critic.parameters()], lr=cfg["learning_rate"]); simulator = ACFIDCompoundFaultEnv(); entropy = 0.0
    for update in range(cfg["updates"]):
        rng = np.random.default_rng(seed * 1000 + update); fault_sets = [value for _, value in zip(range(cfg["rollout_samples_per_update"]), cycle(support))]
        context_seeds = rng.integers(2**31 - 1, size=len(fault_sets)); noise_seeds = rng.integers(2**31 - 1, size=len(fault_sets))
        contexts = [simulator.sample_context(np.random.default_rng(int(value))) for value in context_seeds]; x = tensors(contexts, fault_sets)
        with torch.no_grad():
            distribution = Categorical(logits=policy(*x)); torch.manual_seed(seed * 100000 + update)
            actions = distribution.sample(); old_log_prob = distribution.log_prob(actions); values = critic(x[0], x[1], x[2])
        returns = torch.tensor([simulator.value(c, f, ACTIONS[int(a)], np.random.default_rng(int(ns)).lognormal(0, .055, size=2)) for c, f, a, ns in zip(contexts, fault_sets, actions, noise_seeds)], dtype=torch.float32)
        batch = PPOBatch(*x, actions, old_log_prob, returns, returns - values)
        for _ in range(cfg["ppo_epochs"]):
            optimizer.zero_grad(); loss, metrics = ppo_loss(policy, critic, batch, cfg["clip_ratio"], cfg["value_coef"], cfg["entropy_coef"]); loss.backward()
            torch.nn.utils.clip_grad_norm_([*policy.parameters(), *critic.parameters()], cfg["gradient_norm_max"]); optimizer.step(); entropy = metrics["entropy"]
    return policy, entropy


def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--config", type=Path, default=ROOT / "configs/p8i_acfid_three_way_split_pilot_20260910.json"); parser.add_argument("--output-root", type=Path, required=True); parser.add_argument("--execute", action="store_true"); args = parser.parse_args()
    if not args.execute: raise SystemExit("explicit --execute required")
    if args.output_root.exists(): raise FileExistsError(f"refusing to overwrite {args.output_root}")
    cfg = json.loads(args.config.read_text(encoding="utf-8")); train_pairs = {frozenset(x) for x in cfg["training_pairs"]}; dev = {frozenset(x) for x in cfg["development_pairs"]}; sealed_pairs = {frozenset(x) for x in cfg["sealed_pairs"]}
    remaining = [tuple(x) for x in combinations(FAULTS, 2) if frozenset(x) not in train_pairs]
    ranked = sorted(remaining, key=lambda x: hashlib.sha256((cfg["split_salt"] + "|" + "+".join(x)).encode()).hexdigest())
    split_exact = {frozenset(x) for x in ranked[:4]} == dev and {frozenset(x) for x in ranked[4:]} == sealed_pairs
    support = sorted({frozenset(), *all_sets_of_orders(1), *train_pairs}, key=lambda x: (len(x), sorted(x))); sealed = sealed_pairs | set(all_sets_of_orders(*cfg["sealed_higher_orders"]))
    results = {}
    for seed in cfg["seeds"]:
        train_cases = cases(seed, support, cfg["train_validation_cases_per_set"], 700000); dev_cases = cases(seed, sorted(dev, key=lambda x: sorted(x)), cfg["development_cases_per_pair"], 800000)
        row = {}; models = {}
        for method, spec in cfg["methods"].items():
            models[method], entropy = train(method, spec["hidden"], cfg, seed, support)
            row[method] = {"train_regret": mean_regret(models[method], train_cases), "development_regret": mean_regret(models[method], dev_cases), "final_entropy": entropy}
        row["acfid_no_interaction"] = {"development_regret": mean_regret(NoInteractionView(models["acfid"]), dev_cases)}; results[str(seed)] = row
    rules = cfg["pass_rules"]
    acfid_better = sum((row["additive"]["development_regret"] - row["acfid"]["development_regret"]) / max(row["additive"]["development_regret"], 1e-8) >= rules["minimum_acfid_vs_additive_relative_regret_gain"] for row in results.values())
    direct_noninferior = sum(row["acfid"]["development_regret"] <= row["direct_fault_aware"]["development_regret"] + rules["direct_noninferiority_absolute_regret_margin"] for row in results.values())
    interaction = sum((row["acfid_no_interaction"]["development_regret"] - row["acfid"]["development_regret"]) / max(row["acfid_no_interaction"]["development_regret"], 1e-8) >= rules["interaction_ablation_relative_regret_gain"] for row in results.values())
    train_noninferior = sum(row["acfid"]["train_regret"] <= row["additive"]["train_regret"] + rules["train_support_noninferiority_margin"] for row in results.values())
    checks = {"hash_split_matches_frozen_contract": split_exact, "three_support_layers_are_disjoint": set(support).isdisjoint(dev) and set(support).isdisjoint(sealed) and dev.isdisjoint(sealed), "sealed_test_evaluations_zero": cfg["sealed_test_evaluation_budget"] == 0, "acfid_beats_additive_on_development_pairs": acfid_better >= rules["minimum_acfid_better_seed_count"], "acfid_nondominated_by_direct_baseline": direct_noninferior >= rules["minimum_direct_noninferior_seed_count"], "interaction_head_has_development_value": interaction >= rules["minimum_interaction_supported_seed_count"], "train_support_guard": train_noninferior >= rules["minimum_train_support_noninferior_seed_count"], "no_entropy_collapse": all(value[method]["final_entropy"] >= rules["minimum_final_entropy"] for value in results.values() for method in cfg["methods"])}
    verdict = "ACFID_COMPOSITIONAL_DEVELOPMENT_GATE_PASS" if all(checks.values()) else "ACFID_COMPOSITIONAL_DEVELOPMENT_GATE_STOP"
    payload = {"protocol": cfg["protocol"], "verdict": verdict, "checks": checks, "counts": {"acfid_better_seeds": acfid_better, "direct_noninferior_seeds": direct_noninferior, "interaction_supported_seeds": interaction, "train_guard_seeds": train_noninferior}, "results": results, "sealed_test_evaluations": 0, "formal_training_authorized": verdict.endswith("PASS")}
    args.output_root.mkdir(parents=True); (args.output_root / "ACFID_THREE_WAY_PILOT.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8"); print(json.dumps(payload, indent=2))


if __name__ == "__main__": main()
