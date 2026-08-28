"""Freeze the development-only tape reserved for H2 confirmation analysis."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / "configs" / "drtp_h2_confirmation_development_tape.json"


def digest(payload: dict) -> str:
    wire = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(wire).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists():
        raise FileExistsError(f"refusing to overwrite frozen tape: {output}")
    payload = {
        "protocol": "DRTP-B-LINE-H2-CONFIRMATION-DEVELOPMENT-TAPE-V1",
        "purpose": "H2_confirmation_diagnostic_only",
        "canonical": False,
        "held_out": False,
        "development_only": True,
        "post_hoc": False,
        "training_seed_namespace": [2801, 2802, 2803, 2804, 2805],
        "episode_ids": list(range(530000, 530100)),
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
        "forbidden_episode_namespaces": ["490000-490099", "500000-500099", "510000-510099", "520000-520099"],
    }
    payload["tape_hash"] = digest(payload)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "tape_hash": payload["tape_hash"]}, indent=2))


if __name__ == "__main__":
    main()
