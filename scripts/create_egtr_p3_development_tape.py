"""Create the isolated EGTR P3 development-only tape manifest."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

PROTOCOL = "EGTR-P3-DEVELOPMENT-TAPE-V1"
TAPE_START = 520000
EPISODES = 100
CONDITIONS = {
    "nominal": None,
    "f0_seen_44_80": (44, 80),
    "timing_28_80": (28, 80),
    "timing_36_80": (36, 80),
    "timing_52_80": (52, 80),
    "timing_60_80": (60, 80),
    "duration_44_40": (44, 40),
    "duration_44_60": (44, 60),
    "duration_44_100": (44, 100),
    "duration_44_120": (44, 120),
    "compound_28_120": (28, 120),
    "compound_60_120": (60, 120),
}


def manifest() -> dict:
    payload = {
        "protocol": PROTOCOL,
        "episode_ids": list(range(TAPE_START, TAPE_START + EPISODES)),
        "conditions": [
            {"name": name, "failed_blue_agent": -1 if spec is None else 1,
             "start_step": 0 if spec is None else spec[0],
             "duration_steps": 0 if spec is None else spec[1]}
            for name, spec in CONDITIONS.items()
        ],
        "episodes_per_condition": EPISODES,
        "same_base_ids_across_conditions": True,
        "failure_semantics": "relay_node_1_edge_removal_at_onset_for_duration",
        "canonical": False,
        "development_only": True,
        "forbidden_namespaces": ["340000-430099", "500000-500099"],
        "future_confirmatory_not_generated": True,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {**payload, "tape_hash": hashlib.sha256(encoded).hexdigest()}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    data = manifest()
    args.output_root.mkdir(parents=True, exist_ok=True)
    path = args.output_root / "tape_manifest.json"
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        if existing.get("tape_hash") != data["tape_hash"]:
            raise RuntimeError("existing EGTR P3 tape differs from frozen payload")
    else:
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()
