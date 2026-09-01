"""Zero-training C2 design/readiness audit for group-weighted actor PPO."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def seed_mentions(seed: int) -> list[str]:
    """Find exact historical seed mentions, excluding the C2 contract itself."""
    found: list[str] = []
    pattern = re.compile(rf"(?<!\d){seed}(?!\d)")
    for base in (ROOT / "configs", ROOT / "docs", ROOT / "scripts", ROOT / "algorithms"):
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file() or path.suffix not in {".json", ".md", ".py", ".csv", ".txt"}:
                continue
            if any("drtp_c2_group_weighted_ppo" in part for part in path.parts):
                continue
            try:
                if pattern.search(path.read_text(encoding="utf-8", errors="ignore")):
                    found.append(str(path.relative_to(ROOT)))
            except OSError:
                found.append(str(path.relative_to(ROOT)))
    return found


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite audit: {args.output}")
    freeze_path = ROOT / "configs" / "drtp_c2_group_weighted_ppo_pilot_freeze.json"
    tape_path = ROOT / "configs" / "drtp_c2_group_weighted_ppo_pilot_tape.json"
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    candidates = [seed for cohort in freeze["cohorts"].values() for seed in cohort]
    seed_hits = {str(seed): seed_mentions(seed) for seed in candidates}
    source = (ROOT / "algorithms" / "ri_gmappo" / "simple_ri_gmappo.py").read_text(encoding="utf-8")
    checks = {
        "ten_clean_candidate_seeds": not any(seed_hits.values()) and len(set(candidates)) == 10,
        "two_separate_five_seed_cohorts": all(len(cohort) == 5 for cohort in freeze["cohorts"].values()),
        "three_frozen_arms_and_exact_budget": len(freeze["arms"]) == 3 and freeze["budget"]["trajectories"] == 30,
        "fixed_collection_and_actor_only_candidate": (
            freeze["candidate"]["sampler"] == "fixed_stratified_topology_sampler"
            and freeze["candidate"]["critic"] == "ordinary PPO"
        ),
        "auto_lagged_runtime_persistence_interface": all(
            token in source for token in (
                "group_weighted_actor_auto_lagged: bool = False",
                '"group_weighted_actor_state"',
                "runtime checkpoint is missing auto-lagged group-weight state",
            )
        ),
        "new_development_tape_isolated_from_known_namespaces": (
            json.loads(tape_path.read_text(encoding="utf-8"))["episode_start"] == 670000
            and freeze["evaluation"]["development_only"] is True
        ),
        "no_training_or_evaluation_authorized": not any(freeze["authorization"].values()),
        "two_cohort_gate_forbids_pooled_success_claim": "both pass separately" in freeze["gate"]["decision_rule"],
    }
    status = "C2_READY_FOR_AUTHORIZATION" if all(checks.values()) else "C2_NOT_READY"
    payload = {
        "protocol": freeze["protocol"],
        "status": status,
        "checks": checks,
        "candidate_seed_mentions": seed_hits,
        "freeze_sha256": sha256(freeze_path),
        "tape_sha256": sha256(tape_path),
        "training_started": False,
        "evaluation_started": False,
        "automatic_continuation_authorized": False,
        "mainline_a_modified": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    if status != "C2_READY_FOR_AUTHORIZATION":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
