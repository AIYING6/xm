"""Audit V7 plain-MAPPO learnability before any candidate mechanism is built.

This gate intentionally accepts only fresh V7 development runs.  It asks
whether a capacity-controlled ordinary MLP MAPPO can learn the two public,
causal relay commitments without either universal failure or saturation.  A
pass is permission to design a candidate-method pilot, not paper evidence.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from envs.timed_handoff_intercept_3d_env import SERVICE_ENVELOPE_PROFILES  # noqa: E402


PROTOCOL = "COMMITMENT-HANDOFF-3D-V7-G2-LEARNABILITY-AUDIT-V1"
SOURCE_PROTOCOL = "COMMITMENT-HANDOFF-3D-V7-PLAIN-MAPPO-G2-DEVELOPMENT-V1"
FUTURE_PROFILES = ("future_fresh", "future_durable")
CURRENT_PROFILES = ("current_compact", "current_delayed")
MODERATE_INTERVAL = (0.10, 0.90)


def load_seed(seed_dir: Path) -> tuple[int, dict]:
    manifest_path = seed_dir / "run_manifest.json"
    endpoint_path = seed_dir / "profile_stratified_endpoint.json"
    if not manifest_path.is_file() or not endpoint_path.is_file():
        raise FileNotFoundError(f"missing V7 manifest or endpoint in {seed_dir}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("protocol") != SOURCE_PROTOCOL:
        raise ValueError(f"{seed_dir} is not a fresh V7 G2 run")
    fixed = manifest.get("fixed_task", {})
    if (
        fixed.get("commitment_decision_mode") != "staged_latched_v7"
        or fixed.get("handoff_safety_mode") != "blue_team_only"
        or int(fixed.get("authorization_start_step", -1)) != 0
        or int(fixed.get("authorization_deadline", -1)) != 16
        or int(fixed.get("authorization_decision_step", -1)) != 0
        or int(fixed.get("branch_step", -1)) != 24
    ):
        raise ValueError(f"{seed_dir} does not match the frozen V7 task contract")
    endpoint = json.loads(endpoint_path.read_text(encoding="utf-8"))
    return int(manifest["seed"]), endpoint["summary"]


def is_moderate(value: float) -> bool:
    return MODERATE_INTERVAL[0] <= value <= MODERATE_INTERVAL[1]


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
    loaded = [load_seed(path) for path in args.seed_dir]
    seeds = [seed for seed, _ in loaded]
    if len(seeds) != 3 or len(set(seeds)) != 3:
        raise ValueError("V7 G2 requires exactly three distinct development seeds")
    per_profile: dict[str, dict] = {}
    for profile in SERVICE_ENVELOPE_PROFILES:
        cells = [(seed, summary[profile]) for seed, summary in loaded]
        success = {str(seed): float(cell["success_rate"]) for seed, cell in cells}
        per_profile[profile] = {
            "future_service_required": int(cells[0][1]["future_service_required"]),
            "per_seed_success_rate": success,
            "mean_success_rate": float(np.mean(list(success.values()))),
            "moderate_seed_count": int(sum(is_moderate(value) for value in success.values())),
            "per_seed_authorization_reconstruct": {
                str(seed): float(cell["mean_authorization_decision_reconstruct"]) for seed, cell in cells
            },
            "per_seed_branch_reconstruct": {
                str(seed): float(cell["mean_branch_decision_reconstruct"]) for seed, cell in cells
            },
        }
    future_moderate = all(per_profile[p]["moderate_seed_count"] >= 2 for p in FUTURE_PROFILES)
    current_learned = all(per_profile[p]["mean_success_rate"] > 0.0 for p in CURRENT_PROFILES)
    early_retain = all(
        sum(value < 0.5 for value in per_profile[p]["per_seed_authorization_reconstruct"].values()) >= 2
        for p in FUTURE_PROFILES
    )
    late_reconstruct = all(
        sum(value > 0.5 for value in per_profile[p]["per_seed_branch_reconstruct"].values()) >= 2
        for p in FUTURE_PROFILES
    )
    verdict = "V7_G2_LEARNABILITY_PASS" if (future_moderate and current_learned and early_retain and late_reconstruct) else "V7_G2_NOT_YET_ESTABLISHED"
    report = {
        "protocol": PROTOCOL,
        "artifact_class": "DEVELOPMENT_ONLY_TASK_LEARNABILITY_GATE",
        "paper_evidence": False,
        "training_seeds": seeds,
        "source_training_protocol": SOURCE_PROTOCOL,
        "frozen_future_success_interval": list(MODERATE_INTERVAL),
        "requirements": {
            "future_profiles_have_at_least_two_of_three_moderate_seeds": future_moderate,
            "current_profiles_have_positive_mean_success": current_learned,
            "future_profiles_retain_early_in_at_least_two_seeds": early_retain,
            "future_profiles_reconstruct_after_branch_in_at_least_two_seeds": late_reconstruct,
        },
        "profiles": per_profile,
        "verdict": verdict,
        "interpretation": "A pass permits a candidate-method pilot only; it is not formal experimental evidence.",
    }
    args.out_dir.mkdir(parents=True)
    (args.out_dir / "v7_g2_learnability_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
