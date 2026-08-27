"""Create a small, auditable publication bundle for the independent SNR cohort.

This is deliberately a *data integration* utility.  It never trains or
evaluates a policy, and it copies only the source tables needed to disclose the
completed three-arm 10M cohort in the manuscript and supplementary material.
The formal UTR--DRTP cohort remains a separate estimand.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import shutil
import tarfile
from collections import defaultdict
from pathlib import Path
from statistics import mean, median


ARCHIVE_SHA256 = "86a708244fa4d30935159a08d234c48feeb7a4c455208d58fbc58d308b4f4ae1"
ROOT = "results/formal/drtp_snr_q2_mechanism_comparator_10way"
EVAL_ROOT = f"{ROOT}/evaluations/final_10m"
MEMBERS = {
    "raw_episode_metrics.csv": f"{EVAL_ROOT}/raw_episode_metrics.csv",
    "per_seed_condition_summary.csv": f"{EVAL_ROOT}/per_seed_condition_summary.csv",
    "evaluation_manifest.json": f"{EVAL_ROOT}/evaluation_manifest.json",
    "comparator_report.md": f"{ROOT}/DRTP_SNR_Q2_MECHANISM_COMPARATOR_REPORT.md",
}
NOMINAL = "nominal"
F0 = "f0_seen_44_80"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_member(archive: tarfile.TarFile, name: str) -> bytes:
    member = archive.getmember(name)
    handle = archive.extractfile(member)
    if handle is None:
        raise RuntimeError(f"archive member is unreadable: {name}")
    return handle.read()


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def number(row: dict[str, str], key: str) -> float:
    return float(row[key])


def endpoint_rows(condition_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    by_cell: dict[tuple[str, int], list[dict[str, str]]] = defaultdict(list)
    for row in condition_rows:
        by_cell[(row["arm"], int(row["seed"]))].append(row)

    result: list[dict[str, object]] = []
    for (arm, seed), rows in sorted(by_cell.items()):
        by_condition = {row["condition"]: row for row in rows}
        if len(by_condition) != 12 or NOMINAL not in by_condition or F0 not in by_condition:
            raise ValueError(f"incomplete 12-condition cell: {arm}/seed{seed}")
        perturbation = [
            row for condition, row in by_condition.items() if condition not in {NOMINAL, F0}
        ]
        failures = [row for condition, row in by_condition.items() if condition != NOMINAL]
        trigger_values = [number(row, "failure_trigger_success_rate_risk_set") for row in failures]
        result.append(
            {
                "arm": arm,
                "seed": seed,
                "J_nominal": number(by_condition[NOMINAL], "J"),
                "J_F0": number(by_condition[F0], "J"),
                "J_pert_mean": mean(number(row, "J") for row in perturbation),
                "J_pert_worst": min(number(row, "J") for row in perturbation),
                "collision_fault_mean": mean(number(row, "collision") for row in failures),
                "timeout_fault_mean": mean(number(row, "timeout") for row in failures),
                "constraint_fault_mean": mean(number(row, "constraint_violation") for row in failures),
                "pretrigger_collision_count": sum(int(row["pretrigger_collision_count"]) for row in failures),
                "risk_set_size": sum(int(row["risk_set_size"]) for row in failures),
                "trigger_validity_risk_set": min(trigger_values),
            }
        )
    return result


def paired_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    by_key = {(str(row["arm"]), int(row["seed"])): row for row in rows}
    output: list[dict[str, object]] = []
    for seed in range(2401, 2406):
        utr = by_key[("utr_sg", seed)]
        drtp = by_key[("drtp_sg", seed)]
        output.append(
            {
                "seed": seed,
                **{
                    f"delta_{metric}": float(drtp[metric]) - float(utr[metric])
                    for metric in ("J_nominal", "J_F0", "J_pert_mean", "J_pert_worst")
                },
                "delta_collision_fault_mean": float(drtp["collision_fault_mean"]) - float(utr["collision_fault_mean"]),
                "delta_timeout_fault_mean": float(drtp["timeout_fault_mean"]) - float(utr["timeout_fault_mean"]),
            }
        )
    return output


def pooled_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    fields = [
        "J_nominal", "J_F0", "J_pert_mean", "J_pert_worst", "collision_fault_mean",
        "timeout_fault_mean", "constraint_fault_mean", "pretrigger_collision_count",
        "risk_set_size", "trigger_validity_risk_set",
    ]
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["arm"])].append(row)
    output = []
    for arm, arm_rows in sorted(grouped.items()):
        output.append({"arm": arm, "n_training_seeds": len(arm_rows), **{
            metric: mean(float(row[metric]) for row in arm_rows) for metric in fields
        }})
    return output


def paired_summary(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    fields = [key for key in rows[0] if key.startswith("delta_")]
    return [
        {
            "comparison": "drtp_sg_minus_utr_sg",
            "endpoint": field[len("delta_"):],
            "mean": mean(float(row[field]) for row in rows),
            "median": median(float(row[field]) for row in rows),
            "wins_over_zero": sum(float(row[field]) > 0 for row in rows),
            "total_seeds": len(rows),
            "worst": min(float(row[field]) for row in rows),
        }
        for field in fields
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--archive", type=Path,
        default=Path(r"D:/File/Downloads/drtp_snr_q2_mechanism_comparator_10way_results.tar.gz"),
    )
    parser.add_argument(
        "--output-dir", type=Path,
        default=Path("paper/q2_final_zh/supplementary/source_data/snr_independent_replication"),
    )
    args = parser.parse_args()

    if not args.archive.is_file():
        raise FileNotFoundError(args.archive)
    observed_hash = sha256(args.archive)
    if observed_hash != ARCHIVE_SHA256:
        raise ValueError(f"archive SHA256 mismatch: {observed_hash}")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    with tarfile.open(args.archive, "r:gz") as archive:
        material = {alias: read_member(archive, member) for alias, member in MEMBERS.items()}

    for alias, data in material.items():
        (args.output_dir / alias).write_bytes(data)

    condition_rows = list(csv.DictReader(io.StringIO(material["per_seed_condition_summary.csv"].decode("utf-8"))))
    raw_rows = list(csv.DictReader(io.StringIO(material["raw_episode_metrics.csv"].decode("utf-8"))))
    if len(raw_rows) != 18000 or len(condition_rows) != 180:
        raise ValueError(f"unexpected record counts: raw={len(raw_rows)}, condition={len(condition_rows)}")
    if set(row["arm"] for row in condition_rows) != {"utr_sg", "snr_sg", "drtp_sg"}:
        raise ValueError("three-arm independent cohort is incomplete")
    if set(int(row["seed"]) for row in condition_rows) != set(range(2401, 2406)):
        raise ValueError("independent cohort seeds are incomplete")

    endpoints = endpoint_rows(condition_rows)
    paired = paired_rows(endpoints)
    write_csv(args.output_dir / "per_seed_endpoint_summary.csv", endpoints, list(endpoints[0]))
    write_csv(args.output_dir / "drtp_minus_utr_paired_seed_effects.csv", paired, list(paired[0]))
    pooled = pooled_rows(endpoints)
    write_csv(args.output_dir / "pooled_endpoint_summary.csv", pooled, list(pooled[0]))
    paired_aggregate = paired_summary(paired)
    write_csv(args.output_dir / "drtp_minus_utr_paired_summary.csv", paired_aggregate, list(paired_aggregate[0]))

    provenance = {
        "schema": "drtp-snr-independent-replication-publication-bundle-v1",
        "integration_mode": "zero_training_archive_verification_and_disclosure",
        "source_archive": str(args.archive),
        "source_archive_sha256": observed_hash,
        "source_protocol": "DRTP-SNR-Q2-MECHANISM-COMPARATOR-EVALUATION-V1",
        "training_contract": "DRTP-SNR-Q2-MECHANISM-COMPARATOR-TRAINING-V1",
        "independent_training_seeds": list(range(2401, 2406)),
        "methods": ["utr_sg", "snr_sg", "drtp_sg"],
        "training_budget_env_steps": 10000128,
        "common_final_checkpoint": "10m",
        "evaluation_tape_hash": json.loads(material["evaluation_manifest.json"])["tape_hash"],
        "raw_episode_records": len(raw_rows),
        "condition_summary_rows": len(condition_rows),
        "publication_boundary": (
            "A complete independent three-arm replication stratum. It is never pooled with "
            "the formal 2301-2305 UTR--DRTP cohort and must be disclosed with all methods, "
            "all seeds, endpoints, and safety outcomes."
        ),
    }
    (args.output_dir / "archive_provenance.json").write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(provenance, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
