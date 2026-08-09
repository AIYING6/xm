"""Method-independent development audit of natural PCRF-R2 conflict states."""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from envs.uav_intercept_3d_env import UAVIntercept3DConfig, UAVIntercept3DEnv  # noqa: E402

EPISODE_SEEDS = tuple(range(81, 113))
ACTION_SEED_OFFSET = 8_100
MIN_STATE_RECORDS = 30
MIN_STATE_FRACTION = 0.005


def record_graph(graph: dict, step: int, failure_active: bool, counts: Counter, total: Counter) -> None:
    c_nodes = graph["pcrf_r2_c_node_feat"]
    p_nodes = graph["pcrf_r2_p_node_feat"]
    c_edge = graph["pcrf_r2_c_edge_feat"]
    p_adj, c_adj = graph["pcrf_r2_p_adj"], graph["pcrf_r2_c_adj"]
    target = c_nodes.shape[1] - 1
    window = "failure_active" if failure_active else "outside_failure"
    for receiver in range(c_nodes.shape[0]):
        p = bool(p_adj[receiver, 0, target] > 0.5)
        c = bool(c_adj[receiver, 0, target] > 0.5)
        key_prefix = f"{window}/"
        total[f"{window}/actor_steps"] += 1
        total["all/actor_steps"] += 1
        if p != c:
            counts[key_prefix + "availability_mismatch"] += 1
        if p and not c:
            counts[key_prefix + "p_only"] += 1
        if c and not p:
            counts[key_prefix + "c_only"] += 1
        if c:
            age = float(c_edge[receiver, 0, target, 15])
            confidence = float(c_edge[receiver, 0, target, 16])
            if age > 0.0:
                counts[key_prefix + "stale_c"] += 1
            if confidence < 1.0:
                counts[key_prefix + "confidence_degraded_c"] += 1
        if p and c:
            disagreement = float(np.abs(p_nodes[receiver, target, :11] - c_nodes[receiver, target, :11]).mean())
            age = float(c_edge[receiver, 0, target, 15])
            confidence = float(c_edge[receiver, 0, target, 16])
            if disagreement > 1e-7:
                counts[key_prefix + "both_disagree"] += 1
            if age > 0.0 and disagreement > 1e-7:
                counts[key_prefix + "fresh_p_stale_c_disagree"] += 1
            if disagreement <= 1e-7 and age == 0.0 and confidence == 1.0:
                counts[key_prefix + "exact_neutral_c0"] += 1


def run_audit() -> dict:
    counts: Counter = Counter()
    total: Counter = Counter()
    terminations: Counter = Counter()
    for seed in EPISODE_SEEDS:
        env = UAVIntercept3DEnv(UAVIntercept3DConfig(
            seed=seed,
            strict_target_sensing=True,
            agent_target_info_bottleneck=True,
            communication_dropout_prob=0.3,
            message_delay_steps=2,
            radar_dropout_prob=0.1,
            failed_blue_agent=1,
            node_failure_start_step=40,
            node_failure_duration_steps=80,
            attack_hold_steps=4,
            min_success_step=80,
        ))
        _, _, graph = env.reset()
        rng = np.random.default_rng(ACTION_SEED_OFFSET + seed)
        done = False
        while not done:
            failure_active = env._is_comm_failed(1)
            record_graph(graph, env.step_count, failure_active, counts, total)
            actions = rng.integers(0, env.action_dim, size=env.num_agents, endpoint=False)
            _, _, graph, _, dones, infos = env.step(actions)
            done = bool(np.all(dones))
            if done:
                info = infos[0] if isinstance(infos, (list, tuple)) else infos
                terminations[str(info.get("termination_reason", "unknown"))] += 1
    failure_total = total["failure_active/actor_steps"]
    required = ("availability_mismatch", "p_only", "c_only", "stale_c", "both_disagree", "fresh_p_stale_c_disagree")
    prevalence = {
        state: {
            "records": counts[f"failure_active/{state}"],
            "fraction_of_failure_actor_steps": counts[f"failure_active/{state}"] / failure_total if failure_total else 0.0,
        }
        for state in required
    }
    insufficient = [
        state for state, row in prevalence.items()
        if row["records"] < MIN_STATE_RECORDS or row["fraction_of_failure_actor_steps"] < MIN_STATE_FRACTION
    ]
    return {
        "audit": "P1_NATURAL_CONFLICT_PREVALENCE_V1_9",
        "development_only": True,
        "method_independent": True,
        "episodes": len(EPISODE_SEEDS),
        "episode_seeds": list(EPISODE_SEEDS),
        "action_seed_offset": ACTION_SEED_OFFSET,
        "fixed_sufficiency_rule": {
            "min_records_per_primary_state": MIN_STATE_RECORDS,
            "min_fraction_of_failure_actor_steps": MIN_STATE_FRACTION,
        },
        "failure_actor_steps": failure_total,
        "all_actor_steps": total["all/actor_steps"],
        "prevalence": prevalence,
        "all_counts": dict(sorted(counts.items())),
        "termination_counts": dict(sorted(terminations.items())),
        "verdict": "PASS" if not insufficient else "BLOCKED",
        "insufficient_primary_states": insufficient,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run_audit()
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        if args.output.exists():
            raise RuntimeError(f"refusing to overwrite audit output: {args.output}")
        args.output.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    if result["verdict"] != "PASS":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
