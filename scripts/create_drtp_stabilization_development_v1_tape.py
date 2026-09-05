"""Create the isolated fixed development tape for Global-Anchored EGTR V1."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


PROTOCOL = "DRTP-STABILIZATION-DEVELOPMENT-V1-TAPE"
EPISODE_IDS = list(range(760000, 760100))
CONDITIONS = (
    ("nominal", -1, 0, 0),
    ("F0", 1, 44, 80),
    ("TE", 1, 28, 80),
    ("DL", 1, 44, 120),
    ("CP", 1, 60, 120),
)


def payload() -> dict:
    data = {
        "protocol": PROTOCOL,
        "development_only": True,
        "canonical": False,
        "training_access": "forbidden",
        "same_base_ids_across_conditions": True,
        "episode_ids": EPISODE_IDS,
        "episodes_per_condition": len(EPISODE_IDS),
        "conditions": [
            {"name": name, "failed_blue_agent": agent, "start_step": onset, "duration_steps": duration}
            for name, agent, onset, duration in CONDITIONS
        ],
    }
    encoded = json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {**data, "tape_hash": hashlib.sha256(encoded).hexdigest()}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    args.output_root.mkdir(parents=True, exist_ok=True)
    path = args.output_root / "tape_manifest.json"
    data = payload()
    if path.exists() and json.loads(path.read_text(encoding="utf-8")) != data:
        raise RuntimeError("existing V1 development tape differs from frozen payload")
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "created", "tape_hash": data["tape_hash"]}, indent=2))


if __name__ == "__main__":
    main()
