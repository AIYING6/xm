#!/usr/bin/env python3
"""Audit whether frozen A/B episode assets can support TC-CRC research."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

import numpy as np


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def mean(values: list[float]) -> float:
    return float(np.mean(np.asarray(values, dtype=float)))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--contract", type=Path, required=True)
    ap.add_argument("--a-csv", type=Path, required=True)
    ap.add_argument("--b-csv", type=Path, required=True)
    ap.add_argument("--a-manifest", type=Path, required=True)
    ap.add_argument("--b-manifest", type=Path, required=True)
    ap.add_argument("--output-root", type=Path, required=True)
    ap.add_argument("--execute", action="store_true")
    args = ap.parse_args()
    if not args.execute:
        raise SystemExit("Refusing to run without --execute")
    c = json.loads(args.contract.read_text(encoding="utf-8"))
    if c.get("protocol") != "P7-TCARC-STAGE0-ASSET-FEASIBILITY-V1":
        raise ValueError("contract mismatch")
    if args.output_root.exists():
        raise FileExistsError(args.output_root)
    a, b = read_csv(args.a_csv), read_csv(args.b_csv)
    ma = json.loads(args.a_manifest.read_text(encoding="utf-8"))
    mb = json.loads(args.b_manifest.read_text(encoding="utf-8"))
    required = {"method", "train_seed", "topology_condition", "success_at_horizon",
                "scheduled_failure_onset", "scheduled_failure_duration", "tape_hash"}
    schema_ok = bool(a and b and required <= set(a[0]) and required <= set(b[0]))
    seeds_a = {int(r["train_seed"]) for r in a if r["method"] in c["methods"]}
    seeds_b = {int(r["train_seed"]) for r in b if r["method"] in c["methods"]}
    tapes_a = {r["tape_hash"] for r in a if r["method"] in c["methods"]}
    tapes_b = {r["tape_hash"] for r in b if r["method"] in c["methods"]}
    independent = seeds_a.isdisjoint(seeds_b) and tapes_a.isdisjoint(tapes_b)
    manifest_distinct = ma != mb

    rows = []
    all_strata_ok = True
    all_risks_nondegenerate = True
    miscalibrated_methods = 0
    improved_methods = 0
    lo, hi = c["nondegenerate_risk_interval"]
    for method in c["methods"]:
        aa = [r for r in a if r["method"] == method]
        bb = [r for r in b if r["method"] == method]
        global_a = mean([1.0 - float(r["success_at_horizon"]) for r in aa])
        all_risks_nondegenerate &= lo <= global_a <= hi
        groups = sorted({r["topology_condition"] for r in aa} & {r["topology_condition"] for r in bb})
        global_errors, stratified_errors = [], []
        for group in groups:
            ga = [r for r in aa if r["topology_condition"] == group]
            gb = [r for r in bb if r["topology_condition"] == group]
            ra = [1.0 - float(r["success_at_horizon"]) for r in ga]
            rb = [1.0 - float(r["success_at_horizon"]) for r in gb]
            count_ok = min(len(ga), len(gb)) >= c["minimum_rows_per_method_stratum"]
            event_ok = min(sum(ra), len(ra) - sum(ra), sum(rb), len(rb) - sum(rb)) >= c["minimum_positive_and_negative_events"]
            all_strata_ok &= count_ok and event_ok
            risk_a, risk_b = mean(ra), mean(rb)
            global_error, stratified_error = abs(risk_b - global_a), abs(risk_b - risk_a)
            global_errors.append(global_error); stratified_errors.append(stratified_error)
            rows.append({"method": method, "topology_condition": group, "n_a": len(ga), "n_b": len(gb),
                         "risk_a": risk_a, "risk_b": risk_b, "global_a_risk": global_a,
                         "global_conditional_abs_error": global_error,
                         "stratified_transfer_abs_error": stratified_error,
                         "positive_negative_event_gate": int(event_ok)})
        max_error = max(global_errors)
        if max_error >= c["minimum_global_conditional_max_error"]:
            miscalibrated_methods += 1
        if mean(stratified_errors) < mean(global_errors):
            improved_methods += 1

    checks = {
        "formal_schema_complete": schema_ok,
        "cohort_seeds_and_tapes_independent": independent,
        "manifests_distinct": manifest_distinct,
        "risk_endpoint_nondegenerate": all_risks_nondegenerate,
        "topology_strata_have_minimum_events": all_strata_ok,
        "legal_predeployment_features_available": schema_ok,
        "global_calibration_has_topology_conditional_error": miscalibrated_methods >= c["minimum_methods_showing_conditional_miscalibration"],
        "stratification_has_descriptive_value": improved_methods >= c["minimum_methods_where_stratification_reduces_mae"],
    }
    passed = all(checks.values())
    report = {
        "protocol": c["protocol"],
        "verdict": "TCARC_STAGE0_FEASIBILITY_PASS" if passed else "TCARC_STAGE0_FEASIBILITY_STOP",
        "checks": checks,
        "calibration_seeds": sorted(seeds_a), "test_seeds": sorted(seeds_b),
        "calibration_tape_hashes": sorted(tapes_a), "test_tape_hashes": sorted(tapes_b),
        "methods_with_global_conditional_miscalibration": miscalibrated_methods,
        "methods_where_stratification_reduces_transfer_mae": improved_methods,
        "training_started": False,
        "boundary": "This audit establishes endpoint/data feasibility only. It is not a conformal validity result and does not authorize policy-training claims."
    }
    args.output_root.mkdir(parents=True)
    write_csv(args.output_root / "topology_risk_transfer_a_to_b.csv", rows)
    (args.output_root / "P7_TCARC_STAGE0_REPORT.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (args.output_root / "P7_TCARC_STAGE0_REPORT.md").write_text(
        f"# P7 TC-CRC Stage-0 asset feasibility\n\n**`{report['verdict']}`**\n\n" +
        "\n".join(f"- {k}: {'PASS' if v else 'FAIL'}" for k, v in checks.items()) +
        f"\n\nGlobal conditional miscalibration: {miscalibrated_methods} method(s). "
        f"Topology stratification reduced A-to-B MAE for {improved_methods} method(s).\n",
        encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
