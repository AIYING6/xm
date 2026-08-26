"""Freeze the REL-A0 multi-tape manifests without running environments."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


TAPES = {"T0": 440000, "T1": 450000, "T2": 460000, "T3": 470000, "T4": 480000}
EPISODES = 100
FORBIDDEN = ["340000-340099", "350000-350049", "360000-360099", "370000-370049",
             "380000-380099", "410000-410099", "420000-420099", "430000-430099"]


def digest(payload: dict) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--output-root", type=Path, required=True)
    p.add_argument("--source-t0", type=Path, required=True)
    p.add_argument("--execute", action="store_true")
    args = p.parse_args()
    if not args.execute:
        raise SystemExit("NO-GO: explicit --execute is required")
    source = json.loads(args.source_t0.read_text(encoding="utf-8"))
    expected = ["nominal", "f0", "timing", "duration", "compound"]
    if source.get("episode_ids") != list(range(440000, 440100)):
        raise RuntimeError("T0 source episode namespace is not 440000-440099")
    if [c["name"] for c in source.get("conditions", [])] != expected:
        raise RuntimeError("T0 source conditions differ from the frozen S1-A condition set")
    args.output_root.mkdir(parents=True, exist_ok=True)
    index = {"protocol": "DRTP-REL-A0-MULTI-TAPE-V1", "canonical": False,
             "development_only": True, "tapes": {}}
    for label, start in TAPES.items():
        payload = {
            "protocol": "DRTP-REL-A0-MULTI-TAPE-V1",
            "tape_label": label,
            "episode_ids": list(range(start, start + EPISODES)),
            "conditions": source["conditions"],
            "episodes_per_condition": EPISODES,
            "same_episode_ids_across_conditions": True,
            "failure_semantics": "frozen S2 relay node failure",
            "canonical": False,
            "development_only": True,
            "binding": "deterministic_episode_id_namespace",
            "forbidden_namespaces": FORBIDDEN,
        }
        record = {**payload, "tape_hash": digest(payload)}
        path = args.output_root / f"{label}_manifest.json"
        if path.exists():
            old = json.loads(path.read_text(encoding="utf-8"))
            if old.get("tape_hash") != record["tape_hash"]:
                raise RuntimeError(f"existing {label} tape differs")
        else:
            path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        index["tapes"][label] = {"path": str(path), "start": start, "end": start + 99,
                                  "tape_hash": record["tape_hash"]}
    (args.output_root / "tape_index.json").write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(index, indent=2))


if __name__ == "__main__":
    main()
