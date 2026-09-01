"""Dependency-light cloud preflight for the explicitly authorized C2 pilot."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FREEZE = ROOT / "configs" / "drtp_c2_group_weighted_ppo_pilot_freeze.json"
TAPE = ROOT / "configs" / "drtp_c2_group_weighted_ppo_pilot_tape.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    freeze, tape = json.loads(FREEZE.read_text(encoding="utf-8")), json.loads(TAPE.read_text(encoding="utf-8"))
    source = (ROOT / "algorithms" / "ri_gmappo" / "simple_ri_gmappo.py").read_text(encoding="utf-8")
    all_seeds = freeze["cohorts"]["A"] + freeze["cohorts"]["B"]
    checks = {
        "explicit_authorization": freeze["authorization"]["training_authorized"] is True and freeze["authorization"]["evaluation_authorized"] is True,
        "exact_30_trajectories": len(all_seeds) == 10 and len(freeze["arms"]) == 3,
        "two_separate_clean_cohorts": all_seeds == list(range(4801, 4811)),
        "fixed_budget": freeze["budget"]["updates"] == 1953 and freeze["budget"]["environment_steps_per_trajectory"] == 499968,
        "candidate_only_changes_actor_weighting": freeze["candidate"]["sampler"] == "fixed_stratified_topology_sampler" and freeze["candidate"]["critic"] == "ordinary PPO",
        "lagged_state_persists_across_runtime_resume": all(token in source for token in ("group_weighted_actor_auto_lagged", '"group_weighted_actor_state"', "saved_weight_state")),
        "fresh_development_tape": tape["episode_start"] == 670000 and tape["episode_count"] == 100 and len(tape["conditions"]) == 5,
        "no_automatic_continuation": freeze["authorization"]["automatic_continuation"] is False,
    }
    status = "C2_CLOUD_PREFLIGHT_PASS" if all(checks.values()) else "C2_CLOUD_PREFLIGHT_FAIL"
    payload = {"status": status, "checks": checks, "hashes": {"freeze": sha256(FREEZE), "tape": sha256(TAPE)},
               "training_started": False, "evaluation_started": False, "automatic_continuation_started": False}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    if status != "C2_CLOUD_PREFLIGHT_PASS":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
