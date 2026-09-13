"""Audit whether the commitment-level task is suitable for method pilots.

This is a development gate, not a performance comparison.  It accepts only
context-stratified, read-only endpoint evaluations of plain MAPPO checkpoints.
The gate prevents a formal method study from starting when the control task is
either unlearnable (all-zero performance) or saturated (near-certain success).
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


PROTOCOL = "COMMITMENT-HANDOFF-3D-G2-LEARNABILITY-AUDIT-V1"
CONTEXTS = ("current_authorization", "postbranch_refresh")
MIN_SUCCESS = 0.20
MAX_SUCCESS = 0.80
MIN_SEEDS_PER_CONTEXT = 2


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--seed-dir",
        action="append",
        type=Path,
        required=True,
        help="Completed plain-MAPPO run directory; repeat once per independent seed.",
    )
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    return parser.parse_args()


def read_seed(seed_dir: Path) -> tuple[dict[str, object], list[dict[str, object]]]:
    manifest_path = seed_dir / "run_manifest.json"
    context_path = seed_dir / "context_stratified_endpoint.json"
    rows_path = seed_dir / "context_stratified_endpoint.csv"
    if not manifest_path.is_file() or not context_path.is_file() or not rows_path.is_file():
        raise FileNotFoundError(
            f"{seed_dir} must contain run_manifest.json and the read-only "
            "context_stratified_endpoint.{json,csv} outputs"
        )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    report = json.loads(context_path.read_text(encoding="utf-8"))
    if manifest.get("status") != "completed":
        raise ValueError(f"{seed_dir}: run is not completed")
    if manifest.get("protocol") != "COMMITMENT-HANDOFF-3D-PLAIN-MAPPO-G2-DEVELOPMENT-V1":
        raise ValueError(f"{seed_dir}: unexpected training protocol")
    if report.get("env_name") != "commitment_handoff_3d":
        raise ValueError(f"{seed_dir}: endpoint report is not for commitment_handoff_3d")
    if int(report.get("seed")) != int(manifest.get("seed")):
        raise ValueError(f"{seed_dir}: checkpoint and manifest seeds disagree")
    summary = report.get("summary", {})
    if set(summary) != set(CONTEXTS):
        raise ValueError(f"{seed_dir}: endpoint report does not cover exactly {CONTEXTS}")
    with rows_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    return {"seed": manifest["seed"], "summary": summary, "run_dir": str(seed_dir)}, rows


def main() -> None:
    args = parse_args()
    if not args.execute:
        raise SystemExit("pass --execute because this command creates a development audit")
    if args.out_dir.exists():
        raise FileExistsError(f"refusing to overwrite {args.out_dir}")
    if len(args.seed_dir) < 3:
        raise ValueError("G2 requires at least three independent training seeds")

    seeds: list[dict[str, object]] = []
    all_rows: list[dict[str, object]] = []
    for seed_dir in args.seed_dir:
        result, rows = read_seed(seed_dir)
        seeds.append(result)
        all_rows.extend([{**row, "train_seed": result["seed"]} for row in rows])
    if len({int(item["seed"]) for item in seeds}) != len(seeds):
        raise ValueError("duplicate training seed supplied")

    summary: dict[str, dict[str, object]] = {}
    for context in CONTEXTS:
        values = [float(item["summary"][context]["success_rate"]) for item in seeds]
        moderate = [MIN_SUCCESS <= value <= MAX_SUCCESS for value in values]
        summary[context] = {
            "per_seed_success_rate": dict(zip((int(item["seed"]) for item in seeds), values)),
            "mean_success_rate": sum(values) / len(values),
            "moderate_seed_count": sum(moderate),
            "moderate_seed_requirement": MIN_SEEDS_PER_CONTEXT,
            "passes_context_learnability": sum(moderate) >= MIN_SEEDS_PER_CONTEXT,
        }
    passed = all(bool(summary[context]["passes_context_learnability"]) for context in CONTEXTS)
    verdict = "G2_PLAIN_MAPPO_LEARNABLE_NOT_SATURATED_PASS" if passed else "G2_NOT_YET_ESTABLISHED"
    report = {
        "protocol": PROTOCOL,
        "artifact_class": "DEVELOPMENT_ONLY_TASK_LEARNABILITY_GATE",
        "paper_evidence": False,
        "training_seeds": [int(item["seed"]) for item in seeds],
        "contexts": list(CONTEXTS),
        "success_interval": [MIN_SUCCESS, MAX_SUCCESS],
        "requirement": "At least two of at least three independent plain-MAPPO seeds must be in the success interval for each context.",
        "summary": summary,
        "verdict": verdict,
        "interpretation": (
            "A pass establishes only that the task is suitable for a controlled method pilot. "
            "It does not establish a candidate mechanism, a causal explanation, or paper evidence."
        ),
    }
    args.out_dir.mkdir(parents=True)
    with (args.out_dir / "g2_context_rows.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = list(all_rows[0]) if all_rows else ["train_seed"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(all_rows)
    (args.out_dir / "g2_learnability_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
