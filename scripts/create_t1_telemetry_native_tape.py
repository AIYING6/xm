"""Create the prospective T1 development-only evaluation tape."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


PROTOCOL = "T1-TELEMETRY-NATIVE-DEVELOPMENT-TAPE-V1"
TAPE_START, EPISODES = 920_000, 100
CONDITIONS = {
    "nominal": None,
    "f0_seen_44_80": (44, 80),
    "timing_28_80": (28, 80), "timing_36_80": (36, 80),
    "timing_52_80": (52, 80), "timing_60_80": (60, 80),
    "duration_44_40": (44, 40), "duration_44_60": (44, 60),
    "duration_44_100": (44, 100), "duration_44_120": (44, 120),
    "compound_28_120": (28, 120), "compound_60_120": (60, 120),
}
FORBIDDEN = (
    "340000-340099", "350000-350049", "360000-360099", "370000-370049",
    "380000-380099", "410000-410099", "420000-420099", "430000-430099", "440000-440099",
)


def frozen_manifest() -> dict:
    payload = {
        "protocol": PROTOCOL,
        "episode_ids": list(range(TAPE_START, TAPE_START + EPISODES)),
        "conditions": [
            {"name": name, "failed_blue_agent": -1 if spec is None else 1,
             "start_step": 0 if spec is None else spec[0], "duration_steps": 0 if spec is None else spec[1]}
            for name, spec in CONDITIONS.items()
        ],
        "episodes_per_condition": EPISODES,
        "same_base_ids_across_conditions": True,
        "failure_semantics": "relay_node_1_edge_removal_at_onset_for_duration",
        "canonical": False,
        "held_out": False,
        "development_only": True,
        "binding": "deterministic_episode_id_namespace",
        "forbidden_namespaces": list(FORBIDDEN),
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    return {**payload, "tape_hash": digest}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("NO-GO: explicit --execute is required to create the T1 tape")
    manifest = frozen_manifest()
    args.output_root.mkdir(parents=True, exist_ok=True)
    path = args.output_root / "tape_manifest.json"
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        if existing.get("tape_hash") != manifest["tape_hash"]:
            raise RuntimeError("existing T1 tape differs from the frozen manifest")
    else:
        path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
