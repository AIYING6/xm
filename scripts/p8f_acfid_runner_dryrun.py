"""Matched PPO dry-run and held-out-combination leakage audit for ACFID."""
from __future__ import annotations

import argparse
import hashlib
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
from algorithms.acfid_recovery_policy import ACFIDRecoveryPolicy, AdditiveRecoveryPolicy, DirectFaultAwareRecoveryPolicy, parameter_count
from envs.acfid_compound_fault_env import ACTIONS, FAULTS, ACFIDCompoundFaultEnv
from envs.acfid_sequential_recovery_env import ACFIDSequentialRecoveryEnv, all_sets_of_orders


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def build_policy(name: str, hidden: int):
    if name == "direct_fault_aware": return DirectFaultAwareRecoveryPolicy(7, 5, hidden=hidden)
    if name == "additive": return AdditiveRecoveryPolicy(7, 5, hidden=hidden)
    if name == "acfid": return ACFIDRecoveryPolicy(7, 5, 3, hidden=hidden)
    raise ValueError(name)


def tensors(contexts, fault_sets):
    context = torch.tensor([[*c.demand, *c.urgency, c.cross_link, c.reserve, 5 / 7] for c in contexts], dtype=torch.float32)
    descriptors = torch.tensor(ACFIDSequentialRecoveryEnv.fault_descriptors(), dtype=torch.float32)
    fault_features = descriptors[None].expand(len(contexts), -1, -1).clone()
    active = torch.tensor([[float(f in faults) for f in FAULTS] for faults in fault_sets], dtype=torch.float32)
    relations = torch.tensor(ACFIDSequentialRecoveryEnv.pair_relations(), dtype=torch.float32)[None].expand(len(contexts), -1, -1, -1).clone()
    return context, fault_features, active, relations


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--config", type=Path, default=ROOT / "configs/p8f_acfid_runner_dryrun_20260910.json"); parser.add_argument("--output-root", type=Path, required=True); parser.add_argument("--execute", action="store_true"); args = parser.parse_args()
    if not args.execute: raise SystemExit("explicit --execute required")
    if args.output_root.exists(): raise FileExistsError(f"refusing to overwrite {args.output_root}")
    cfg = json.loads(args.config.read_text(encoding="utf-8")); torch.manual_seed(cfg["seed"]); rng = np.random.default_rng(cfg["seed"]); simulator = ACFIDCompoundFaultEnv()
    train_pairs = {frozenset(pair) for pair in cfg["train_pairs"]}; train_support = {frozenset(), *all_sets_of_orders(1), *train_pairs}
    heldout = set(all_sets_of_orders(2, 3, 4)) - train_pairs
    ordered_train = sorted(train_support, key=lambda x: (len(x), sorted(x)))
    faults = [value for _, value in zip(range(cfg["rollout_samples"]), cycle(ordered_train))]
    context_seeds = rng.integers(0, 2**31 - 1, size=cfg["rollout_samples"]).tolist()
    contexts = [simulator.sample_context(np.random.default_rng(seed)) for seed in context_seeds]
    noise_seeds = rng.integers(0, 2**31 - 1, size=cfg["rollout_samples"]).tolist()
    tape = [{"context_seed": c, "noise_seed": n, "faults": sorted(f)} for c, n, f in zip(context_seeds, noise_seeds, faults)]
    x = tensors(contexts, faults); method_results = {}; counts = {}
    for method, spec in cfg["methods"].items():
        torch.manual_seed(cfg["seed"] + 17); policy = build_policy(method, spec["hidden"]); critic = InvariantRecoveryCritic(7, 5)
        counts[method] = parameter_count(policy)
        with torch.no_grad():
            distribution = Categorical(logits=policy(*x)); actions = distribution.sample(); old_log_prob = distribution.log_prob(actions)
            values = critic(x[0], x[1], x[2])
        # One realized two-branch transition per rollout.  Counterfactual
        # action enumeration is reserved for the evaluator, never training.
        returns = torch.tensor([simulator.value(c, f, ACTIONS[int(a)], np.random.default_rng(ns).lognormal(0, .055, size=2)) for c, f, a, ns in zip(contexts, faults, actions, noise_seeds)], dtype=torch.float32)
        batch = PPOBatch(*x, actions, old_log_prob, returns, returns - values)
        before = torch.cat([p.detach().flatten() for p in policy.parameters()]); optimizer = torch.optim.Adam([*policy.parameters(), *critic.parameters()], lr=cfg["learning_rate"])
        finite = True; metrics = {}
        for _ in range(cfg["ppo_epochs"]):
            optimizer.zero_grad(); loss, metrics = ppo_loss(policy, critic, batch, cfg["clip_ratio"], cfg["value_coef"], cfg["entropy_coef"])
            finite = finite and bool(torch.isfinite(loss)); loss.backward()
            finite = finite and all(p.grad is None or bool(torch.isfinite(p.grad).all()) for p in [*policy.parameters(), *critic.parameters()])
            torch.nn.utils.clip_grad_norm_([*policy.parameters(), *critic.parameters()], cfg["gradient_norm_max"]); optimizer.step()
        after = torch.cat([p.detach().flatten() for p in policy.parameters()]); change = float(torch.linalg.vector_norm(after - before))
        method_results[method] = {"tape_sha256": digest(tape), "finite_update": finite, "parameter_l2_change": change,
                                  "mean_rollout_return": float(returns.mean()), **metrics}
    max_gap = (max(counts.values()) - min(counts.values())) / min(counts.values())
    source = (ROOT / "scripts/p8f_acfid_runner_dryrun.py").read_text(encoding="utf-8")
    update_source = source.split("    checks = {", 1)[0]
    checks = {
        "train_and_heldout_support_disjoint": train_support.isdisjoint(heldout),
        "heldout_combinations_absent_from_rollout_tape": all(frozenset(row["faults"]) not in heldout for row in tape),
        "all_methods_use_identical_tape": len({row["tape_sha256"] for row in method_results.values()}) == 1,
        "policy_capacities_matched": max_gap <= cfg["capacity_gap_max"],
        "all_losses_and_gradients_finite": all(row["finite_update"] for row in method_results.values()),
        "all_policy_parameters_update": all(row["parameter_l2_change"] >= cfg["parameter_change_min"] for row in method_results.values()),
        "no_pair_identity_embedding": "Embedding(" not in (ROOT / "algorithms/acfid_recovery_policy.py").read_text(encoding="utf-8"),
        "no_oracle_q_values_in_policy_update": ".q_values(" not in update_source,
    }
    verdict = "ACFID_RUNNER_DRYRUN_PASS" if all(checks.values()) else "ACFID_RUNNER_DRYRUN_STOP"
    payload = {"protocol": cfg["protocol"], "verdict": verdict, "checks": checks, "metrics": {"train_support_count": len(train_support), "heldout_support_count": len(heldout), "policy_parameter_counts": counts, "maximum_capacity_gap": max_gap, "methods": method_results}, "training_started": False, "full_pilot_authorized": False, "next_gate": "FIXED_ENDPOINT_EVALUATOR_AND_COMMON_NOISE_REGRET_AUDIT"}
    args.output_root.mkdir(parents=True); (args.output_root / "ACFID_RUNNER_DRYRUN_REPORT.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8"); print(json.dumps(payload, indent=2))


if __name__ == "__main__": main()
