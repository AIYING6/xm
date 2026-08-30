"""Freeze the independent B5 observational development tape without evaluation."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "configs" / "drtp_b5_observational_tape.json"


def canonical(payload: dict) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def build() -> dict:
    payload = {
        "protocol": "DRTP-B5-OBSERVATIONAL-TAPE-V1",
        "canonical": False,
        "development_only": True,
        "held_out": False,
        "post_hoc": False,
        "purpose": "group_conditioned_credit_mechanism_diagnostic_only",
        "episode_ids": list(range(600000, 600100)),
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
        "training_seed_namespace": [3601, 3602, 3603, 3604, 3605],
        "forbidden_episode_namespaces": [
            "420000-440099", "490000-490099", "500000-500099", "510000-510099",
            "520000-520099", "530000-530099", "550000-550099", "560000-560099",
            "570000-570099", "580000-580099", "590000-590099"
        ],
    }
    return {**payload, "tape_hash": hashlib.sha256(canonical(payload)).hexdigest()}


def main() -> None:
    tape = build()
    if OUTPUT.exists():
        existing = json.loads(OUTPUT.read_text(encoding="utf-8"))
        if existing != tape:
            raise FileExistsError(f"refusing to rewrite a different frozen tape: {OUTPUT}")
    else:
        OUTPUT.write_text(json.dumps(tape, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUTPUT), "tape_hash": tape["tape_hash"]}, indent=2))


if __name__ == "__main__":
    main()
