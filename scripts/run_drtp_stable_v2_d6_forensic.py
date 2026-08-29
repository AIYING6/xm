"""Read-only D6 forensic for the completed Stable-v2 D5 pilot.

The tool deliberately has no environment, checkpoint, or training imports.
It analyzes only existing CSV artifacts and refuses to overwrite its report.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from statistics import mean


ARMS = ("utr_sg", "drtp_sg", "drtp_klb_sg")
SEEDS = (3201, 3202, 3203)
FAILURE_CONDITIONS = ("F0_44_80", "T28_28_80", "D120_44_120", "C28_120")
Q_FIELDS = ("q_F0", "q_TE", "q_TL", "q_DS", "q_DL", "q_CP")
UNIFORM = 1.0 / len(Q_FIELDS)
EXPECTED_UPDATES = 1953


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def q_l1(left: dict[str, str], right: dict[str, str]) -> float:
    return sum(abs(float(left[key]) - float(right[key])) for key in Q_FIELDS)


def q_uniform_l1(row: dict[str, str]) -> float:
    return sum(abs(float(row[key]) - UNIFORM) for key in Q_FIELDS)


def adapted_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [row for row in rows if row.get("adapted") == "True"]


def first_q_divergence(
    original: list[dict[str, str]], candidate: list[dict[str, str]]
) -> dict[str, float | int] | None:
    by_count = {int(row["adaptation_count"]): row for row in adapted_rows(original)}
    for candidate_row in adapted_rows(candidate):
        count = int(candidate_row["adaptation_count"])
        original_row = by_count.get(count)
        if original_row is None:
            continue
        distance = q_l1(original_row, candidate_row)
        if distance > 1e-12:
            return {
                "adaptation_count": count,
                "original_update": int(original_row["update"]),
                "candidate_update": int(candidate_row["update"]),
                "q_l1": distance,
            }
    return None


def guard_events(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [row for row in rows if int(float(row["policy_guard_triggered"])) == 1]


def robust_mean(summary: list[dict[str, str]], arm: str, seed: int) -> float:
    values = [
        float(row["J"])
        for row in summary
        if row["method"] == arm
        and int(row["train_seed"]) == seed
        and row["condition"] in FAILURE_CONDITIONS
    ]
    if len(values) != len(FAILURE_CONDITIONS):
        raise RuntimeError(f"incomplete endpoint summary for {arm}/seed{seed}")
    return mean(values)


def analyze_seed(d5_root: Path, summary: list[dict[str, str]], seed: int) -> tuple[dict, list[dict]]:
    original_train = read_csv(d5_root / "runs" / "drtp_sg" / f"seed{seed}" / "train_log.csv")
    candidate_train = read_csv(d5_root / "runs" / "drtp_klb_sg" / f"seed{seed}" / "train_log.csv")
    original_sampler = read_csv(d5_root / "runs" / "drtp_sg" / f"seed{seed}" / "drtp_topology_sampler_log.csv")
    candidate_sampler = read_csv(d5_root / "runs" / "drtp_klb_sg" / f"seed{seed}" / "drtp_topology_sampler_log.csv")
    if len(original_train) != EXPECTED_UPDATES or len(candidate_train) != EXPECTED_UPDATES:
        raise RuntimeError(f"incomplete D5 training telemetry for seed{seed}")
    events = guard_events(candidate_train)
    if not events:
        raise RuntimeError(f"D5 KLB is inactive for seed{seed}")
    divergence = first_q_divergence(original_sampler, candidate_sampler)
    original_adapted = adapted_rows(original_sampler)
    candidate_adapted = adapted_rows(candidate_sampler)
    if not original_adapted or not candidate_adapted or divergence is None:
        raise RuntimeError(f"missing paired sampler divergence for seed{seed}")
    original_gain = robust_mean(summary, "drtp_sg", seed) - robust_mean(summary, "utr_sg", seed)
    candidate_gain = robust_mean(summary, "drtp_klb_sg", seed) - robust_mean(summary, "utr_sg", seed)
    first_event = events[0]
    row = {
        "seed": seed,
        "first_guard_update": int(first_event["update"]),
        "first_guard_kl_attempted": float(first_event["policy_kl_attempted_max"]),
        "first_guard_alpha": float(first_event["policy_backtrack_alpha"]),
        "guard_event_count": len(events),
        "first_q_divergence_update": int(divergence["candidate_update"]),
        "first_q_divergence_l1": float(divergence["q_l1"]),
        "max_paired_q_l1": max(
            q_l1(
                {key: original[key] for key in Q_FIELDS},
                {key: candidate[key] for key in Q_FIELDS},
            )
            for original, candidate in zip(original_adapted, candidate_adapted)
        ),
        "final_paired_q_l1": q_l1(original_adapted[-1], candidate_adapted[-1]),
        "original_mean_q_uniform_l1": mean(q_uniform_l1(row) for row in original_adapted),
        "klb_mean_q_uniform_l1": mean(q_uniform_l1(row) for row in candidate_adapted),
        "G_original": original_gain,
        "G_klb": candidate_gain,
        "klb_minus_original": candidate_gain - original_gain,
    }
    row["temporal_ordering"] = row["first_q_divergence_update"] > row["first_guard_update"]
    row["amplification"] = row["klb_mean_q_uniform_l1"] > row["original_mean_q_uniform_l1"]
    row["nonimprovement"] = row["G_klb"] <= row["G_original"]
    event_rows = [
        {
            "seed": seed,
            "update": int(event["update"]),
            "policy_guard_epoch": int(float(event["policy_guard_epoch"])),
            "attempted_kl": float(event["policy_kl_attempted_max"]),
            "accepted_kl": float(event["policy_kl_post_step"]),
            "alpha": float(event["policy_backtrack_alpha"]),
            "backtrack_iterations": int(float(event["policy_backtrack_iterations"])),
        }
        for event in events
    ]
    return row, event_rows


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--d5-root", type=Path, required=True, help="Extracted D5 result root")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("--execute required; D6 is read-only")
    if args.output_dir.exists():
        raise FileExistsError(f"refusing overwrite/rerun: {args.output_dir}")
    summary_path = args.d5_root / "evaluations" / "final_05m" / "per_seed_condition_summary.csv"
    if not summary_path.exists():
        raise RuntimeError("missing D5 final evaluation summary")
    summary = read_csv(summary_path)
    expected = {(arm, seed) for arm in ARMS for seed in SEEDS}
    found = {(row["method"], int(row["train_seed"])) for row in summary}
    if not expected.issubset(found):
        raise RuntimeError("incomplete D5 arm/seed evaluation summary")
    args.output_dir.mkdir(parents=True, exist_ok=False)
    seed_rows, events = [], []
    for seed in SEEDS:
        row, seed_events = analyze_seed(args.d5_root, summary, seed)
        seed_rows.append(row)
        events.extend(seed_events)
    criteria = {
        "temporal_ordering_all_seeds": all(row["temporal_ordering"] for row in seed_rows),
        "sampler_amplification_all_seeds": all(row["amplification"] for row in seed_rows),
        "candidate_nonimprovement_all_seeds": all(row["nonimprovement"] for row in seed_rows),
        "input_integrity": True,
    }
    authorized = all(criteria.values())
    decision = (
        "D6_PAIRED_PROBE_DESIGN_AUDIT_AUTHORIZED"
        if authorized
        else "D6_NO_GO_NO_NEW_CANDIDATE_AUTHORIZED"
    )
    write_csv(args.output_dir / "seed_level_feedback_timeline.csv", seed_rows)
    write_csv(args.output_dir / "klb_intervention_events.csv", events)
    inputs = {"evaluation_summary": sha256(summary_path)}
    for arm in ("drtp_sg", "drtp_klb_sg"):
        for seed in SEEDS:
            for name in ("train_log.csv", "drtp_topology_sampler_log.csv"):
                path = args.d5_root / "runs" / arm / f"seed{seed}" / name
                inputs[str(path.relative_to(args.d5_root))] = sha256(path)
    decision_data = {
        "protocol": "DRTP-STABLE-V2-D6-FEEDBACK-FORENSIC-V1",
        "decision": decision,
        "criteria": criteria,
        "source_d5_root": str(args.d5_root),
        "source_hashes": inputs,
        "seed_results": seed_rows,
        "causal_claim_authorized": False,
        "implementation_authorized": False,
        "training_authorized": False,
        "mainline_a_modified": False,
        "allowed_next_action": (
            "paired-probe design audit only" if authorized else "stop; no new candidate"
        ),
    }
    (args.output_dir / "D6_FEEDBACK_FORENSIC_DECISION.json").write_text(
        json.dumps(decision_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    rows = "\n".join(
        "| {seed} | {first_guard_update} | {first_q_divergence_update} | {original_mean_q_uniform_l1:.3f} | {klb_mean_q_uniform_l1:.3f} | {G_original:.3f} | {G_klb:.3f} |".format(**row)
        for row in seed_rows
    )
    report = f"""# Stable-v2 D6 sampler-feedback forensic

**Decision:** `{decision}`.

| Seed | First KLB trigger | First paired q divergence | Original mean $\\|q-q_u\\|_1$ | KLB mean $\\|q-q_u\\|_1$ | G Original | G KLB |
|---:|---:|---:|---:|---:|---:|---:|
{rows}

## Frozen criteria

```json
{json.dumps(criteria, indent=2)}
```

The observed ordering supports only the limited statement that KLB intervention
precedes later paired sampler divergence in these D5 trajectories. It does not
identify the cause of Original DRTP seed sensitivity and does not authorize a
new implementation or training run.
"""
    (args.output_dir / "D6_FEEDBACK_FORENSIC_REPORT.md").write_text(report, encoding="utf-8")
    print(json.dumps({"decision": decision, "output": str(args.output_dir)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
