"""Create the frozen development-only diagnostic tape manifest for S1."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


TAPE_START = 440000
EPISODES = 100
CONDITIONS = {
    "nominal": None,
    "f0": (44, 80),
    "timing": (28, 80),
    "duration": (44, 40),
    "compound": (60, 120),
}


def manifest() -> dict:
    payload = {
        "protocol": "DRTP-SEED-S1-DIAGNOSTIC-TAPE-V1",
        "episode_ids": list(range(TAPE_START, TAPE_START + EPISODES)),
        "conditions": [
            {
                "name": name,
                "failed_blue_agent": -1 if spec is None else 1,
                "failure_start_step": None if spec is None else spec[0],
                "failure_duration_steps": None if spec is None else spec[1],
            }
            for name, spec in CONDITIONS.items()
        ],
        "episodes_per_condition": EPISODES,
        "same_episode_ids_across_conditions": True,
        "failure_semantics": "frozen S2 relay node failure",
        "canonical": False,
        "development_only": True,
        "forbidden_namespaces": [
            "340000-340099", "350000-350049", "360000-360099", "370000-370049",
            "380000-380099", "410000-410099", "420000-420099", "430000-430099",
        ],
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {**payload, "tape_hash": hashlib.sha256(encoded).hexdigest()}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=Path("artifacts/drtp_seed_s1"))
    args = parser.parse_args()
    args.output_root.mkdir(parents=True, exist_ok=True)
    payload = manifest()
    path = args.output_root / "diagnostic_tape_manifest.json"
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        if existing.get("tape_hash") != payload["tape_hash"]:
            raise RuntimeError("existing S1 diagnostic tape differs from frozen payload")
    else:
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()

