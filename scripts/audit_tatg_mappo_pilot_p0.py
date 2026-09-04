"""Zero-training preregistration audit for the first TATG fresh-seed pilot."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


FREEZE = ROOT / "configs" / "tatg_mappo_pilot_freeze.json"
TAPE = ROOT / "configs" / "tatg_mappo_pilot_development_tape.json"
UTR_SAMPLER = ROOT / "algorithms" / "ri_gmappo" / "tcr_topology_sampler.py"
REQUIRED_ARMS = {
    "utr_snapshot_sg",
    "tatg_cetm_utr",
    "tatg_snapshot_gru_utr",
    "tatg_zero_residual_utr",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def collect_checks() -> tuple[dict[str, bool], dict[str, Any]]:
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    tape = json.loads(TAPE.read_text(encoding="utf-8"))
    training = freeze["training_seeds"]
    replication = freeze["reserved_independent_replication_seeds"]
    confirmatory = freeze["reserved_confirmatory_seeds"]
    budget = freeze["budget"]
    forbidden = tape["forbidden_episode_namespaces"]
    sampler_source = UTR_SAMPLER.read_text(encoding="utf-8")
    checks = {
        "three_fresh_matched_training_seeds_are_frozen": training == [75011, 75012, 75013],
        "future_replication_and_confirmation_seed_namespaces_are_disjoint": not (
            set(training) & set(replication) or set(training) & set(confirmatory) or set(replication) & set(confirmatory)
        ) and len(replication) == len(confirmatory) == 5,
        "four_required_arms_are_exactly_frozen": set(freeze["arms"]) == REQUIRED_ARMS,
        "all_arms_use_fixed_utr_and_no_adaptive_sampler": "fixed UTR" in freeze["training"]["exposure"]
        and "no DRTP, EGTR, adaptive sampler" in freeze["training"]["sampler"],
        "rollout_layout_matches_existing_fixed_utr_sampler": budget["num_envs"] == 4
        and budget["rollout_steps"] == 64
        and "requires exactly four environments" in sampler_source,
        "candidate_and_controls_share_one_chronological_actor_update_contract": "full chronological [time, environment] replay"
        in freeze["training"]["ppo"]["actor"],
        "critic_and_environment_semantics_are_frozen": freeze["training"]["critic"].startswith("existing architecturally unchanged")
        and freeze["training"]["reward"] == "unchanged"
        and freeze["training"]["transition_semantics"] == "unchanged",
        "budget_and_fixed_endpoint_are_exact": budget["environment_steps_per_trajectory"] == budget["num_envs"] * budget["rollout_steps"] * budget["updates"]
        and budget["environment_steps_per_trajectory"] == 1_000_192
        and budget["fixed_endpoint_update"] == budget["updates"]
        and budget["trajectories"] == 12,
        "development_tape_is_new_fixed_and_offline": tape["development_only"]
        and tape["episode_start"] == 780000
        and tape["episode_count"] == 100
        and "780000-780099" not in forbidden
        and len(tape["conditions"]) == 5,
        "gate_requires_candidate_direction_and_not_control_pooling": "strictly positive" in freeze["pilot_gate"]["required"][0]
        and "not below either temporal control" in freeze["pilot_gate"]["required"][2]
        and "pooled" not in freeze["pilot_gate"]["rule"],
        "no_training_or_evaluation_is_started_by_this_audit": not freeze["authorization"]["training_authorized"]
        and not freeze["authorization"]["evaluation_authorized"]
        and not freeze["authorization"]["automatic_continuation"],
    }
    return checks, {
        "frozen_training_seeds": training,
        "reserved_independent_replication_seeds": replication,
        "arms": sorted(freeze["arms"]),
        "environment_steps_per_trajectory": budget["environment_steps_per_trajectory"],
        "total_environment_steps_if_authorized": budget["total_environment_steps"],
        "freeze_sha256": _sha256(FREEZE),
        "development_tape_sha256": _sha256(TAPE),
        "environment_steps_executed": 0,
        "ppo_updates_executed": 0,
        "evaluation_episodes_executed": 0,
    }


def render_report(result: dict[str, Any]) -> str:
    lines = [
        "# TATG-MAPPO fresh-seed pilot P0 preregistration audit",
        "",
        f"**Verdict:** `{result['verdict']}`.",
        "",
        "The first performance experiment is now defined before any TATG policy training: three new matched training seeds, a frozen one-million-step endpoint, fixed UTR exposure, CETM, snapshot-actor UTR and two parameter-matched temporal controls. The central critic, reward and environment semantics are fixed. CETM actor epochs must replay whole rollouts chronologically; the snapshot baseline keeps its ordinary PPO path.",
        "",
        "The 100-episode-per-condition development tape is offline-only, uses a new episode namespace and is read only after every arm reaches the fixed endpoint. No milestone can be promoted by return. The pilot direction rule requires CETM to improve the paired UTR primary metric on average, avoid a new zero-success seed, preserve nominal success within the frozen tolerance and not be below either temporal control on the cohort mean.",
        "",
        "This audit ran no environment step, PPO update or evaluation episode. It does not claim efficacy and does not start the pilot. A pass merely makes the exact 12-trajectory pilot eligible for separate execution authorization. A pilot failure closes CETM without tuning; a pilot pass requires a separately authorized five-seed independent replication.",
        "",
        "## Checks",
        "",
    ]
    lines.extend(f"- `{name}`: `{passed}`" for name, passed in result["checks"].items())
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("Refusing to write pilot P0 output without --execute")
    output = Path(args.output_dir)
    if output.exists():
        raise SystemExit(f"Refusing to overwrite existing output: {output}")
    checks, details = collect_checks()
    result = {
        "protocol": "TATG-MAPPO-FRESH-SEED-PILOT-P0-PREREGISTRATION-AUDIT-V1",
        "verdict": "TATG_PILOT_P0_PREREGISTRATION_READY" if all(checks.values()) else "TATG_PILOT_P0_PREREGISTRATION_NO_GO",
        "checks": checks,
        "audit_details": details,
        "training_started": False,
        "evaluation_started": False,
        "automatic_continuation": False,
    }
    output.mkdir(parents=True)
    (output / "TATG_PILOT_P0_RESULT.json").write_bytes((json.dumps(result, indent=2) + "\n").encode("utf-8"))
    (output / "TATG_PILOT_P0_REPORT.md").write_bytes(render_report(result).encode("utf-8"))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
