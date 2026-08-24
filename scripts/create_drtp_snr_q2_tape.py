"""Create the prospective SNR mechanism-comparator evaluation tape."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


PROTOCOL = "DRTP-SNR-Q2-MECHANISM-COMPARATOR-TAPE-V1"
TAPE_START, EPISODES = 500000, 100
SEEDS = (2401, 2402, 2403, 2404, 2405)
CONDITIONS = {
    "nominal": None,
    "f0_seen_44_80": (44, 80),
    "timing_28_80": (28, 80), "timing_36_80": (36, 80),
    "timing_52_80": (52, 80), "timing_60_80": (60, 80),
    "duration_44_40": (44, 40), "duration_44_60": (44, 60),
    "duration_44_100": (44, 100), "duration_44_120": (44, 120),
    "compound_28_120": (28, 120), "compound_60_120": (60, 120),
}
FORBIDDEN_NAMESPACES = tuple(
    ["340000-340099", "350000-350049", "360000-360099", "370000-370049"]
    + [f"{start}000-{start}099" for start in range(380, 510, 10) if start != 500]
)


def frozen_manifest() -> dict:
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
        "binding": "deterministic_episode_id_namespace",
        "prospective_mechanism_comparator": True,
        "canonical": False,
        "paired_training_seeds": list(SEEDS),
        "canonical_seeds_prohibited": [0, 1, 2, 3, 4],
        "forbidden_namespaces": list(FORBIDDEN_NAMESPACES),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {**payload, "tape_hash": hashlib.sha256(encoded).hexdigest()}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("NO-GO: comparator tape creation requires explicit --execute")
    manifest = frozen_manifest()
    args.output_root.mkdir(parents=True, exist_ok=True)
    path = args.output_root / "snr_comparator_tape_manifest.json"
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        if existing.get("tape_hash") != manifest["tape_hash"]:
            raise RuntimeError("existing comparator tape differs from frozen payload")
    else:
        path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
