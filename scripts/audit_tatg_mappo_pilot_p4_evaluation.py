"""Source-only readiness audit for the frozen TATG pilot endpoint evaluator."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FREEZE = ROOT / "configs" / "tatg_mappo_pilot_p4_evaluation_freeze.json"
TAPE = ROOT / "configs" / "tatg_mappo_pilot_development_tape.json"
EVALUATOR = ROOT / "scripts" / "run_tatg_mappo_pilot_evaluation.py"
LAUNCHER = ROOT / "scripts" / "launch_tatg_mappo_pilot_evaluation_autodl.sh"


def collect_checks() -> dict[str, bool]:
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    tape = json.loads(TAPE.read_text(encoding="utf-8"))
    source = EVALUATOR.read_text(encoding="utf-8")
    launcher = LAUNCHER.read_text(encoding="utf-8")
    return {
        "four_arms_and_three_training_seeds_are_exact": freeze["source"]["arms"] == ["utr_snapshot_sg", "tatg_cetm_utr", "tatg_snapshot_gru_utr", "tatg_zero_residual_utr"] and freeze["source"]["training_seeds"] == [75011, 75012, 75013],
        "only_fixed_update_3907_endpoint_is_accepted": freeze["source"]["fixed_endpoint_update"] == 3907 and "EXPECTED_UPDATES = 3907" in source and '"actor_critic_latest.pt"' in source,
        "frozen_development_tape_has_exactly_five_by_one_hundred_cells": tape["episode_start"] == 780000 and tape["episode_count"] == 100 and len(tape["conditions"]) == 5 and freeze["evaluation"]["total_episodes"] == 6000,
        "evaluation_refuses_incomplete_or_overwritten_inputs": 'manifest.get("status") != "completed"' in source and "refusing to overwrite fixed endpoint evaluation" in source,
        "temporal_actor_and_snapshot_baseline_have_distinct_deterministic_inference_paths": "TATGSequenceActorRunner" in source and "snapshot_action" in source and "deterministic=True" in source,
        "no_training_resume_or_checkpoint_selection_interface": "train_ri_gmappo" not in source and "optimizer.step" not in source and "--resume" not in launcher and "aggregate_" not in launcher,
        "launcher_requires_completed_training_and_writes_no_gate": "TATG_PILOT_TRAINING_COMPLETE.json" in launcher and "TATG_PILOT_FIXED_ENDPOINT_EVALUATION_COMPLETE" in launcher,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("refusing to write endpoint-evaluation audit without --execute")
    if args.output_dir.exists():
        raise FileExistsError(args.output_dir)
    checks = collect_checks()
    result = {
        "protocol": "TATG-MAPPO-FRESH-SEED-PILOT-P4-FIXED-ENDPOINT-EVALUATION-AUDIT-V1",
        "verdict": "TATG_PILOT_P4_EVALUATION_INTERFACE_READY" if all(checks.values()) else "TATG_PILOT_P4_EVALUATION_INTERFACE_NO_GO",
        "checks": checks,
        "training_started": False,
        "evaluation_started": False,
        "automatic_aggregation_or_continuation": False,
    }
    args.output_dir.mkdir(parents=True)
    (args.output_dir / "TATG_PILOT_P4_RESULT.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    (args.output_dir / "TATG_PILOT_P4_REPORT.md").write_text(
        "# TATG-MAPPO pilot P4 fixed endpoint evaluation audit\n\n"
        f"**Verdict:** `{result['verdict']}`.\n\n"
        "This is source inspection only: it creates no environment episodes, PPO updates, training continuation, checkpoint selection or pilot gate.\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
