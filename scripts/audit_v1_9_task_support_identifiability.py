"""Read-only G0-R1 audit of Task-Support versus Communication identifiability.

The audit intentionally does not train, evaluate a policy, or alter an
environment.  It checks three necessary conditions for calling Task-Support an
independent actor-information source: support, feature, and intervention
identifiability.
"""
from __future__ import annotations

import argparse
import inspect
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.simple_ri_gmappo import ProvenanceConditionedRelationFactorEncoder
from envs import RELATION_COMMUNICATION, RELATION_TASK_SUPPORT
from envs.uav_intercept_3d_env import UAVIntercept3DConfig, UAVIntercept3DEnv


CONDITIONS = (
    ("nominal", {}),
    ("packet_loss", {"communication_dropout_prob": 0.30}),
    ("delayed_packets", {"communication_dropout_prob": 0.30, "message_delay_steps": 2}),
    ("radar_dropout", {"radar_dropout_prob": 0.10}),
    ("relay_failure", {"failed_blue_agent": 1, "node_failure_start_step": 20, "node_failure_duration_steps": 80}),
    ("combined_formal_like", {
        "communication_dropout_prob": 0.30, "message_delay_steps": 2, "radar_dropout_prob": 0.10,
        "failed_blue_agent": 1, "node_failure_start_step": 20, "node_failure_duration_steps": 80,
    }),
)
SEEDS = (701, 702, 703)
STEPS = 100


def source_contract() -> dict[str, bool]:
    env_source = inspect.getsource(UAVIntercept3DEnv._get_recipient_graph_view)
    encoder_source = inspect.getsource(ProvenanceConditionedRelationFactorEncoder._apply_layer)
    return {
        "communication_and_support_share_the_same_valid_teammate_predicate": (
            "comm = float(src == receiver and dst < n_blue and dst != receiver and valid[dst] > 0.5)" in env_source
            and "support = float(src == receiver and dst < n_blue and dst != receiver and valid[dst] > 0.5)" in env_source
        ),
        "task_support_edge_field_is_the_support_scalar": "comm, support, 0.0, age" in env_source,
        "each_factor_receives_the_same_generic_edge_feature_tensor": "layer(x, relation_adj[:, relation_id], edge_feat)" in encoder_source,
        "only_explicit_task_support_change_is_the_ablation_switch": "graph_relation_ablation == \"no_task_support\"" in env_source,
    }


def audit_condition(name: str, overrides: dict[str, int | float]) -> dict[str, object]:
    states = 0
    support_mismatches = 0
    feature_mismatches = 0
    for seed in SEEDS:
        env = UAVIntercept3DEnv(UAVIntercept3DConfig(
            seed=seed,
            strict_target_sensing=True,
            agent_target_info_bottleneck=True,
            **overrides,
        ))
        _, _, graph = env.reset()
        actions = np.random.default_rng(seed + 20_000).integers(
            0, env.action_dim, size=(STEPS, env.config.num_blue), endpoint=False
        )
        for step in range(STEPS + 1):
            rel = graph["relation_adj"]
            edge = graph["edge_feat"]
            states += 1
            support_mismatches += int(np.count_nonzero(
                rel[:, RELATION_COMMUNICATION] != rel[:, RELATION_TASK_SUPPORT]
            ))
            feature_mismatches += int(np.count_nonzero(edge[..., 12] != edge[..., 13]))
            if step == STEPS:
                break
            _, _, graph, _, dones, _ = env.step(actions[step])
            if bool(np.all(dones)):
                _, _, graph = env.reset()
    return {
        "condition": name,
        "states": states,
        "communication_task_support_mask_mismatches": support_mismatches,
        "communication_task_support_edge_feature_mismatches": feature_mismatches,
        "independent_legal_intervention_observed": False,
    }


def audit() -> dict[str, object]:
    rows = [audit_condition(name, dict(overrides)) for name, overrides in CONDITIONS]
    contract = source_contract()
    no_difference = all(
        row["communication_task_support_mask_mismatches"] == 0
        and row["communication_task_support_edge_feature_mismatches"] == 0
        for row in rows
    )
    independent = (not no_difference) and not contract[
        "communication_and_support_share_the_same_valid_teammate_predicate"
    ]
    return {
        "audit": "G0_R1_TASK_SUPPORT_IDENTIFIABILITY",
        "mode": "read_only_method_independent_fixed_actions_and_static_source_inspection",
        "repository_head_at_audit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "seeds_per_condition": list(SEEDS),
        "steps_per_seed": STEPS,
        "conditions": rows,
        "source_contract": contract,
        "support_identifiability": not no_difference,
        "feature_identifiability": not no_difference,
        "intervention_identifiability": independent,
        "ablation_switch_is_not_a_legal_environment_intervention": True,
        "decision": (
            "TASK_SUPPORT_NOT_AN_INDEPENDENT_LEGAL_INFORMATION_SOURCE"
            if not independent else "AUTHOR_REVIEW_REQUIRED_FOR_TASK_SUPPORT_SEMANTICS"
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = audit()
    payload = json.dumps(report, indent=2, sort_keys=True)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w", encoding="utf-8", newline="\n") as output:
            output.write(payload + "\n")
    print(payload)
    if report["decision"] != "TASK_SUPPORT_NOT_AN_INDEPENDENT_LEGAL_INFORMATION_SOURCE":
        raise SystemExit("Task-Support audit changed; author review required before proceeding")


if __name__ == "__main__":
    main()
