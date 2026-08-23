"""Verify PAPER-Q2 evidence lineage, statistics, and immutable boundaries."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path
from statistics import mean, median, stdev


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "paper_q2_closeout"
TOL = 1e-9


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rows(rel: str) -> list[dict[str, str]]:
    with (ROOT / rel).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def quantile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * q
    low, high = math.floor(position), math.ceil(position)
    return ordered[low] + (ordered[high] - ordered[low]) * (position - low)


def mad(values: list[float]) -> float:
    center = median(values)
    return median([abs(value - center) for value in values])


def close(left: float, right: float, label: str) -> None:
    if not math.isclose(left, right, rel_tol=TOL, abs_tol=TOL):
        raise AssertionError(f"{label}: {left} != {right}")


def main() -> None:
    checks: list[str] = []
    manifest = json.loads((OUT / "evidence_chain_manifest.json").read_text(encoding="utf-8"))
    for source in manifest["sources"]:
        path = ROOT / source["path"]
        if not path.exists():
            raise FileNotFoundError(source["path"])
        if sha256(path) != source["sha256"]:
            raise AssertionError(f"hash mismatch: {source['path']}")
    checks.append(f"HASH_CHAIN_PASS:{len(manifest['sources'])}")

    p1_main = rows("artifacts/paper_q2_p1/main_table.csv")
    final_main = rows("artifacts/paper_q2_closeout/final_main_results.csv")
    if p1_main != final_main or len(final_main) != 5:
        raise AssertionError("final main table is not an identity-preserving P1 export")
    checks.append("MAIN_TABLE_IDENTITY_PASS")

    p1_seed = rows("artifacts/paper_q2_p1/seed_level_results.csv")
    final_seed = rows("artifacts/paper_q2_closeout/final_seed_level_results.csv")
    if p1_seed != final_seed:
        raise AssertionError("final seed table is not an identity-preserving P1 export")
    expected_seeds = {1901, 1902, 2001, 2002, 2003}
    if {int(row["seed"]) for row in final_seed} != expected_seeds or len(final_seed) != 5:
        raise AssertionError("required seed set is incomplete or duplicated")
    checks.append("ALL_FIVE_SEEDS_RETAINED_PASS")

    absolute = rows("artifacts/paper_q2_closeout/final_paired_absolute_results.csv")
    if len(absolute) != 10:
        raise AssertionError("expected ten absolute method-seed rows")
    by_pair = {(row["contract"], int(row["seed"]), row["method"]): row for row in absolute}
    metric_map = {
        "delta_nominal": "J_nominal",
        "delta_F0": "J_F0",
        "delta_OOD_mean": "J_OOD_mean",
        "delta_OOD_worst": "J_OOD_worst",
    }
    for seed_row in final_seed:
        contract = seed_row["contract"]
        seed = int(seed_row["seed"])
        utr = by_pair[(contract, seed, "UTR-SG")]
        drtp = by_pair[(contract, seed, "DRTP-SG")]
        for delta_name, absolute_name in metric_map.items():
            observed = float(drtp[absolute_name]) - float(utr[absolute_name])
            close(observed, float(seed_row[delta_name]), f"paired delta {seed} {delta_name}")
    checks.append("ABSOLUTE_TO_PAIRED_DELTAS_PASS")

    canonical = json.loads((ROOT / "artifacts/paper_q2_p1/statistical_summary.json").read_text(encoding="utf-8"))
    reliability = {row["metric"]: row for row in rows("artifacts/paper_q2_closeout/final_reliability_results.csv")}
    for metric in metric_map:
        values = [float(row[metric]) for row in final_seed]
        expected = {
            "mean": mean(values),
            "median": median(values),
            "std": stdev(values),
            "IQR": quantile(values, 0.75) - quantile(values, 0.25),
            "MAD": mad(values),
            "worst_delta": min(values),
        }
        source = canonical["primary_metrics"][metric]
        export = reliability[metric]
        for name, value in expected.items():
            close(value, float(source[name]), f"canonical stats {metric} {name}")
        close(expected["mean"], float(export["mean_delta_drtp_minus_utr"]), f"export mean {metric}")
        close(expected["median"], float(export["median_delta_drtp_minus_utr"]), f"export median {metric}")
        close(expected["std"], float(export["std"]), f"export std {metric}")
        close(expected["IQR"], float(export["iqr"]), f"export IQR {metric}")
        close(expected["MAD"], float(export["mad"]), f"export MAD {metric}")
        close(expected["worst_delta"], float(export["worst_delta"]), f"export worst {metric}")
        if export["wins"] != f"{sum(value > 0 for value in values)}/5":
            raise AssertionError(f"win count mismatch: {metric}")
    checks.append("SEED_LEVEL_STATISTICS_RECOMPUTED_PASS")

    stratified = rows("artifacts/paper_q2_closeout/final_stratified_statistics.csv")
    if len(stratified) != 8 or {(row["contract"], row["metric"]) for row in stratified} != {
        (contract, metric) for contract in ("development_3M", "heldout_10M") for metric in metric_map
    }:
        raise AssertionError("contract-stratified statistics are incomplete")
    if {int(row["n_training_seeds"]) for row in stratified if row["contract"] == "development_3M"} != {2}:
        raise AssertionError("development n must remain 2")
    if {int(row["n_training_seeds"]) for row in stratified if row["contract"] == "heldout_10M"} != {3}:
        raise AssertionError("held-out n must remain 3")
    checks.append("CONTRACT_STRATIFICATION_PASS")

    seed2002 = next(row for row in final_seed if int(row["seed"]) == 2002)
    if not all(float(seed2002[name]) < 0 for name in metric_map):
        raise AssertionError("seed2002 adverse outcome was weakened or removed")
    seed1902 = next(row for row in final_seed if int(row["seed"]) == 1902)
    if not (float(seed1902["delta_F0"]) < 0 and float(seed1902["delta_OOD_mean"]) < 0):
        raise AssertionError("seed1902 limitation was weakened or removed")
    checks.append("NEGATIVE_SEEDS_PRESERVED_PASS")

    decision = json.loads((OUT / "final_submission_decision.json").read_text(encoding="utf-8"))
    required_decisions = set(manifest["historical_decisions_required"])
    if not required_decisions.issubset(decision["historical_decisions_preserved"]):
        raise AssertionError("historical decisions were not preserved")
    if decision["new_algorithm_started"] or decision["seed_rescue_started"] or decision["remaining_training_budget"] != 0:
        raise AssertionError("closeout unexpectedly authorizes new science")
    checks.append("HISTORICAL_DECISIONS_AND_STOP_RULE_PASS")

    source_policy = rows("artifacts/paper_q2_closeout/manuscript_source_manifest.csv")
    legacy = next(row for row in source_policy if row["source_path"] == "paper_latex_3d_en/")
    if legacy["status"] != "legacy_quarantined":
        raise AssertionError("legacy recovery manuscript is not quarantined")
    if any(row["source_path"].startswith("paper_latex_3d_en/") and row["status"] == "authoritative" for row in source_policy):
        raise AssertionError("legacy manuscript became an authoritative evidence source")
    checks.append("LEGACY_EVIDENCE_QUARANTINE_PASS")

    p1_stats_doc = (ROOT / "docs/PAPER_Q2_P1_STATISTICAL_RESULTS.md").read_text(encoding="utf-8")
    if "| F0 | 3/5 | +26.404 | +29.804 | 99.467 | 125.952 | 74.461 | −113.951 |" not in p1_stats_doc:
        raise AssertionError("corrected F0 MAD is absent")
    if "| OOD worst | 4/5 | +31.479 | +23.688 | 87.658 | 85.074 | 68.938 | −97.100 |" not in p1_stats_doc:
        raise AssertionError("corrected OOD-worst MAD is absent")
    checks.append("STATISTICAL_TRANSCRIPTION_CORRECTION_PASS")

    audit = {
        "schema": "paper-q2-evidence-chain-audit-v1",
        "status": "PASS",
        "training_started": False,
        "checks": checks,
        "independent_unit": "training_seed",
        "statistical_boundary": "cross-stratum n=5 summary is descriptive only",
        "remaining_risks": [
            "development n=2 and held-out n=3 are small and contract-separated",
            "no fair external drop-in comparator",
            "seed2002 adverse reversal and mixed safety",
            "3-UAV simulation scope only",
        ],
    }
    with (OUT / "evidence_chain_audit.json").open(
        "w", encoding="utf-8", newline="\n"
    ) as handle:
        handle.write(json.dumps(audit, indent=2, ensure_ascii=False) + "\n")
    print(f"PAPER-Q2 evidence chain PASS ({len(checks)} checks)")


if __name__ == "__main__":
    main()
