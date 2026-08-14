"""Create the fresh 100-pair development tape manifest for Stage MSR."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


TAPE_START = 380000
EPISODES = 100


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    args.output_root.mkdir(parents=True, exist_ok=True)
    payload = {
        "protocol": "PHASE-MSR-TAPE-V1",
        "episode_ids": list(range(TAPE_START, TAPE_START + EPISODES)),
        "conditions": ["nominal", "relay_failure"],
        "episodes_per_condition": EPISODES,
        "failure": {"failed_blue_agent": 1, "start_step": 44, "duration_steps": 80},
        "forbidden_namespaces": ["340000-340099", "350000-350049", "360000-360099", "370000-370049"],
        "canonical": False,
        "binding": "deterministic_episode_id_namespace",
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    manifest = {**payload, "tape_hash": hashlib.sha256(encoded).hexdigest()}
    path = args.output_root / "tape_manifest.json"
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        if existing.get("tape_hash") != manifest["tape_hash"]:
            raise RuntimeError("existing MSR tape manifest does not match frozen payload")
    else:
        path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
