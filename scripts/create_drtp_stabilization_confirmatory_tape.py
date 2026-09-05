"""Create the frozen final-method confirmation evaluation tape."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


PROTOCOL = "DRTP-STABILIZATION-CONFIRMATORY-TAPE-V1"
EPISODE_IDS = list(range(780000, 780100))
CONDITIONS = (
    ("nominal", -1, 0, 0), ("F0", 1, 44, 80), ("TE", 1, 28, 80),
    ("TL", 1, 52, 80), ("DS", 1, 44, 40), ("DL", 1, 44, 100),
    ("CP", 1, 28, 120),
)


def payload() -> dict:
    body = {
        "protocol": PROTOCOL, "confirmatory": True, "development_only": False,
        "canonical": False, "training_access": "forbidden",
        "same_base_ids_across_conditions": True, "episode_ids": EPISODE_IDS,
        "episodes_per_condition": len(EPISODE_IDS),
        "conditions": [
            {"name": name, "failed_blue_agent": agent, "start_step": onset, "duration_steps": duration}
            for name, agent, onset, duration in CONDITIONS
        ],
    }
    encoded = json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {**body, "tape_hash": hashlib.sha256(encoded).hexdigest()}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    args.output_root.mkdir(parents=True, exist_ok=True)
    path = args.output_root / "tape_manifest.json"
    frozen = payload()
    if path.exists() and json.loads(path.read_text(encoding="utf-8")) != frozen:
        raise RuntimeError("existing confirmatory tape differs from its frozen payload")
    path.write_text(json.dumps(frozen, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "created", "tape_hash": frozen["tape_hash"]}, indent=2))


if __name__ == "__main__":
    main()
