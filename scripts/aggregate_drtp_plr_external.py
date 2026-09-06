"""Joint descriptive report for frozen UTR, Original DRTP and PLR endpoints."""
from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
from scripts.drtp_plr_external_contracts import ARMS, SEEDS  # noqa: E402

PROTOCOL = "DRTP-PLR-EXTERNAL-FORMAL-REPORT-V1"; PERTURBED = ("F0", "TE", "TL", "DS", "DL", "CP")


def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as handle: return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(dict.fromkeys(key for row in rows for key in row))); writer.writeheader(); writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--evaluation-root", type=Path, required=True); parser.add_argument("--output-root", type=Path, required=True); parser.add_argument("--execute", action="store_true"); args = parser.parse_args()
    if not args.execute: raise SystemExit("explicit --execute is required")
    out = args.output_root / "diagnostics" / "plr_external_final" 
    if out.exists(): raise FileExistsError(f"refusing to overwrite {out}")
    manifest = json.loads((args.evaluation_root / "evaluation_manifest.json").read_text(encoding="utf-8"))
    if manifest.get("protocol") != "DRTP-PLR-EXTERNAL-FORMAL-ENDPOINT-EVALUATION-V1" or manifest.get("status") != "completed": raise RuntimeError("incompatible endpoint evaluation")
    cells = defaultdict(dict)
    for row in read_csv(args.evaluation_root / "per_seed_condition_summary.csv"): cells[(row["method"], int(row["train_seed"]))][row["condition"]] = row
    endpoint = []
    for arm in ARMS:
        for seed in SEEDS:
            cell = cells[(arm, seed)]
            if set(cell) != {"nominal", *PERTURBED}: raise RuntimeError(f"incomplete endpoint {arm}/seed{seed}")
            p = [cell[group] for group in PERTURBED]
            endpoint.append({"method": arm, "train_seed": seed, "J_nominal": float(cell["nominal"]["J"]), "J_perturbed": statistics.mean(float(row["J"]) for row in p), "J_perturbed_worst_condition": min(float(row["J"]) for row in p), "success_perturbed": statistics.mean(float(row["success_at_horizon"]) for row in p), "collision_perturbed": statistics.mean(float(row["collision"]) for row in p), "timeout_perturbed": statistics.mean(float(row["timeout"]) for row in p)})
    summaries = []
    for arm in ARMS:
        rows = [row for row in endpoint if row["method"] == arm]
        summaries.append({"method": arm, "n_training_seeds": len(rows), **{f"mean_{metric}": statistics.mean(row[metric] for row in rows) for metric in ("J_nominal", "J_perturbed", "J_perturbed_worst_condition", "success_perturbed", "collision_perturbed", "timeout_perturbed")}, "median_J_perturbed": statistics.median(row["J_perturbed"] for row in rows), "min_J_perturbed": min(row["J_perturbed"] for row in rows), "sample_sd_J_perturbed": statistics.stdev(row["J_perturbed"] for row in rows)})
    lookup = {(row["method"], row["train_seed"]): row for row in endpoint}; paired = []
    for baseline in ("utr_sg", "drtp_sg"):
        for seed in SEEDS:
            candidate, reference = lookup[("plr_style_sg", seed)], lookup[(baseline, seed)]
            paired.append({"candidate": "plr_style_sg", "baseline": baseline, "train_seed": seed, **{f"delta_{metric}": candidate[metric] - reference[metric] for metric in ("J_nominal", "J_perturbed", "J_perturbed_worst_condition", "success_perturbed", "collision_perturbed", "timeout_perturbed")}})
    out.mkdir(parents=True); write_csv(out / "PLR_EXTERNAL_PER_SEED_ENDPOINTS.csv", endpoint); write_csv(out / "PLR_EXTERNAL_METHOD_SUMMARY.csv", summaries); write_csv(out / "PLR_EXTERNAL_PAIRED_DELTAS.csv", paired)
    report = {"protocol": PROTOCOL, "verdict": "DRTP_PLR_EXTERNAL_COMPARATOR_REPORTED", "independent_unit": "training_seed", "methods": list(ARMS), "endpoint": "10m_only", "joint_interpretation_required": ["mean", "median", "lower_tail", "paired_direction", "collision", "timeout"], "automatic_algorithm_revision": False, "automatic_continuation": False}
    (out / "PLR_EXTERNAL_FINAL_REPORT.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (out / "PLR_EXTERNAL_FINAL_REPORT.md").write_text("# PLR-style external comparator report\n\n`DRTP_PLR_EXTERNAL_COMPARATOR_REPORTED`\n\nThis is a matched fixed-endpoint comparison, not an automatic algorithm-selection gate. Interpret all endpoint dimensions jointly.\n", encoding="utf-8")
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__": main()
