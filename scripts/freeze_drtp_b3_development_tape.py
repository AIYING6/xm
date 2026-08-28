"""Freeze the non-canonical, development-only B3 diagnostic evaluation tape."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "configs" / "drtp_b3_development_tape.json"


def canonical(value: dict) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists():
        raise FileExistsError(f"refusing to overwrite frozen tape: {output}")
    episode_ids = list(range(520000, 520100))
    tape = {
        "protocol": "DRTP-B-LINE-B3-DEVELOPMENT-TAPE-V1",
        "purpose": "mechanism_diagnostic_only",
        "canonical": False,
        "held_out": False,
        "post_hoc": False,
        "development_only": True,
        "training_seed_namespace": [2701, 2702, 2703],
        "episode_ids": episode_ids,
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
        "forbidden_episode_namespaces": ["490000-490099", "500000-500099", "510000-510099"],
    }
    tape["tape_hash"] = hashlib.sha256(canonical(tape)).hexdigest()
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(tape, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(output), "tape_hash": tape["tape_hash"]}, indent=2))


if __name__ == "__main__":
    main()
