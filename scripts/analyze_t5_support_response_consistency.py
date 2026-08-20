#!/usr/bin/env python3
"""T5 offline falsification of topology-equivariant support-response coupling.

This reads frozen T1 telemetry and checkpoints only.  It does not construct an
environment, step a simulator, update an optimizer, or write model assets.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.analyze_t4_support_utilization import (  # offline-only helpers
    GOOD,
    INTERMEDIATE,
    SEEDS,
    WEAK,
    make_agent,
    mask_samples,
    parse_seed,
    run_actor,
    tvd,
)

PROTOCOL = "T5-SUPPORT-RESPONSE-OFFLINE-FALSIFICATION-V1"
PHASES = ("pre", "early", "later")


def mean(values: list[np.ndarray | float]) -> np.ndarray | float | None:
    if not values:
        return None
    return np.mean(np.asarray(values), axis=0)


def cosine(a: np.ndarray | None, b: np.ndarray | None) -> float | None:
    if a is None or b is None:
        return None
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    return None if denom < 1e-12 else float(np.dot(a, b) / denom)


def group_mean(rows: list[dict], name: str, group: tuple[int, ...]) -> float | None:
    values = [row[name] for row in rows if row["seed"] in group and row[name] is not None]
    return None if not values else float(np.mean(values))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--t1-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    if args.output_root.exists():
        raise FileExistsError(f"refusing to overwrite: {args.output_root}")

    per_seed, checkpoint_audit = [], {}
    for seed in SEEDS:
        telemetry = args.t1_root / "evaluations" / "final_1m" / "utr_sg" / f"seed{seed}" / "raw_step_telemetry.jsonl"
        samples, sampling = parse_seed(telemetry, seed)
        failure = [sample for sample in samples if sample["family"] != "nominal"]
        checkpoint = args.t1_root / "runs" / "utr_sg" / f"seed{seed}" / "actor_critic_latest.pt"
        agent = make_agent(samples[0], checkpoint, seed)
        base, masked = run_actor(agent.actor, failure), run_actor(agent.actor, mask_samples(failure))
        delta = masked["prob"] - base["prob"]

        phase_vectors: dict[str, dict[str, list[float] | list[list[float]]]] = {
            phase: {"attacker": [], "roles": [[], [], []]} for phase in PHASES
        }
        quality, sensitivity = [], []
        for index, sample in enumerate(failure):
            current_phase = sample["phase"]
            if current_phase in phase_vectors:
                phase_vectors[current_phase]["attacker"].append(delta[index, 2].tolist())
                for role in range(3):
                    phase_vectors[current_phase]["roles"][role].append(delta[index, role].tolist())
            # Local, actor-legal support-quality descriptor; diagnostic only.
            obs = sample["obs"][2]
            support_quality = float(np.mean([obs[18], obs[28], 1.0 - obs[29], 1.0 - obs[30], obs[31]]))
            quality.append(support_quality)
            sensitivity.append(float(tvd(base["prob"][index, 2], masked["prob"][index, 2])))

        attacker_means = {phase: mean(phase_vectors[phase]["attacker"]) for phase in PHASES}
        role_means = {
            phase: [mean(phase_vectors[phase]["roles"][role]) for role in range(3)]
            for phase in PHASES
        }
        pre_early = cosine(attacker_means["pre"], attacker_means["early"])
        early_later = cosine(attacker_means["early"], attacker_means["later"])
        role_cosines = []
        for phase in PHASES:
            vectors = role_means[phase]
            role_cosines.extend([cosine(vectors[0], vectors[1]), cosine(vectors[0], vectors[2]), cosine(vectors[1], vectors[2])])

        # Monotonicity is assessed within quintiles of the legal descriptor, not as a
        # performance claim.  It is intentionally only an offline diagnostic.
        order = np.argsort(quality)
        cut = max(1, len(order) // 5)
        low = [sensitivity[i] for i in order[:cut]]
        high = [sensitivity[i] for i in order[-cut:]]
        per_seed.append({
            "seed": seed,
            "sampling": sampling,
            "failure_samples": len(failure),
            "attacker_response_cosine_pre_to_early": pre_early,
            "attacker_response_cosine_early_to_later": early_later,
            "mean_cross_role_response_cosine": mean([value for value in role_cosines if value is not None]),
            "support_sensitivity_low_quality": mean(low),
            "support_sensitivity_high_quality": mean(high),
            "high_minus_low_quality_sensitivity": float(mean(high) - mean(low)),
            "phase_response_norm": {phase: None if attacker_means[phase] is None else float(np.linalg.norm(attacker_means[phase])) for phase in PHASES},
        })
        checkpoint_audit[str(seed)] = {"parameter_count": sum(p.numel() for p in agent.parameters())}
        print(f"T5 analyzed frozen seed{seed}: {len(failure)} failure samples", flush=True)

    group_rows = {}
    for label, group in (("good", GOOD), ("weak", WEAK), ("intermediate", INTERMEDIATE)):
        group_rows[label] = {
            key: group_mean(per_seed, key, group)
            for key in (
                "attacker_response_cosine_pre_to_early",
                "attacker_response_cosine_early_to_later",
                "mean_cross_role_response_cosine",
                "high_minus_low_quality_sensitivity",
            )
        }
    good, weak = group_rows["good"], group_rows["weak"]
    consistency_gap = None if good["attacker_response_cosine_pre_to_early"] is None or weak["attacker_response_cosine_pre_to_early"] is None else good["attacker_response_cosine_pre_to_early"] - weak["attacker_response_cosine_pre_to_early"]
    role_specific = all((group_rows["good"]["mean_cross_role_response_cosine"] or 1.0) < 0.95 for _ in (0,))
    # A prospective coupling principle is falsified if good policies do not show
    # at least weak-level response consistency, topology relevance, and role differentiation.
    topology_consistency_supported = consistency_gap is not None and consistency_gap >= 0.0
    decision = "PASS" if topology_consistency_supported and role_specific else "FAIL"

    result = {
        "protocol": PROTOCOL,
        "offline_only": True,
        "no_environment_constructed": True,
        "no_optimizer_update": True,
        "candidate_principle": "topology-equivariant role-specific support-response coupling",
        "actor_legal_support_descriptor": ["direct_detection", "inbound_connectivity", "one_minus_inbound_age", "one_minus_cache_age", "cache_confidence"],
        "diagnostic_only": ["seed_rank", "phase", "future_continuity"],
        "forbidden": ["failure_truth_actor_input", "global_topology", "future_state", "share_obs"],
        "checkpoint_audit": checkpoint_audit,
        "per_seed": per_seed,
        "groups": group_rows,
        "tests": {
            "T5_1_response_separation": "Supported by frozen T4 matched-action and sensitivity results; reported separately in T4.",
            "T5_2_topology_response_consistency": {"good_minus_weak_pre_to_early_cosine": consistency_gap, "pass": topology_consistency_supported},
            "T5_3_role_specificity": {"good_cross_role_cosine": good["mean_cross_role_response_cosine"], "pass": role_specific},
            "T5_4_topology_specificity": "Supported by frozen T4 early-phase amplification (0.145 to 0.322).",
            "T5_5_representation_action_stage": "Supported by frozen T4 latent probe: no material good-vs-weak latent decoding gap.",
        },
        "decision": decision,
        "boundary": "PASS means the principle is empirically compatible with frozen development evidence only; it is not a causal or training-performance result.",
    }
    args.output_root.mkdir(parents=True)
    (args.output_root / "t5_support_response_falsification.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"status": "completed", "decision": decision}, indent=2))


if __name__ == "__main__":
    main()
