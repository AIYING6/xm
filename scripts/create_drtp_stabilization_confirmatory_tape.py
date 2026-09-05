"""Create the frozen final-method confirmation evaluation tape."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.drtp_stabilization_confirmation_contracts import cohort_names, cohort_spec  # noqa: E402

CONDITIONS = (
    ("nominal", -1, 0, 0), ("F0", 1, 44, 80), ("TE", 1, 28, 80),
    ("TL", 1, 52, 80), ("DS", 1, 44, 40), ("DL", 1, 44, 100),
    ("CP", 1, 28, 120),
)


def payload(cohort: str = "A") -> dict:
    spec = cohort_spec(cohort)
    body = {
        "protocol": spec["tape_protocol"], "cohort": cohort, "confirmatory": True, "development_only": False,
        "canonical": False, "training_access": "forbidden",
        "same_base_ids_across_conditions": True, "episode_ids": spec["episode_ids"],
        "episodes_per_condition": len(spec["episode_ids"]),
        "conditions": [
            {"name": name, "failed_blue_agent": agent, "start_step": onset, "duration_steps": duration}
            for name, agent, onset, duration in CONDITIONS
        ],
    }
    encoded = json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {**body, "tape_hash": hashlib.sha256(encoded).hexdigest()}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cohort", choices=cohort_names(), default="A")
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    args.output_root.mkdir(parents=True, exist_ok=True)
    path = args.output_root / "tape_manifest.json"
    frozen = payload(args.cohort)
    if path.exists() and json.loads(path.read_text(encoding="utf-8")) != frozen:
        raise RuntimeError("existing confirmatory tape differs from its frozen payload")
    path.write_text(json.dumps(frozen, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "created", "tape_hash": frozen["tape_hash"]}, indent=2))


if __name__ == "__main__":
    main()
