"""Create the isolated development-only tape for Mechanism Experiment V1."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


PROTOCOL = "DRTP-TRAINING-FAILURE-MECHANISM-V1-DIAGNOSTIC-TAPE"
EPISODES_PER_CONDITION = 100
CONDITIONS = (
    ("nominal", -1, 0, 0),
    ("F0", 1, 44, 80),
    ("T28", 1, 28, 80),
    ("D120", 1, 44, 120),
    ("C28-120", 1, 28, 120),
)


def build_manifest() -> dict:
    episodes = []
    for condition_index, (name, failed_agent, onset, duration) in enumerate(CONDITIONS):
        for local_id in range(EPISODES_PER_CONDITION):
            episodes.append({
                "episode_id": 260000 + condition_index * 1000 + local_id,
                "condition": name,
                "condition_index": condition_index,
                "local_id": local_id,
                "failed_blue_agent": failed_agent,
                "failure_start_step": onset,
                "failure_duration_steps": duration,
            })
    payload = {
        "protocol": PROTOCOL,
        "version": 1,
        "purpose": "development-only failure-mechanism diagnosis; not held-out or canonical",
        "episodes_per_condition": EPISODES_PER_CONDITION,
        "conditions": [
            {"name": name, "failed_blue_agent": agent, "failure_start_step": onset,
             "failure_duration_steps": duration}
            for name, agent, onset, duration in CONDITIONS
        ],
        "episodes": episodes,
        "matched_pseudo_onset": 44,
        "failure_event_window": {"pre_steps": 20, "post_steps": 60},
        "training_seeds": [2601, 2602, 2603],
        "methods": ["utr_sg", "drtp_sg"],
        "canonical": False,
        "held_out": False,
        "historical_tapes_reused": False,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {**payload, "tape_hash": hashlib.sha256(encoded).hexdigest()}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("NO-GO: use --execute to create the frozen tape")
    manifest = build_manifest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.exists():
        existing = json.loads(args.output.read_text(encoding="utf-8"))
        if existing.get("tape_hash") != manifest["tape_hash"]:
            raise RuntimeError("existing mechanism tape differs from frozen payload")
    else:
        args.output.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
