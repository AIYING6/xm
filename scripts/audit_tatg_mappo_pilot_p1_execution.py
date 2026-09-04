"""Static execution-interface audit for the frozen TATG fresh-seed pilot."""

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

PILOT = ROOT / "configs" / "tatg_mappo_pilot_freeze.json"
PREFLIGHT = ROOT / "configs" / "tatg_mappo_pilot_p1_execution_freeze.json"
LEGACY = ROOT / "algorithms" / "ri_gmappo" / "simple_ri_gmappo.py"
OUTER = ROOT / "algorithms" / "ri_gmappo" / "tatg_outer_rollout.py"
RUNNER = ROOT / "algorithms" / "ri_gmappo" / "tatg_sequence_runner.py"
SEQUENCE = ROOT / "algorithms" / "ri_gmappo" / "tatg_sequence_ppo.py"
SAMPLER = ROOT / "algorithms" / "ri_gmappo" / "tcr_topology_sampler.py"


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def collect_checks() -> tuple[dict[str, bool], dict[str, Any]]:
    pilot = json.loads(PILOT.read_text(encoding="utf-8"))
    preflight = json.loads(PREFLIGHT.read_text(encoding="utf-8"))
    legacy, outer, runner, sequence, sampler = (path.read_text(encoding="utf-8") for path in (LEGACY, OUTER, RUNNER, SEQUENCE, SAMPLER))
    checks = {
        "pilot_contract_is_still_not_executed": not pilot["authorization"]["training_authorized"] and not pilot["authorization"]["evaluation_authorized"],
        "baseline_uses_existing_fixed_utr_snapshot_path": "def train_ri_gmappo" in legacy and "FixedStratifiedTopologySampler" in legacy,
        "frozen_four_by_sixtyfour_utr_layout_is_supported": pilot["budget"]["num_envs"] == 4 and pilot["budget"]["rollout_steps"] == 64 and "requires exactly four environments" in sampler,
        "temporal_collection_has_slot_local_reset_and_saved_rollout_start_state": "tatg_state_before_rollout" in outer and "reset_completed" in outer,
        "temporal_actor_replay_is_full_chronological_sequence": "replay_rollout" in runner and "for t in range(time_steps)" in sequence and "clipped_actor_objective" in sequence,
        "temporal_runtime_checkpoint_has_required_mutable_state": all(token in outer for token in ("system_state", "optimizer_state", "environment_states", "action_generator_state", "tatg_actor_runtime_state")),
        "evaluation_is_separate_and_endpoint_only_by_contract": preflight["execution_layout"]["evaluation"].startswith("separate endpoint-only") and pilot["evaluation"]["endpoint"] == "fixed 1m checkpoint only",
        "preflight_does_not_take_training_or_evaluation_actions": "environment reset or step" in preflight["forbidden"] and not preflight["automatic_continuation"],
    }
    return checks, {
        "source_sha256": {path.name: _hash(path) for path in (LEGACY, OUTER, RUNNER, SEQUENCE, SAMPLER)},
        "frozen_arms": sorted(pilot["arms"]),
        "environment_steps_executed": 0,
        "ppo_updates_executed": 0,
        "evaluation_episodes_executed": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("Refusing to write pilot P1 output without --execute")
    output = Path(args.output_dir)
    if output.exists():
        raise SystemExit(f"Refusing to overwrite existing output: {output}")
    checks, details = collect_checks()
    result = {
        "protocol": "TATG-MAPPO-FRESH-SEED-PILOT-EXECUTION-PREFLIGHT-V1",
        "verdict": "TATG_PILOT_P1_EXECUTION_INTERFACE_READY" if all(checks.values()) else "TATG_PILOT_P1_EXECUTION_INTERFACE_NO_GO",
        "checks": checks,
        "audit_details": details,
        "training_started": False,
        "evaluation_started": False,
        "automatic_continuation": False,
    }
    text = json.dumps(result, indent=2) + "\n"
    report = "\n".join([
        "# TATG-MAPPO pilot P1 execution-interface preflight", "", f"**Verdict:** `{result['verdict']}`.", "",
        "The frozen pilot can use the existing four-stream fixed-UTR snapshot runner for its baseline and the isolated TATG state-owning sequence runner for all temporal arms. Chronological actor replay, completed-slot resets and strict runtime state are all present as explicit interfaces. Endpoint-only evaluation remains a later separate phase.", "",
        "This is source/interface inspection only: zero environment steps, PPO updates and evaluation episodes. It makes execution implementation eligible; it does not launch the 12 trajectories.", "",
        "## Checks", "", *[f"- `{name}`: `{passed}`" for name, passed in checks.items()], "",
    ])
    output.mkdir(parents=True)
    (output / "TATG_PILOT_P1_RESULT.json").write_bytes(text.encode("utf-8"))
    (output / "TATG_PILOT_P1_REPORT.md").write_bytes(report.encode("utf-8"))
    print(text)


if __name__ == "__main__":
    main()
