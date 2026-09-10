"""Execute the frozen short ACFID optimization-qualification pilot."""
from __future__ import annotations

import argparse
import json
import sys
from itertools import cycle
from pathlib import Path

import numpy as np
import torch
from torch.distributions import Categorical

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from algorithms.acfid_clipped_ppo import InvariantRecoveryCritic, PPOBatch, ppo_loss
from algorithms.acfid_fixed_endpoint_evaluator import EvaluationCase, evaluate_fixed_endpoint
from algorithms.acfid_recovery_policy import ACFIDRecoveryPolicy, AdditiveRecoveryPolicy, DirectFaultAwareRecoveryPolicy
from envs.acfid_compound_fault_env import ACTIONS, ACFIDCompoundFaultEnv
from envs.acfid_sequential_recovery_env import ACFIDSequentialRecoveryEnv, all_sets_of_orders


def build_policy(name: str, hidden: int):
    if name == "direct_fault_aware": return DirectFaultAwareRecoveryPolicy(7, 5, hidden=hidden)
    if name == "additive": return AdditiveRecoveryPolicy(7, 5, hidden=hidden)
    if name == "acfid": return ACFIDRecoveryPolicy(7, 5, 3, hidden=hidden)
    raise ValueError(name)


def batch_tensors(contexts, fault_sets):
    context = torch.tensor([[*c.demand, *c.urgency, c.cross_link, c.reserve, 5 / 7] for c in contexts], dtype=torch.float32)
    descriptors = torch.tensor(ACFIDSequentialRecoveryEnv.fault_descriptors(), dtype=torch.float32)
    faults = descriptors[None].expand(len(contexts), -1, -1).clone()
    active = torch.tensor([[float(fault in value) for fault in ACFIDCompoundFaultEnv.dependency_branch] for value in fault_sets], dtype=torch.float32)
    relations = torch.tensor(ACFIDSequentialRecoveryEnv.pair_relations(), dtype=torch.float32)[None].expand(len(contexts), -1, -1, -1).clone()
    return context, faults, active, relations


def validation_cases(seed: int, support, count: int):
    rng = np.random.default_rng(seed + 700000)
    return [EvaluationCase(int(rng.integers(2**31 - 1)), int(rng.integers(2**31 - 1)), faults)
            for faults in support for _ in range(count)]


def summarize(rows):
    return {"mean_regret": float(np.mean([row["action_regret"] for row in rows])),
            "success": float(np.mean([row["success"] for row in rows])),
            "timeout": float(np.mean([row["timeout"] for row in rows]))}


def train_one(method: str, spec: dict, cfg: dict, seed: int, support):
    torch.manual_seed(seed); policy = build_policy(method, spec["hidden"]); critic = InvariantRecoveryCritic(7, 5)
    optimizer = torch.optim.Adam([*policy.parameters(), *critic.parameters()], lr=cfg["learning_rate"])
    simulator = ACFIDCompoundFaultEnv(); cases = validation_cases(seed, support, cfg["validation_cases_per_fault_set"])
    initial = summarize(evaluate_fixed_endpoint(policy, cases)); ordered = list(support); interaction_gradient_max = 0.0; final_entropy = 0.0
    for update in range(cfg["updates"]):
        rng = np.random.default_rng(seed * 1000 + update); fault_sets = [value for _, value in zip(range(cfg["rollout_samples_per_update"]), cycle(ordered))]
        context_seeds = rng.integers(2**31 - 1, size=len(fault_sets)); noise_seeds = rng.integers(2**31 - 1, size=len(fault_sets))
        contexts = [simulator.sample_context(np.random.default_rng(int(value))) for value in context_seeds]; x = batch_tensors(contexts, fault_sets)
        with torch.no_grad():
            distribution = Categorical(logits=policy(*x)); actions = distribution.sample(); old_log_prob = distribution.log_prob(actions); values = critic(x[0], x[1], x[2])
        returns = torch.tensor([simulator.value(context, faults, ACTIONS[int(action)], np.random.default_rng(int(noise_seed)).lognormal(0, .055, size=2)) for context, faults, action, noise_seed in zip(contexts, fault_sets, actions, noise_seeds)], dtype=torch.float32)
        batch = PPOBatch(*x, actions, old_log_prob, returns, returns - values)
        for _ in range(cfg["ppo_epochs"]):
            optimizer.zero_grad(); loss, metrics = ppo_loss(policy, critic, batch, cfg["clip_ratio"], cfg["value_coef"], cfg["entropy_coef"]); loss.backward()
            if method == "acfid":
                norm = torch.sqrt(sum((parameter.grad.square().sum() for parameter in policy.interaction.parameters() if parameter.grad is not None), torch.tensor(0.0)))
                interaction_gradient_max = max(interaction_gradient_max, float(norm))
            torch.nn.utils.clip_grad_norm_([*policy.parameters(), *critic.parameters()], cfg["gradient_norm_max"]); optimizer.step(); final_entropy = metrics["entropy"]
    final = summarize(evaluate_fixed_endpoint(policy, cases)); reduction = (initial["mean_regret"] - final["mean_regret"]) / max(initial["mean_regret"], 1e-8)
    return {"initial": initial, "final": final, "relative_regret_reduction": reduction, "final_entropy": final_entropy, "interaction_gradient_max": interaction_gradient_max}


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--config", type=Path, default=ROOT / "configs/p8h_acfid_short_learning_pilot_20260910.json"); parser.add_argument("--output-root", type=Path, required=True); parser.add_argument("--execute", action="store_true"); args = parser.parse_args()
    if not args.execute: raise SystemExit("explicit --execute required")
    if args.output_root.exists(): raise FileExistsError(f"refusing to overwrite {args.output_root}")
    cfg = json.loads(args.config.read_text(encoding="utf-8")); train_pairs = {frozenset(pair) for pair in cfg["train_pairs"]}
    support = sorted({frozenset(), *all_sets_of_orders(1), *train_pairs}, key=lambda x: (len(x), sorted(x))); sealed = set(all_sets_of_orders(2, 3, 4)) - train_pairs
    results = {method: {str(seed): train_one(method, spec, cfg, seed, support) for seed in cfg["seeds"]} for method, spec in cfg["methods"].items()}
    rules = cfg["pass_rules"]; learned = {method: sum(row["relative_regret_reduction"] >= rules["minimum_relative_regret_reduction"] for row in seeds.values()) for method, seeds in results.items()}
    noninferior = sum(results["acfid"][str(seed)]["final"]["mean_regret"] <= results["additive"][str(seed)]["final"]["mean_regret"] + rules["acfid_additive_noninferiority_margin"] for seed in cfg["seeds"])
    checks = {"sealed_test_support_absent": set(support).isdisjoint(sealed),
              "all_methods_learn_in_at_least_two_seeds": all(value >= rules["minimum_seeds_with_regret_reduction_per_method"] for value in learned.values()),
              "no_policy_entropy_collapse": all(row["final_entropy"] >= rules["minimum_final_entropy"] for seeds in results.values() for row in seeds.values()),
              "acfid_interaction_head_receives_gradient": all(results["acfid"][str(seed)]["interaction_gradient_max"] >= rules["minimum_acfid_interaction_gradient_norm"] for seed in cfg["seeds"]),
              "acfid_is_train_support_noninferior_to_additive": noninferior >= rules["minimum_acfid_noninferior_seeds"]}
    verdict = "ACFID_SHORT_LEARNING_PILOT_PASS" if all(checks.values()) else "ACFID_SHORT_LEARNING_PILOT_STOP"
    payload = {"protocol": cfg["protocol"], "verdict": verdict, "checks": checks, "metrics": {"learned_seed_counts": learned, "acfid_noninferior_seed_count": noninferior, "results": results}, "sealed_test_evaluations": 0, "full_1m_training_authorized": False, "next_gate": "P8I_FORMAL_PILOT_DECISION"}
    args.output_root.mkdir(parents=True); (args.output_root / "ACFID_SHORT_LEARNING_PILOT.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8"); print(json.dumps(payload, indent=2))


if __name__ == "__main__": main()
