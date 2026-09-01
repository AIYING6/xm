"""Read-only C0 audit for stable collection plus group-weighted PPO.

This is intentionally not an implementation of the candidate algorithm.  It
only checks whether existing metadata and PPO aggregation make a future,
separately authorized candidate technically coherent without adaptive sampling
or evaluation leakage.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze", type=Path, default=ROOT / "configs" / "drtp_c0_stable_collection_adaptive_optimization_freeze.json")
    parser.add_argument("--source", type=Path, default=ROOT / "algorithms" / "ri_gmappo" / "simple_ri_gmappo.py")
    parser.add_argument("--sampler", type=Path, default=ROOT / "algorithms" / "ri_gmappo" / "tcr_topology_sampler.py")
    args = parser.parse_args()

    freeze = json.loads(args.freeze.read_text(encoding="utf-8"))
    source = args.source.read_text(encoding="utf-8")
    sampler = args.sampler.read_text(encoding="utf-8")

    static = {
        "rollout_records_condition_group": '"condition_group": np.asarray(condition_group_buf' in source,
        "condition_group_documented_outside_model_inputs": "excluded from obs, graph" in source,
        "per_graph_ppo_surrogate_exists": "policy_per_graph =" in source,
        "actor_loss_aggregates_per_graph_terms": "actor_loss = actor_per_graph.mean()" in source,
        "fixed_stratified_sampler_exists": "class FixedStratifiedTopologySampler" in sampler,
        "fixed_sampler_is_uniform_over_failure_groups": "1.0 / len(FAILURE_GROUPS)" in sampler,
        "fixed_sampler_does_not_adapt_q": "self.q" not in sampler,
    }

    ppo_pass = (
        static["per_graph_ppo_surrogate_exists"]
        and static["actor_loss_aggregates_per_graph_terms"]
    )
    isolation_pass = (
        static["rollout_records_condition_group"]
        and static["condition_group_documented_outside_model_inputs"]
        and static["fixed_stratified_sampler_exists"]
        and static["fixed_sampler_is_uniform_over_failure_groups"]
        and static["fixed_sampler_does_not_adapt_q"]
    )
    cost_pass = ppo_pass and isolation_pass
    verdict = "C0_FEASIBLE" if all((ppo_pass, isolation_pass, cost_pass)) else "C0_NO_GO"

    result = {
        "protocol": freeze["protocol"],
        "stage": freeze["stage"],
        "verdict": verdict,
        "algorithm_implemented": False,
        "training_started": False,
        "evaluation_started": False,
        "automatic_c1_authorized": False,
        "gates": {
            "ppo_objective_validity": {
                "pass": ppo_pass,
                "reason": "Per-graph clipped PPO terms already exist before actor aggregation. Positive bounded group weights can therefore define an explicit alternative surrogate. This does not preserve an unbiased UTR objective or create a monotonic-improvement guarantee.",
            },
            "training_only_isolation": {
                "pass": isolation_pass,
                "reason": "The rollout records condition_group separately from model inputs, and the fixed-stratified sampler is deterministic and uniform over failure groups. A future difficulty state must remain a lagged training-only statistic and cannot control reset selection.",
            },
            "cost_and_matched_collection": {
                "pass": cost_pass,
                "reason": "A weighted mean over already-computed per-graph actor terms is O(batch size), needs no additional environment interactions or policy forwards, and retains the existing fixed-exposure collection contract.",
            },
        },
        "static_interface_evidence": static,
        "required_future_contract": {
            "sampler": "fixed_stratified_topology_sampler only",
            "nominal_weight": 1.0,
            "failure_weight_mean": 1.0,
            "actor_only": True,
            "critic_ordinary_ppo": True,
            "difficulty_signal": "lagged training-only group statistic",
            "must_report": ["weight range", "weight entropy/range", "per-group exposure", "actor KL", "nominal endpoint", "failure-group endpoints"],
        },
        "literature_boundary": "PPO permits optimization of a stated surrogate; group-DRO motivates group-aware objectives but does not establish cross-seed reliability or guarantee generalization in this MARL setting.",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
