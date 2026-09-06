"""Materialize the frozen PLR external-comparator endpoint tape."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts.drtp_plr_external_contracts import tape_payload


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--output-root", type=Path, required=True); args = parser.parse_args()
    args.output_root.mkdir(parents=True, exist_ok=True)
    target, payload = args.output_root / "tape_manifest.json", tape_payload()
    if target.exists() and json.loads(target.read_text(encoding="utf-8")) != payload:
        raise RuntimeError("existing PLR tape differs from frozen payload")
    target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "created", "tape_hash": payload["tape_hash"]}, indent=2))


if __name__ == "__main__": main()
