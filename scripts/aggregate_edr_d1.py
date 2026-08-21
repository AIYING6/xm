"""Reproduce EDR-D1 seed-level and paired development summaries from raw records."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.aggregate_t1_telemetry_native_reference import cell_summary  # noqa: E402
from scripts.run_edr_d1_single import SEEDS  # noqa: E402
from scripts.telemetry_native_t0 import read_jsonl, sha256  # noqa: E402


PROTOCOL = "EDR-D1-DEVELOPMENT-AGGREGATE-V1"
METRICS = ("J_nominal", "J_F0", "J_OOD_mean", "J_OOD_worst", "collision", "timeout", "constraint_violation")


def seed_summary(root: Path, arm: str, seed: int) -> dict:
    path = root / "evaluations" / "final_1m" / arm / f"seed{seed}"
    manifest = json.loads((path / "manifest.json").read_text(encoding="utf-8"))
    raw, aggregates = path / "raw_step_telemetry.jsonl", path / "episode_aggregates.jsonl"
    if not manifest.get("source_closure_pass") or sha256(raw) != manifest["raw_step_telemetry_sha256"] or sha256(aggregates) != manifest["episode_aggregates_sha256"]:
        raise RuntimeError(f"raw source-closure failure: {path}")
    return cell_summary(read_jsonl(aggregates))


def average(rows: dict[int, dict]) -> dict:
    return {key: float(np.mean([value[key] for value in rows.values()])) for key in (*METRICS, "survival_to_onset_fraction", "failure_trigger_success_among_risk_set", "pre_trigger_collision_rate", "episode_length", "path_switch_count", "direct_path_fraction", "relay_path_fraction", "task_support_fraction", "legal_information_fraction", "mean_cache_age", "traveled_distance", "control_effort")}


def decision(edr: dict[int, dict], utr: dict[int, dict]) -> tuple[str, dict]:
    paired = {seed: {key: edr[seed][key] - utr[seed][key] for key in METRICS} for seed in SEEDS}
    favorable = [seed for seed in SEEDS if all(paired[seed][key] > 0 for key in ("J_F0", "J_OOD_mean", "J_OOD_worst")) and paired[seed]["timeout"] < 0]
    pooled_edr, pooled_utr = average(edr), average(utr)
    catastrophic = [seed for seed in SEEDS if paired[seed]["J_F0"] < -0.5 * abs(utr[seed]["J_F0"]) or paired[seed]["J_OOD_worst"] < -0.5 * abs(utr[seed]["J_OOD_worst"])]
    profile = {"favorable_seeds": favorable, "catastrophic_seeds": catastrophic, "pooled_difference": {key: pooled_edr[key] - pooled_utr[key] for key in METRICS}}
    if len(favorable) >= 4 and not catastrophic and all(profile["pooled_difference"][key] > 0 for key in ("J_F0", "J_OOD_mean", "J_OOD_worst")) and profile["pooled_difference"]["timeout"] < 0 and profile["pooled_difference"]["collision"] <= 0 and profile["pooled_difference"]["constraint_violation"] <= 0:
        return "A — EDR_DEV_PASS", profile
    if any(profile["pooled_difference"][key] > 0 for key in ("J_F0", "J_OOD_mean", "J_OOD_worst")) and not catastrophic:
        return "B — EDR_DEV_MIXED", profile
    return "C — EDR_DEV_FAIL", profile


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--edr-root", type=Path, required=True)
    parser.add_argument("--t1-root", type=Path, required=True)
    parser.add_argument("--docs-root", type=Path, default=ROOT / "docs")
    parser.add_argument("--artifacts-root", type=Path, default=ROOT / "artifacts" / "edr_d1")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("NO-GO: explicit --execute is required")
    if args.artifacts_root.exists():
        raise FileExistsError(f"refusing to overwrite: {args.artifacts_root}")
    edr = {seed: seed_summary(args.edr_root, "edr_sg", seed) for seed in SEEDS}
    utr = {seed: seed_summary(args.t1_root, "utr_sg", seed) for seed in SEEDS}
    final, profile = decision(edr, utr)
    pooled_edr, pooled_utr = average(edr), average(utr)
    args.artifacts_root.mkdir(parents=True)
    rows = []
    for seed in SEEDS:
        rows.append({"method": "EDR", "seed": seed, **{key: edr[seed][key] for key in METRICS}})
        rows.append({"method": "UTR", "seed": seed, **{key: utr[seed][key] for key in METRICS}})
    with (args.artifacts_root / "seed_results.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=("method", "seed", *METRICS)); writer.writeheader(); writer.writerows(rows)
    paired_rows = [{"seed": seed, **{key: edr[seed][key] - utr[seed][key] for key in METRICS}} for seed in SEEDS]
    with (args.artifacts_root / "paired_utr_comparison.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=("seed", *METRICS)); writer.writeheader(); writer.writerows(paired_rows)
    result = {"protocol": PROTOCOL, "final_decision": final, "training_seed_unit": "seed", "edr_per_seed": edr, "utr_per_seed": utr, "edr_pooled": pooled_edr, "utr_pooled": pooled_utr, "profile": profile}
    (args.artifacts_root / "eval_summary.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    manifest = {"protocol": PROTOCOL, "edr_root": str(args.edr_root), "t1_root": str(args.t1_root), "files": {path.name: sha256(path) for path in args.artifacts_root.iterdir()}}
    (args.artifacts_root / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    table = "\n".join(f"| {seed} | {edr[seed]['J_nominal']:.3f} | {edr[seed]['J_F0']:.3f} | {edr[seed]['J_OOD_mean']:.3f} | {edr[seed]['J_OOD_worst']:.3f} | {edr[seed]['timeout']:.3f} |" for seed in SEEDS)
    args.docs_root.joinpath("EDR_D1_FIVE_SEED_RESULTS.md").write_text(f"# EDR-D1 Five-Seed Results\n\n| Seed | J nominal | J F0 | J OOD mean | J OOD worst | Timeout |\n| --- | ---: | ---: | ---: | ---: | ---: |\n{table}\n", encoding="utf-8")
    args.docs_root.joinpath("EDR_D1_PAIRED_UTR_COMPARISON.md").write_text(f"# EDR-D1 Paired UTR Comparison\n\nFinal checkpoint-only paired seed comparison.\n\n```json\n{json.dumps(profile, indent=2)}\n```\n", encoding="utf-8")
    args.docs_root.joinpath("EDR_D1_OOD_SAFETY_ANALYSIS.md").write_text(f"# EDR-D1 OOD and Safety Analysis\n\n```json\n{json.dumps({'edr': pooled_edr, 'utr': pooled_utr}, indent=2)}\n```\n", encoding="utf-8")
    args.docs_root.joinpath("EDR_D1_FINAL_DECISION.md").write_text(f"# EDR-D1 Final Decision\n\n**Decision:** `{final}`\n\n```json\n{json.dumps(profile, indent=2)}\n```\n", encoding="utf-8")
    print(json.dumps({"status": "completed", "final_decision": final, "artifacts": str(args.artifacts_root)}, indent=2))


if __name__ == "__main__":
    main()
