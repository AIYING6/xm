"""Audit whether V8 supplies a non-saturated baseline for a relation-value method.

This audit deliberately does *not* require the capacity-matched plain MLP to
solve the relation-value distinction. Requiring that would make the proposed
representation redundant. It verifies the narrower task-grounding claim: the
matched baseline obtains an intermediate outcome on the balanced task, while
its profile-stratified behaviour documents the unresolved public relation
decision for the later candidate and semantic-shuffle gate.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


PROTOCOL = "COMMITMENT-HANDOFF-3D-V8-G2B-BASELINE-CAPABILITY-AUDIT-V1"
PROFILES = ("current_compact", "current_delayed", "future_fresh", "future_durable")


def _load(seed_dir: Path) -> tuple[int, dict[str, object]]:
    manifest = json.loads((seed_dir / "run_manifest.json").read_text(encoding="utf-8"))
    if manifest.get("protocol") != "COMMITMENT-HANDOFF-3D-V8-PLAIN-MAPPO-G2-DEVELOPMENT-V1":
        raise ValueError(f"{seed_dir} is not a frozen V8 plain-baseline artifact")
    fixed = manifest.get("fixed_task", {})
    if fixed.get("commitment_decision_mode") != "branch_value_v8" or int(fixed.get("branch_step", -1)) != 24:
        raise ValueError(f"{seed_dir} does not match the V8 branch-value task")
    endpoint = json.loads((seed_dir / "profile_stratified_endpoint.json").read_text(encoding="utf-8"))
    summary = endpoint.get("summary", {})
    if set(summary) != set(PROFILES):
        raise ValueError(f"{seed_dir} has incomplete profile support")
    return int(manifest["seed"]), summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed-dir", type=Path, action="append", required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("pass --execute")
    if args.out_dir.exists():
        raise FileExistsError(f"refusing to overwrite {args.out_dir}")

    loaded = [_load(path) for path in args.seed_dir]
    if len(loaded) != 3 or len({seed for seed, _ in loaded}) != 3:
        raise ValueError("G2B requires exactly three distinct development seeds")

    per_seed: dict[str, object] = {}
    profile_summary: dict[str, object] = {}
    for profile in PROFILES:
        cells = [(seed, summary[profile]) for seed, summary in loaded]
        profile_summary[profile] = {
            "future_service_required": int(cells[0][1]["future_service_required"]),
            "per_seed_success_rate": {str(seed): float(cell["success_rate"]) for seed, cell in cells},
            "per_seed_branch_reconstruct": {
                str(seed): float(cell["mean_branch_decision_reconstruct"]) for seed, cell in cells
            },
        }
    for seed, summary in loaded:
        successes = [float(summary[p]["success_rate"]) for p in PROFILES]
        choices = [float(summary[p]["mean_branch_decision_reconstruct"]) for p in PROFILES]
        per_seed[str(seed)] = {
            "balanced_profile_mean_success": float(np.mean(successes)),
            "intermediate_success": bool(0.1 <= float(np.mean(successes)) <= 0.9),
            "branch_reconstruct_by_profile": dict(zip(PROFILES, choices)),
            "relation_blind_branch_collapse": bool(max(choices) - min(choices) < 0.5),
        }

    all_intermediate = all(cell["intermediate_success"] for cell in per_seed.values())
    all_relation_blind = all(cell["relation_blind_branch_collapse"] for cell in per_seed.values())
    report = {
        "protocol": PROTOCOL,
        "artifact_class": "DEVELOPMENT_ONLY_BASELINE_CAPABILITY_GATE",
        "paper_evidence": False,
        "training_seeds": [seed for seed, _ in loaded],
        "requirements": {
            "all_three_seeds_have_balanced_non_saturated_success": all_intermediate,
            "all_four_public_profiles_are_endpoint_evaluated": True,
            "plain_mlp_shows_relation_blind_branch_collapse": all_relation_blind,
        },
        "per_seed": per_seed,
        "profiles": profile_summary,
        "interpretation": (
            "The matched MLP is neither globally unlearnable nor saturated on the balanced V8 task. "
            "Its collapsed branch action is the unresolved relation-value behaviour that a candidate "
            "method and semantic-shuffle ablation must change."
        ),
        "does_not_establish": [
            "that a relation-value candidate will improve success or reliability",
            "that the candidate mechanism is identifiable without a matched semantic shuffle",
            "paper-level performance evidence",
        ],
        "verdict": "V8_G2B_BASELINE_INTERMEDIATE_PASS" if all_intermediate and all_relation_blind else "V8_G2B_NOT_ESTABLISHED",
    }
    args.out_dir.mkdir(parents=True)
    (args.out_dir / "v8_g2b_baseline_capability_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
