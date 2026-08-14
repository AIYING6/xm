"""Aggregate TP-1 Round-A and decide whether B or C is triggered."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np

ARMS = ("sg", "ctp_a")
SEEDS = (1601, 1602)


def rows(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def avg(data: list[dict], key: str) -> float:
    return float(np.mean([float(row[key]) for row in data]))


def write_csv(path: Path, data: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(data[0]))
        writer.writeheader()
        writer.writerows(data)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=Path("results/phase_tp1_round_a"))
    args = parser.parse_args()
    summary = []
    for arm in ARMS:
        for seed in SEEDS:
            run = args.output_root / "runs" / arm / f"seed{seed}"
            manifest = json.loads((run / "run_manifest.json").read_text(encoding="utf-8"))
            if manifest.get("status") != "completed":
                raise RuntimeError(f"incomplete run {arm}/{seed}")
            train_log = rows(run / "train_log.csv")
            raw = rows(run / "raw_episode_metrics.csv")
            paired = rows(run / "paired_metrics.csv")
            if len(train_log) != 1172 or len(raw) != 100 or len(paired) != 50:
                raise RuntimeError(f"artifact row count mismatch {arm}/{seed}")
            summary.append({
                "arm": arm, "seed": seed,
                "J_nominal": avg(paired, "J_nominal"), "J_failure": avg(paired, "J_failure"),
                "Delta_J": avg(paired, "delta_J"),
                "collision_nominal": avg(paired, "collision_nominal"), "collision_failure": avg(paired, "collision_failure"),
                "timeout_nominal": avg(paired, "timeout_nominal"), "timeout_failure": avg(paired, "timeout_failure"),
                "constraint_nominal": avg(paired, "constraint_nominal"), "constraint_failure": avg(paired, "constraint_failure"),
                "failure_exposure": avg(paired, "failure_exposed"),
            })
    write_csv(args.output_root / "round_a_per_seed_summary.csv", summary)
    sg = [row for row in summary if row["arm"] == "sg"]
    ctp = [row for row in summary if row["arm"] == "ctp_a"]
    sg_nominal, ctp_nominal = avg(sg, "J_nominal"), avg(ctp, "J_nominal")
    sg_failure, ctp_failure = avg(sg, "J_failure"), avg(ctp, "J_failure")
    sg_delta, ctp_delta = avg(sg, "Delta_J"), avg(ctp, "Delta_J")
    nominal_sufficient = ctp_nominal >= 0.95 * sg_nominal
    failure_robustness_sufficient = ctp_failure > sg_failure and ctp_delta < sg_delta
    safety = {}
    for metric in ("collision_failure", "timeout_failure", "constraint_failure"):
        safety[metric] = {
            "sg": avg(sg, metric), "ctp_a": avg(ctp, metric),
            "difference_ctp_minus_sg": avg(ctp, metric) - avg(sg, metric),
        }
    if not nominal_sufficient:
        trigger = "SCHEDULE_B"
        reason = "mean J_nominal_CTP < 0.95 × mean J_nominal_SG"
    elif not failure_robustness_sufficient:
        trigger = "SCHEDULE_C"
        reason = "nominal competence sufficient, but failure score or Delta_J criterion insufficient"
    else:
        trigger = "NONE_FREEZE_A"
        reason = "Schedule A meets Round-A tuning target; freeze A immediately"
    decision = {
        "protocol": "PHASE-TP-1-ROUND-A-V1", "round_a_complete": True,
        "mean": {"sg": {"J_nominal": sg_nominal, "J_failure": sg_failure, "Delta_J": sg_delta},
                 "ctp_a": {"J_nominal": ctp_nominal, "J_failure": ctp_failure, "Delta_J": ctp_delta}},
        "nominal_sufficient": nominal_sufficient,
        "failure_robustness_sufficient": failure_robustness_sufficient,
        "safety": safety, "trigger": trigger, "reason": reason,
        "schedule_b_started": False, "schedule_c_started": False,
        "canonical_seeds_used": False, "resume_used": False,
    }
    (args.output_root / "ROUND_A_DECISION.json").write_text(json.dumps(decision, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(decision, indent=2))


if __name__ == "__main__":
    main()
