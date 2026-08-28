"""Create the one-time additional unseen-condition DRTP evaluation tape."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


PROTOCOL = "DRTP-ADDITIONAL-UNSEEN-CONDITION-TAPE-V1"
TAPE_START, EPISODES = 510000, 100
CONDITIONS = {
    "unseen_t20_d80": (20, 80),
    "unseen_t68_d80": (68, 80),
    "unseen_t44_d20": (44, 20),
    "unseen_t44_d140": (44, 140),
    "unseen_c20_d140": (20, 140),
    "unseen_c68_d40": (68, 40),
}
SEEN_SUPPORT = {
    (44, 80), (28, 80), (36, 80), (52, 80), (60, 80),
    (44, 40), (44, 60), (44, 100), (44, 120), (28, 120), (60, 120),
}


def frozen_manifest() -> dict:
    if set(CONDITIONS.values()) & SEEN_SUPPORT:
        raise RuntimeError("unseen tape contains a training-support member")
    payload = {
        "protocol": PROTOCOL,
        "status": "frozen_before_outcome_collection",
        "episode_ids": list(range(TAPE_START, TAPE_START + EPISODES)),
        "conditions": [
            {"name": name, "failed_blue_agent": 1, "start_step": onset, "duration_steps": duration}
            for name, (onset, duration) in CONDITIONS.items()
        ],
        "episodes_per_condition": EPISODES,
        "same_base_ids_across_conditions": True,
        "failure_semantics": "relay_node_1_edge_removal_at_onset_for_duration",
        "training_support_excluded": [list(item) for item in sorted(SEEN_SUPPORT)],
        "held_out_condition_tuples": [list(item) for item in CONDITIONS.values()],
        "binding": "deterministic_episode_id_namespace",
        "canonical": False,
        "post_hoc_additional_evaluation": True,
        "original_confirmatory_ood": False,
        "forbidden_namespaces": ["490000-490099", "500000-500099"],
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {**payload, "tape_hash": hashlib.sha256(encoded).hexdigest()}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("NO-GO: explicit --execute is required to freeze the unseen tape")
    manifest = frozen_manifest()
    args.output_root.mkdir(parents=True, exist_ok=True)
    path = args.output_root / "additional_unseen_tape_manifest.json"
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        if existing.get("tape_hash") != manifest["tape_hash"]:
            raise RuntimeError("existing unseen tape differs from frozen payload")
    else:
        path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
