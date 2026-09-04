"""Source-only audit of the frozen TATG pilot runner."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

RUNNER = ROOT / "scripts" / "run_tatg_mappo_pilot_single.py"
FREEZE = ROOT / "configs" / "tatg_mappo_pilot_p2_runner_freeze.json"
PILOT = ROOT / "configs" / "tatg_mappo_pilot_freeze.json"


def collect_checks() -> tuple[dict[str, bool], dict[str, object]]:
    source = RUNNER.read_text(encoding="utf-8")
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    pilot = json.loads(PILOT.read_text(encoding="utf-8"))
    checks = {
        "four_frozen_arms_present": all(name in source for name in pilot["arms"]),
        "fixed_utr_layout_is_exact": "NUM_ENVS = 4" in source and "ROLLOUT_STEPS = 64" in source and "UPDATES = 3907" in source,
        "baseline_reuses_existing_snapshot_runner": "train_ri_gmappo(cfg)" in source,
        "temporal_arms_use_fixed_sampler_at_initial_and_completed_resets": source.count("sampler.select(") >= 2 and "on_before_reset=apply_next_selection" in source,
        "temporal_actor_replay_is_chronological": "runner.replay_rollout(" in source and "clipped_actor_objective(" in source,
        "critic_is_updated_without_changing_its_architecture": "system.critic_value(" in source and "TATGActorCriticSystem" in source,
        "runtime_payload_contains_sampler_episode_and_rng_state": all(token in source for token in ("sampler_state", "episode_counts", "action_generator_state", "environment_states", "tatg_actor_runtime_state")),
        "runner_has_no_evaluation_tape_import_or_evaluate_command": "development_tape" not in source and '"evaluate"' not in source,
        "training_requires_explicit_execute": "refusing to train without --execute" in source,
        "freeze_keeps_execution_unstarted": freeze["status"] == "IMPLEMENTED_NOT_EXECUTED" and not pilot["authorization"]["training_authorized"],
    }
    return checks, {"runner_sha256": hashlib.sha256(RUNNER.read_bytes()).hexdigest(), "environment_steps_executed": 0, "ppo_updates_executed": 0, "evaluation_episodes_executed": 0}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("refusing to write audit output without --execute")
    output = Path(args.output_dir)
    if output.exists():
        raise SystemExit(f"refusing to overwrite existing output: {output}")
    checks, details = collect_checks()
    result = {"protocol": "TATG-MAPPO-FRESH-SEED-PILOT-RUNNER-AUDIT-V1", "verdict": "TATG_PILOT_P2_RUNNER_IMPLEMENTED" if all(checks.values()) else "TATG_PILOT_P2_RUNNER_NO_GO", "checks": checks, "details": details, "training_started": False, "evaluation_started": False, "automatic_continuation": False}
    output.mkdir(parents=True)
    (output / "TATG_PILOT_P2_RESULT.json").write_bytes((json.dumps(result, indent=2) + "\n").encode("utf-8"))
    (output / "TATG_PILOT_P2_REPORT.md").write_bytes(("# TATG-MAPPO pilot P2 runner audit\n\n**Verdict:** `" + result["verdict"] + "`.\n\nThis is source inspection only: 0 environment steps, PPO updates and evaluation episodes.\n").encode("utf-8"))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
