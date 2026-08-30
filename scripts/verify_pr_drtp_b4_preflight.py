"""Zero-training checkpoint-load and asset-integrity preflight for PR-DRTP B4."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]
import run_phase_fl_single as fl  # noqa: E402
from run_pr_drtp_b4_evaluation import validate_assets  # noqa: E402


FREEZE = ROOT / "configs" / "pr_drtp_b4_feasibility_freeze.json"


def parameter_count(agent) -> int:
    return sum(parameter.numel() for parameter in agent.parameters())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--asset-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing preflight overwrite: {args.output}")
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    inventory, manifest = validate_assets(args.asset_root.resolve(), freeze)
    seed = min(inventory)
    counts = {}
    for arm in ("utr_sg", "drtp_sg"):
        agent = fl.build_agent(
            {"graph_encoder": "single", "hidden_dim": 115}, inventory[seed][arm], seed
        )
        counts[arm] = parameter_count(agent)
    result = {
        "protocol": "PR-DRTP-B4-PREFLIGHT-V1",
        "status": "PASS" if len(set(counts.values())) == 1 and next(iter(counts.values())) == 116728 else "FAIL",
        "training_started": False,
        "asset_checkpoint_count": manifest["checkpoint_count"],
        "checkpoint_load_seed": seed,
        "parameter_counts": counts,
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    if result["status"] != "PASS":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
