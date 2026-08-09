"""Build the post-training v1.8 repair selector manifest without evaluation."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from select_formal_v1_8_repair_checkpoints import verify_and_select  # noqa: E402


RUNS = (
    ("corrected_ea_rg", "ea_rg"),
    ("corrected_wider_single_graph", "single"),
    ("matched_information_nongraph", "matched_nongraph"),
)
EXPECTED_UPDATES = [1, *range(10, 301, 10)]
PROTOCOL = "V1_8_FORMAL_PROTOCOL_REPAIR"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-root", type=Path, default=ROOT / "results" / "formal_v1_8_repair")
    parser.add_argument("--output", type=Path, default=ROOT / "docs" / "FORMAL_V1_8_REPAIR_SELECTION_MANIFEST.md")
    args = parser.parse_args()
    selections = []
    for method, prefix in RUNS:
        for seed in range(3):
            run_dir = args.results_root / f"{prefix}_seed{seed}"
            winner, candidates = verify_and_select(run_dir, method, seed, PROTOCOL)
            updates = [int(row["update"]) for row in candidates]
            if updates != EXPECTED_UPDATES:
                raise RuntimeError(f"INCOMPLETE_VALIDATION_SNAPSHOTS: {run_dir}: {updates}")
            selections.append({
                "method": method,
                "seed": seed,
                "selected_update": int(winner["update"]),
                "checkpoint_path": str(run_dir / winner["snapshot_path"]),
                "checkpoint_sha256": winner["snapshot_sha256"],
                "rmst80": winner["eval_rmst80"],
                "establishment_probability": winner["eval_establishment_probability"],
                "censoring_rate": winner["eval_censoring_rate"],
                "rmst220": winner["eval_rmst220"],
            })
    if args.output.exists():
        raise RuntimeError(f"refusing to overwrite frozen output: {args.output}")
    lines = [
        "# FORMAL_V1_8_REPAIR_SELECTION_MANIFEST",
        "",
        "**Status: checkpoint selection completed from training-time immutable artifacts only.**",
        "No confirmatory held-out evaluation was accessed.",
        "",
        "| method | seed | selected update | checkpoint SHA256 | RMST80 | establishment | censoring | RMST220 |",
        "|---|---:|---:|---|---:|---:|---:|---:|",
    ]
    for row in selections:
        lines.append(
            f"| {row['method']} | {row['seed']} | {row['selected_update']} | "
            f"`{row['checkpoint_sha256']}` | {row['rmst80']:.6g} | "
            f"{row['establishment_probability']:.6g} | {row['censoring_rate']:.6g} | {row['rmst220']:.6g} |"
        )
    lines.extend([
        "",
        "Each selected artifact was SHA256-verified against its append-only run manifest;",
        "method, seed, update, and protocol provenance were verified before applying the",
        "frozen selector: lower RMST80, higher establishment probability, lower censoring,",
        "lower RMST220, then earlier update on exact ties.",
        "",
        "```json",
        json.dumps(selections, indent=2, sort_keys=True),
        "```",
        "",
    ])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {args.output} with {len(selections)} frozen selections")


if __name__ == "__main__":
    main()
