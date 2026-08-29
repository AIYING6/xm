"""Freeze the non-canonical, development-only D5 pilot tape."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "configs" / "drtp_stable_v2_d5_pilot_tape.json"


def canonical(value: dict) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists():
        raise FileExistsError(f"refusing to overwrite frozen tape: {output}")
    tape = {
        "protocol": "DRTP-STABLE-V2-D5-PILOT-TAPE-V1",
        "purpose": "joint_high_return_downside_and_seed_reliability_development_gate",
        "canonical": False,
        "confirmatory": False,
        "held_out": False,
        "post_hoc": False,
        "development_only": True,
        "training_seed_namespace": [3201, 3202, 3203],
        "episode_ids": list(range(560000, 560100)),
        "episodes_per_condition": 100,
        "same_base_ids_across_conditions": True,
        "failure_semantics": "relay_node_1_edge_removal_at_onset_for_duration",
        "conditions": [
            {"name": "nominal", "failed_blue_agent": -1, "start_step": 44, "duration_steps": 0},
            {"name": "F0_44_80", "failed_blue_agent": 1, "start_step": 44, "duration_steps": 80},
            {"name": "T28_28_80", "failed_blue_agent": 1, "start_step": 28, "duration_steps": 80},
            {"name": "D120_44_120", "failed_blue_agent": 1, "start_step": 44, "duration_steps": 120},
            {"name": "C28_120", "failed_blue_agent": 1, "start_step": 28, "duration_steps": 120},
        ],
        "forbidden_episode_namespaces": [
            "420000-420099", "430000-430099", "440000-440099", "490000-490099",
            "500000-500099", "510000-510099", "520000-520099", "530000-530099",
            "540000-540099", "550000-550099",
        ],
    }
    tape["tape_hash"] = hashlib.sha256(canonical(tape)).hexdigest()
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(tape, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps({"output": str(output), "tape_hash": tape["tape_hash"]}, indent=2))


if __name__ == "__main__":
    main()
