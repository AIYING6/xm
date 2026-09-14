"""Audit V8 plain-MAPPO task learnability after its frozen development run."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


PROTOCOL = "COMMITMENT-HANDOFF-3D-V8-G2-LEARNABILITY-AUDIT-V1"
CURRENT_PROFILES = ("current_compact", "current_delayed")
FUTURE_PROFILES = ("future_fresh", "future_durable")


def load_seed(seed_dir: Path) -> tuple[int, dict[str, object]]:
    manifest = json.loads((seed_dir / "run_manifest.json").read_text(encoding="utf-8"))
    if manifest.get("protocol") != "COMMITMENT-HANDOFF-3D-V8-PLAIN-MAPPO-G2-DEVELOPMENT-V1":
        raise ValueError(f"{seed_dir} does not use the frozen V8 source protocol")
    fixed = manifest.get("fixed_task", {})
    if fixed.get("commitment_decision_mode") != "branch_value_v8" or int(fixed.get("branch_step", -1)) != 24:
        raise ValueError(f"{seed_dir} does not match the V8 branch-value contract")
    endpoint = json.loads((seed_dir / "profile_stratified_endpoint.json").read_text(encoding="utf-8"))
    return int(manifest["seed"]), endpoint["summary"]


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
    if len(loaded) != 3 or len({seed for seed, _ in loaded}) != 3:
        raise ValueError("V8 G2 requires exactly three distinct development seeds")
    per_profile: dict[str, object] = {}
    for profile in CURRENT_PROFILES + FUTURE_PROFILES:
        cells = [(seed, summary[profile]) for seed, summary in loaded]
        successes = {str(seed): float(cell["success_rate"]) for seed, cell in cells}
        branch = {str(seed): float(cell["mean_branch_decision_reconstruct"]) for seed, cell in cells}
        per_profile[profile] = {
            "future_service_required": int(cells[0][1]["future_service_required"]),
            "per_seed_success_rate": successes,
            "mean_success_rate": float(np.mean(list(successes.values()))),
            "moderate_seed_count": int(sum(0.1 <= value <= 0.9 for value in successes.values())),
            "per_seed_branch_reconstruct": branch,
        }
    future_moderate = all(per_profile[p]["moderate_seed_count"] >= 2 for p in FUTURE_PROFILES)
    current_learned = all(per_profile[p]["mean_success_rate"] > 0.0 for p in CURRENT_PROFILES)
    current_retain = all(sum(value < 0.5 for value in per_profile[p]["per_seed_branch_reconstruct"].values()) >= 2 for p in CURRENT_PROFILES)
    future_reconstruct = all(sum(value > 0.5 for value in per_profile[p]["per_seed_branch_reconstruct"].values()) >= 2 for p in FUTURE_PROFILES)
    verdict = "V8_G2_LEARNABILITY_PASS" if future_moderate and current_learned and current_retain and future_reconstruct else "V8_G2_NOT_YET_ESTABLISHED"
    report = {
        "protocol": PROTOCOL,
        "artifact_class": "DEVELOPMENT_ONLY_TASK_LEARNABILITY_GATE",
        "paper_evidence": False,
        "training_seeds": [seed for seed, _ in loaded],
        "requirements": {
            "future_profiles_have_at_least_two_of_three_moderate_seeds": future_moderate,
            "current_profiles_have_positive_mean_success": current_learned,
            "current_profiles_retain_at_branch_in_at_least_two_seeds": current_retain,
            "future_profiles_reconstruct_at_branch_in_at_least_two_seeds": future_reconstruct,
        },
        "profiles": per_profile,
        "verdict": verdict,
    }
    args.out_dir.mkdir(parents=True)
    (args.out_dir / "v8_g2_learnability_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
