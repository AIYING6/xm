"""Fixed-endpoint, common-noise evaluation for ACFID recovery policies."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import torch

from envs.acfid_compound_fault_env import ACTIONS, ACFIDCompoundFaultEnv
from envs.acfid_sequential_recovery_env import ACFIDSequentialRecoveryEnv


@dataclass(frozen=True)
class EvaluationCase:
    context_seed: int
    noise_seed: int
    faults: frozenset[str]


def evaluate_fixed_endpoint(policy: torch.nn.Module, cases: list[EvaluationCase]) -> list[dict]:
    """Evaluate without gradients, updates, normalization fitting, or selection."""
    simulator = ACFIDCompoundFaultEnv(); descriptors = ACFIDSequentialRecoveryEnv.fault_descriptors()
    relations = ACFIDSequentialRecoveryEnv.pair_relations(); rows = []
    training = policy.training; policy.eval()
    with torch.no_grad():
        for case in cases:
            context = simulator.sample_context(np.random.default_rng(case.context_seed))
            noise = np.random.default_rng(case.noise_seed).lognormal(0, .055, size=(32, 2))
            context_tensor = torch.tensor([[*context.demand, *context.urgency, context.cross_link, context.reserve, 5 / 7]], dtype=torch.float32)
            fault_tensor = torch.tensor(descriptors[None], dtype=torch.float32)
            active = torch.tensor([[float(fault in case.faults) for fault in simulator.dependency_branch]], dtype=torch.float32)
            relation_tensor = torch.tensor(relations[None], dtype=torch.float32)
            logits = policy(context_tensor, fault_tensor, active, relation_tensor)
            selected = int(logits.argmax(dim=-1).item()); q = simulator.q_values(context, case.faults, noise)
            selected_value = q[ACTIONS[selected]]; oracle_value = max(q.values())
            rows.append({"context_seed": case.context_seed, "noise_seed": case.noise_seed,
                         "faults": "+".join(sorted(case.faults)), "selected_action": ACTIONS[selected],
                         "selected_value": selected_value, "oracle_value": oracle_value,
                         "action_regret": oracle_value - selected_value,
                         "success": float(selected_value >= .85), "timeout": float(selected_value < .45),
                         "safe_abort": float(ACTIONS[selected] == "safe_abort")})
    policy.train(training)
    return rows
