"""Create the reserved, diagnostic-only Phase FL paired tape manifest."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


TAPE_START = 370000
EPISODES = 50
PROTOCOL = "PHASE-FL-TAPE-V1"


def canonical_hash(payload: dict) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    args.output_root.mkdir(parents=True, exist_ok=True)
    payload = {
        "protocol": PROTOCOL,
        "episode_ids": list(range(TAPE_START, TAPE_START + EPISODES)),
        "conditions": ["nominal", "relay_failure"],
        "episodes_per_condition": EPISODES,
        "failure": {"failed_blue_agent": 1, "start_step": 44, "duration_steps": 80},
        "forbidden_namespaces": ["340000-340099", "350000-350049", "360000-360099"],
        "canonical": False,
    }
    tape_hash = canonical_hash(payload)
    manifest = {**payload, "tape_hash": tape_hash, "binding": "deterministic_episode_id_namespace"}
    path = args.output_root / "tape_manifest.json"
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        if existing.get("tape_hash") != tape_hash:
            raise RuntimeError("existing FL tape manifest does not match frozen payload")
    else:
        path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
