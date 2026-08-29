"""Create the independent S1 stabilization development-only evaluation tape."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "configs" / "drtp_stabilization_s1_development_tape.json"


def main() -> None:
    tape = {
        "protocol": "DRTP-STABILIZATION-S1-DEVELOPMENT-TAPE-V1",
        "development_only": True,
        "canonical": False,
        "confirmatory": False,
        "post_hoc": False,
        "episode_ids": list(range(530000, 530100)),
        "episodes_per_condition": 100,
        "same_base_ids_across_conditions": True,
        "conditions": [
            {"name": "nominal", "failed_blue_agent": -1, "start_step": 44, "duration_steps": 0},
            {"name": "F0_44_80", "failed_blue_agent": 1, "start_step": 44, "duration_steps": 80},
            {"name": "T28_28_80", "failed_blue_agent": 1, "start_step": 28, "duration_steps": 80},
            {"name": "D120_44_120", "failed_blue_agent": 1, "start_step": 44, "duration_steps": 120},
            {"name": "C28_120", "failed_blue_agent": 1, "start_step": 28, "duration_steps": 120},
        ],
        "failure_semantics": "relay_node_1_edge_removal_at_onset_for_duration",
        "forbidden_namespaces": ["420000-420099", "430000-430099", "440000-440099", "490000-490099", "500000-500099", "510000-510099"],
    }
    encoded = json.dumps(tape, sort_keys=True, separators=(",", ":")).encode("utf-8")
    tape["tape_hash"] = hashlib.sha256(encoded).hexdigest()
    OUT.write_text(json.dumps(tape, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"path": str(OUT), "tape_hash": tape["tape_hash"]}, indent=2))


if __name__ == "__main__":
    main()
