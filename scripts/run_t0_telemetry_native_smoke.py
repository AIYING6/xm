"""Run the zero-training T0 telemetry-native evidence-chain smoke test."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.telemetry_native_t0 import F0, NOMINAL, PROTOCOL, write_evidence_bundle


TECHNICAL_SMOKE_IDS = (910000, 910001)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=Path("artifacts/t0_telemetry_native_smoke"))
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("T0 smoke is write-producing; pass --execute")
    plans = [(episode_id, scenario) for episode_id in TECHNICAL_SMOKE_IDS for scenario in (NOMINAL, F0)]
    manifest = write_evidence_bundle(args.output_root.resolve(), plans)
    print(json.dumps({"protocol": PROTOCOL, "status": "completed", **manifest}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
