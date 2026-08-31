"""Dependency-light no-rollout integrity gate for Reliable-DRTP ensemble P1."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FREEZE = ROOT / "configs" / "reliable_drtp_ensemble_p1_freeze.json"
TAPE = ROOT / "configs" / "reliable_drtp_ensemble_p1_tape.json"
POOLING = ROOT / "algorithms" / "ri_gmappo" / "reliability_ensemble.py"
RUNNER = ROOT / "scripts" / "run_reliable_drtp_ensemble_p1.py"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    tape = json.loads(TAPE.read_text(encoding="utf-8"))
    bundles = [seeds for cohort in ("A", "B") for seeds in freeze["cohorts"][cohort].values()]
    members = [seed for seeds in bundles for seed in seeds]
    start, count = int(tape["episode_start"]), int(tape["episode_count"])
    source = RUNNER.read_text(encoding="utf-8")
    checks = {
        "explicit_authorization": freeze["authorization"]["member_training_authorized"] is True,
        "two_arms_only": set(freeze["arms"]) == {"e_utr", "e_drtp"},
        "six_k3_bundles": len(bundles) == 6 and all(len(bundle) == 3 for bundle in bundles),
        "exact_36_member_trajectories": len(members) * len(freeze["arms"]) == 36,
        "unique_clean_candidate_seeds": len(members) == len(set(members)) == 18 and 4610 not in members,
        "fixed_budget": freeze["training"]["updates"] == 1953 and freeze["training"]["environment_steps_per_member"] == 499968,
        "uniform_probability_pool": freeze["pooling"]["rule"] == "uniform_action_probability_mean" and freeze["pooling"]["evaluation_action_rule"] == "deterministic_argmax_of_pooled_probabilities",
        "no_distillation": freeze["distillation"] == {"implemented": False, "authorized": False},
        "no_auto_continuation": freeze["authorization"]["automatic_continuation"] is False,
        "development_tape_only": tape["development_only"] is True and tape["canonical"] is False and start == 650000 and count == 100,
        "training_does_not_read_tape": "read_tape()" not in source[source.index("def train("):source.index("def pooled_action(")],
        "no_member_selection_by_evaluation": "member_selection_uses_evaluation\": False" in source,
    }
    passed = all(checks.values())
    payload = {
        "status": "RELIABILITY_ENSEMBLE_P1_CLOUD_PREFLIGHT_PASS" if passed else "RELIABILITY_ENSEMBLE_P1_CLOUD_PREFLIGHT_FAIL",
        "checks": checks,
        "hashes": {"freeze": sha256(FREEZE), "tape": sha256(TAPE), "pooling": sha256(POOLING), "runner": sha256(RUNNER)},
        "zero_training_preflight": True,
        "evaluation_started": False,
        "distillation_started": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
