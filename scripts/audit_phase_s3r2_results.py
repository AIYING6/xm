"""Audit S3-R2 results and apply its preregistered screening rule."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np


METHOD = "simple_full_no_role_gate"
SEEDS = (1501, 1502, 1503)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("results/development/phase_s3r2_simple_full/runs/simple_full_no_role_gate"))
    parser.add_argument("--baseline", type=Path, default=Path("results/development/phase_s3r_evaluation_remediation/per_seed_summary.csv"))
    parser.add_argument("--output", type=Path, default=Path("results/development/phase_s3r2_audit_summary.csv"))
    args = parser.parse_args()

    summary = []
    checkpoint_hashes_match = True
    all_complete = True
    all_shared_tape = True
    all_exposed = True
    finite_diagnostics = True
    for seed in SEEDS:
        run = args.root / f"seed{seed}"
        manifest = json.loads((run / "run_manifest.json").read_text(encoding="utf-8"))
        checkpoint = run / "actor_critic_latest.pt"
        hash_match = sha256(checkpoint) == manifest.get("checkpoint_sha256")
        paired = rows(run / "paired_metrics.csv")
        log = rows(run / "train_log.csv")
        checkpoint_hashes_match &= hash_match
        all_complete &= manifest.get("status") == "completed" and len(log) == 782 and len(paired) == 100
        ids = {int(row["development_episode_id"]) for row in paired}
        all_shared_tape &= ids == set(range(340000, 340100))
        all_exposed &= all(float(row["failure_exposed"]) == 1.0 for row in paired)
        finite_diagnostics &= all(np.isfinite(float(log[-1][key])) for key in ("loss", "approx_kl", "grad_norm", "explained_variance"))
        summary.append({
            "method": METHOD, "seed": seed, "status": manifest.get("status"),
            "updates": len(log), "episodes": len(paired), "checkpoint_sha256": manifest.get("checkpoint_sha256"),
            "checkpoint_hash_matches_manifest": hash_match,
            "J_nominal_mean": float(np.mean([float(row["J_nominal"]) for row in paired])),
            "J_failure_mean": float(np.mean([float(row["J_failure"]) for row in paired])),
            "delta_J_mean": float(np.mean([float(row["delta_J"]) for row in paired])),
            "success_nominal_mean": float(np.mean([float(row["success_nominal"]) for row in paired])),
            "success_failure_mean": float(np.mean([float(row["success_failure"]) for row in paired])),
            "failure_exposure": float(np.mean([float(row["failure_exposed"]) for row in paired])),
        })

    baseline = {int(row["train_seed"]): row for row in rows(args.baseline) if row["method"] == "matched_single_graph"}
    simple_nominal = float(np.mean([row["J_nominal_mean"] for row in summary]))
    sg_nominal = float(np.mean([float(baseline[seed]["J_nominal_mean"]) for seed in SEEDS]))
    simple_delta = float(np.mean([row["delta_J_mean"] for row in summary]))
    sg_delta = float(np.mean([float(baseline[seed]["delta_J_mean"]) for seed in SEEDS]))
    nominal_ratio = simple_nominal / abs(sg_nominal) if sg_nominal else float("nan")
    delta_better_seeds = sum(row["delta_J_mean"] < float(baseline[seed]["delta_J_mean"]) for row, seed in zip(summary, SEEDS))
    negative_nominal_in_positive_sg_seed = any(row["J_nominal_mean"] < 0.0 and float(baseline[seed]["J_nominal_mean"]) > 0.0 for row, seed in zip(summary, SEEDS))
    gates = {
        "all_runs_complete_finite": all_complete and finite_diagnostics,
        "shared_tape_and_exposure_provenance": all_shared_tape and all_exposed,
        "nominal_within_10_percent_of_matched_sg": nominal_ratio >= 0.90,
        "delta_better_in_at_least_two_seeds_and_mean": delta_better_seeds >= 2 and simple_delta < sg_delta,
        "no_low_competence_pseudo_robustness_seed": not negative_nominal_in_positive_sg_seed,
    }
    result = {
        "protocol": "PHASE-S3-R2-V1", "method": METHOD, "training_started": True,
        "new_training_authorized_after_result": False, "independent_unit": "training_seed",
        "checkpoint_hashes_match": checkpoint_hashes_match, "summary": summary,
        "comparison": {"simple_full_nominal_mean": simple_nominal, "matched_sg_nominal_mean": sg_nominal,
                       "simple_full_delta_mean": simple_delta, "matched_sg_delta_mean": sg_delta,
                       "simple_full_nominal_ratio_to_sg": nominal_ratio, "delta_better_seed_count": delta_better_seeds},
        "gates": gates, "decision": "NO-GO" if all(gates.values()) is False or not all(gates.values()) else "PASS",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary[0]))
        writer.writeheader(); writer.writerows(summary)
    (args.output.with_suffix(".json")).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
