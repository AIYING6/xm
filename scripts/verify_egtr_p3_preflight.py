"""Mechanical pre-flight for the frozen EGTR P3 1M launch."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.drtp_topology_sampler import EGTRTopologySampler  # noqa: E402

SEEDS = [2501, 2502, 2503]
ARMS = {"utr_sg": "utr", "drtp_sg": "drtp", "egtr_sg": "egtr"}
TAPE_START, TAPE_END = 520000, 520099


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("NO-GO: explicit --execute is required")
    tape_path = args.output_root / "tape" / "tape_manifest.json"
    tape = json.loads(tape_path.read_text(encoding="utf-8"))
    assert tape["protocol"] == "EGTR-P3-DEVELOPMENT-TAPE-V1"
    assert tape["episode_ids"] == list(range(TAPE_START, TAPE_END + 1))
    assert tape["canonical"] is False and tape["development_only"] is True
    assert EGTRTopologySampler(9001, 3907).manifest()["protocol"] == "EGTR-DRTP-SG-MAPPO-CONTRACT-V1"
    assert EGTRTopologySampler(9001, 3907).manifest()["trust_region_after_projection"] is True
    assert not any((args.output_root / "runs" / arm / f"seed{seed}").exists()
                   for arm in ARMS for seed in SEEDS)
    result = {
        "protocol": "EGTR-P3-PREFLIGHT-V1",
        "methods": list(ARMS), "sampler_modes": ARMS,
        "seeds": SEEDS, "updates": 3907, "environment_steps": 1000192,
        "tape_hash": tape["tape_hash"], "tape_start": TAPE_START, "tape_end": TAPE_END,
        "parameter_count": 116728, "nominal_anchor": 0.5,
        "egtr_contract_protocol": "EGTR-DRTP-SG-MAPPO-CONTRACT-V1",
        "runtime_state_from_step_zero": True, "best_checkpoint_promotion": False,
        "status": "PASS",
    }
    args.output_root.mkdir(parents=True, exist_ok=True)
    path = args.output_root / "EGTR_P3_PREFLIGHT.json"
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
