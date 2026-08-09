"""Read-only G0 audit of PCRF-R1 comparator inputs and relation separability.

This is deliberately not a policy evaluation.  It drives fixed, method-
independent actions through the recipient-specific environment and reports the
raw graph tensors that every graph actor receives.  It must pass before any
v1.9 GPU phase can claim a three-relation mechanism.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from envs import RELATION_COMMUNICATION, RELATION_PERCEPTION, RELATION_TASK_SUPPORT
from envs.uav_intercept_3d_env import UAVIntercept3DConfig, UAVIntercept3DEnv


EDGE_FIELD_NAMES = (
    "relative_x", "relative_y", "relative_z", "distance", "los_x", "los_y", "los_z",
    "relative_vx", "relative_vy", "relative_vz", "blue_blue", "perception_relation",
    "communication_relation", "task_support_relation", "reserved", "message_age",
    "message_confidence", "endpoint_valid",
)
SEEDS = (501, 502, 503, 504, 505)
STEPS_PER_SEED = 120


def jaccard(left: np.ndarray, right: np.ndarray) -> float:
    union = np.logical_or(left > 0.5, right > 0.5).sum()
    if union == 0:
        return 1.0
    return float(np.logical_and(left > 0.5, right > 0.5).sum() / union)


def audit() -> dict[str, object]:
    relation_pairs = (("perception_communication", RELATION_PERCEPTION, RELATION_COMMUNICATION),
                      ("perception_task_support", RELATION_PERCEPTION, RELATION_TASK_SUPPORT),
                      ("communication_task_support", RELATION_COMMUNICATION, RELATION_TASK_SUPPORT))
    jaccards: dict[str, list[float]] = {name: [] for name, _, _ in relation_pairs}
    exactly_equal: dict[str, int] = {name: 0 for name, _, _ in relation_pairs}
    task_comm_mismatch_entries = 0
    relation_field_mismatch_entries = 0
    union_mismatch_entries = 0
    states_seen = 0

    for seed in SEEDS:
        env = UAVIntercept3DEnv(UAVIntercept3DConfig(
            seed=seed,
            strict_target_sensing=True,
            agent_target_info_bottleneck=True,
            communication_dropout_prob=0.30,
            message_delay_steps=2,
            radar_dropout_prob=0.10,
            failed_blue_agent=1,
            node_failure_start_step=40,
            node_failure_duration_steps=80,
        ))
        _, _, graph = env.reset()
        actions = np.random.default_rng(seed + 10_000).integers(
            0, env.action_dim, size=(STEPS_PER_SEED, env.config.num_blue), endpoint=False
        )
        for step in range(STEPS_PER_SEED + 1):
            relation = graph["relation_adj"]
            edge = graph["edge_feat"]
            union = graph["adj"]
            states_seen += 1
            task_comm_mismatch_entries += int(np.count_nonzero(
                relation[:, RELATION_COMMUNICATION] != relation[:, RELATION_TASK_SUPPORT]
            ))
            relation_field_mismatch_entries += int(np.count_nonzero(
                relation[:, RELATION_PERCEPTION] != edge[..., 11]
            ))
            relation_field_mismatch_entries += int(np.count_nonzero(
                relation[:, RELATION_COMMUNICATION] != edge[..., 12]
            ))
            relation_field_mismatch_entries += int(np.count_nonzero(
                relation[:, RELATION_TASK_SUPPORT] != edge[..., 13]
            ))
            union_mismatch_entries += int(np.count_nonzero(
                union + 1e-6 < relation.max(axis=1)
            ))
            for name, left_id, right_id in relation_pairs:
                left, right = relation[:, left_id], relation[:, right_id]
                jaccards[name].append(jaccard(left, right))
                exactly_equal[name] += int(np.array_equal(left, right))
            if step == STEPS_PER_SEED:
                break
            _, _, graph, _, dones, _ = env.step(actions[step])
            if bool(np.all(dones)):
                _, _, graph = env.reset()

    total_pair_observations = states_seen
    return {
        "audit": "G0_COMPARATOR_INPUT_AND_RELATION_SEPARABILITY",
        "mode": "read_only_method_independent_fixed_actions",
        "repository_head_at_audit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "seeds": list(SEEDS),
        "states_seen": states_seen,
        "edge_feature_schema": list(enumerate(EDGE_FIELD_NAMES)),
        "relation_identity_is_present_in_shared_edge_features": True,
        "raw_graph_tensor_source_is_shared_across_graph_encoders": True,
        "relation_edge_field_mismatch_entries": relation_field_mismatch_entries,
        "union_undercontains_relation_entries": union_mismatch_entries,
        "task_support_communication_mismatch_entries": task_comm_mismatch_entries,
        "pairwise_relation": {
            name: {
                "mean_jaccard": float(np.mean(values)),
                "min_jaccard": float(np.min(values)),
                "exactly_equal_states": exactly_equal[name],
                "state_count": total_pair_observations,
                "exactly_equal_fraction": exactly_equal[name] / total_pair_observations,
            }
            for name, values in jaccards.items()
        },
        "decision": (
            "NO_GO_FOR_THREE_RELATION_TASK_SUPPORT_MECHANISM"
            if task_comm_mismatch_entries == 0 else "TASK_SUPPORT_HAS_INDEPENDENT_ACTIVATION"
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
        args.output.write_text(payload + "\n", encoding="utf-8")
    print(payload)
    if report["decision"] != "NO_GO_FOR_THREE_RELATION_TASK_SUPPORT_MECHANISM":
        raise SystemExit("G0 audit outcome changed; require author review before proceeding")


if __name__ == "__main__":
    main()
