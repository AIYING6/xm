"""Apply only the frozen S1 0.5M gate; this program never starts follow-on work."""
from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARMS, SEEDS = ("utr_sg", "drtp_sg", "drtp_tr_sg"), (2901, 2902, 2903)
CONDITIONS = ("nominal", "F0_44_80", "T28_28_80", "D120_44_120", "C28_120")
FAILURES = CONDITIONS[1:]
EXPECTED_ROWS = len(ARMS) * len(SEEDS) * len(CONDITIONS) * 100


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def avg(values: list[float]) -> float:
    return sum(values) / len(values)


def dispersion(values: list[float]) -> dict[str, float]:
    median = statistics.median(values)
    return {"range": max(values) - min(values), "sample_sd": statistics.stdev(values),
            "mad": statistics.median([abs(value - median) for value in values])}


def catastrophic(candidate: dict[str, float], reference: dict[str, float]) -> bool:
    f0_ratio = candidate["J_F0"] / reference["J_F0"]
    worst_ratio = candidate["J_pert_worst"] / reference["J_pert_worst"]
    collapse = (f0_ratio < .70 and worst_ratio < .85) or (worst_ratio < .70 and f0_ratio < .85)
    safety_collapse = candidate["timeout"] - reference["timeout"] > .20 and (f0_ratio < .85 or worst_ratio < .85)
    return collapse or safety_collapse


def cell(summary: list[dict[str, str]], arm: str, seed: int) -> dict[str, float]:
    by_condition = {row["condition"]: row for row in summary if row["method"] == arm and int(row["train_seed"]) == seed}
    if set(by_condition) != set(CONDITIONS):
        raise RuntimeError(f"missing summary cell: {arm}/seed{seed}")
    metric = lambda condition, key: float(by_condition[condition][key])
    return {
        "J_nominal": metric("nominal", "J"), "J_F0": metric("F0_44_80", "J"),
        "J_pert_mean": avg([metric(condition, "J") for condition in FAILURES]),
        "J_pert_worst": min(metric(condition, "J") for condition in FAILURES),
        "collision": avg([metric(condition, "collision") for condition in FAILURES]),
        "timeout": avg([metric(condition, "timeout") for condition in FAILURES]),
        "constraint_violation": max(metric(condition, "constraint_violation") for condition in FAILURES),
    }


def md_table(rows: list[dict]) -> str:
    header = "| Seed | G original DRTP | G DRTP-TR | TR−DRTP J pert | Δ collision vs UTR | Δ timeout vs UTR | Original catastrophic | TR catastrophic |\n|---:|---:|---:|---:|---:|---:|---|---|"
    body = "\n".join(
        f"| {row['seed']} | {row['G_drtp']:.3f} | {row['G_tr']:.3f} | {row['tr_minus_drtp']:.3f} | {row['tr_collision_minus_utr']:.3f} | {row['tr_timeout_minus_utr']:.3f} | {row['drtp_catastrophic']} | {row['tr_catastrophic']} |"
        for row in rows)
    return header + "\n" + body


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("--execute required")
    freeze = json.loads((ROOT / "configs/drtp_stabilization_s0_freeze.json").read_text(encoding="utf-8"))
    tape = json.loads((ROOT / "configs/drtp_stabilization_s1_development_tape.json").read_text(encoding="utf-8"))
    evaluation = args.output_root / "evaluations" / "final_05m"
    manifest = json.loads((evaluation / "evaluation_manifest.json").read_text(encoding="utf-8"))
    raw, summary = read_csv(evaluation / "raw_episode_metrics.csv"), read_csv(evaluation / "per_seed_condition_summary.csv")
    expected_summary = {(arm, seed, condition) for arm in ARMS for seed in SEEDS for condition in CONDITIONS}
    found_summary = {(row["method"], int(row["train_seed"]), row["condition"]) for row in summary}
    source_valid = len(manifest.get("source_runs", [])) == 9 and all(
        source.get("status") == "completed" and source.get("updates") == 1953
        and source.get("environment_steps") == 499968 and source.get("parameter_count") == 116728
        and source.get("early_stopping") is False and source.get("checkpoint_promotion") is False
        and source.get("seed_replacement") is False and source.get("tape_hash") == tape["tape_hash"]
        for source in manifest.get("source_runs", []))
    integrity = (manifest.get("status") == "completed" and manifest.get("raw_rows") == EXPECTED_ROWS
                 and len(raw) == EXPECTED_ROWS and found_summary == expected_summary)
    if not integrity or not source_valid:
        raise RuntimeError("TECHNICAL_INVALID: incomplete S1 data or contract violation")
    metrics = {arm: {seed: cell(summary, arm, seed) for seed in SEEDS} for arm in ARMS}
    evidence = []
    for seed in SEEDS:
        utr, drtp, tr = metrics["utr_sg"][seed], metrics["drtp_sg"][seed], metrics["drtp_tr_sg"][seed]
        evidence.append({"seed": seed, "G_drtp": drtp["J_pert_mean"] - utr["J_pert_mean"],
                         "G_tr": tr["J_pert_mean"] - utr["J_pert_mean"],
                         "tr_minus_drtp": tr["J_pert_mean"] - drtp["J_pert_mean"],
                         "tr_collision_minus_utr": tr["collision"] - utr["collision"],
                         "tr_timeout_minus_utr": tr["timeout"] - utr["timeout"],
                         "drtp_catastrophic": catastrophic(drtp, utr), "tr_catastrophic": catastrophic(tr, utr)})
    epsilon, margin = float(freeze["epsilon_J"]), float(freeze["practical_downside_improvement_margin"])
    gains_drtp, gains_tr = [row["G_drtp"] for row in evidence], [row["G_tr"] for row in evidence]
    dispersion_drtp, dispersion_tr = dispersion(gains_drtp), dispersion(gains_tr)
    advantage = avg([metrics["drtp_tr_sg"][seed]["J_pert_mean"] for seed in SEEDS]) >= avg([metrics["drtp_sg"][seed]["J_pert_mean"] for seed in SEEDS]) - epsilon
    downside = min(gains_tr) - min(gains_drtp) > margin and sum(row["tr_catastrophic"] for row in evidence) <= sum(row["drtp_catastrophic"] for row in evidence)
    reliable = all(dispersion_tr[key] < dispersion_drtp[key] for key in dispersion_drtp)
    safety_rows = []
    for seed in SEEDS:
        for condition in FAILURES:
            candidate = next(row for row in summary if row["method"] == "drtp_tr_sg" and int(row["train_seed"]) == seed and row["condition"] == condition)
            reference = next(row for row in summary if row["method"] == "utr_sg" and int(row["train_seed"]) == seed and row["condition"] == condition)
            safety_rows.append({"seed": seed, "condition": condition,
                                "collision_difference": float(candidate["collision"]) - float(reference["collision"]),
                                "timeout_difference": float(candidate["timeout"]) - float(reference["timeout"]),
                                "constraint_violation": float(candidate["constraint_violation"])})
    safety = (avg([row["tr_collision_minus_utr"] for row in evidence]) <= .05
              and avg([row["tr_timeout_minus_utr"] for row in evidence]) <= .05
              and all(row["collision_difference"] <= .10 and row["timeout_difference"] <= .10 and row["constraint_violation"] == 0 for row in safety_rows))
    upper_seeds = [row for row in evidence if row["G_drtp"] > epsilon]
    upper_tail = bool(upper_seeds) and all(row["tr_minus_drtp"] >= -epsilon for row in upper_seeds)
    criteria = {"advantage_retention": advantage, "downside_protection": downside, "seed_reliability": reliable,
                "safety": safety, "upper_tail_retention": upper_tail, "upper_tail_assessable": bool(upper_seeds)}
    no_go_reasons = []
    if not advantage: no_go_reasons.append("advantage_retention_failed")
    if min(gains_tr) < min(gains_drtp): no_go_reasons.append("TR_worst_paired_gain_worse_than_original")
    if sum(row["tr_catastrophic"] for row in evidence) > sum(row["drtp_catastrophic"] for row in evidence): no_go_reasons.append("catastrophic_seed_count_increased")
    if not safety: no_go_reasons.append("safety_failed")
    if upper_seeds and not upper_tail: no_go_reasons.append("upper_tail_retention_failed")
    if all(criteria[key] for key in ("advantage_retention", "downside_protection", "seed_reliability", "safety", "upper_tail_retention")):
        decision = "S1_EARLY_GO"
    elif no_go_reasons:
        decision = "S1_NO_GO"
    else:
        decision = "S1_INCONCLUSIVE"
    report_dir = args.output_root / "diagnostics" / "s1_05m_gate"
    report_dir.mkdir(parents=True, exist_ok=False)
    with (report_dir / "s1_seed_level_evidence.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = list(evidence[0])
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader(); writer.writerows(evidence)
    with (report_dir / "s1_safety_evidence.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(safety_rows[0])); writer.writeheader(); writer.writerows(safety_rows)
    result = {"protocol": "DRTP-STABILIZATION-S1-05M-GATE-V1", "decision": decision,
              "tape_hash": tape["tape_hash"], "primary_inference_unit": "training_seed", "n_training_seeds": 3,
              "epsilon_J": epsilon, "practical_downside_margin": margin, "criteria": criteria,
              "no_go_reasons": no_go_reasons, "original_drtp_gain_dispersion": dispersion_drtp,
              "drtp_tr_gain_dispersion": dispersion_tr, "upper_tail_reference_seeds": [row["seed"] for row in upper_seeds],
              "seed_level_evidence": evidence, "safety_seed_condition_evidence": safety_rows,
              "automatic_s2_started": False, "automatic_continuation_started": False}
    (report_dir / "S1_05M_GATE_DECISION.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    text = f"""# S1 0.5M frozen gate report

**Decision:** `{decision}`. No continuation, S2 run, seed replacement, rerun, or parameter change was started.

## Integrity

- Nine final checkpoints: `9/9`; raw fixed-tape records: `{len(raw)}/{EXPECTED_ROWS}`.
- Tape SHA256: `{tape['tape_hash']}`; S0 delta: `{freeze['delta_q_l1']}`; epsilon_J and downside margin: `{epsilon}`.
- Primary inference unit: training seed (`n=3`). The evaluation tape is development-only.

## Seed-level paired evidence

{md_table(evidence)}

## Frozen criteria

| Criterion | Result |
|---|---|
| Advantage retention | `{advantage}` |
| Downside protection | `{downside}` |
| Seed reliability (range, SD, MAD all lower) | `{reliable}` |
| Safety | `{safety}` |
| Upper-tail retention | `{upper_tail}` |

Original-DRTP gain dispersion: `{json.dumps(dispersion_drtp)}`. DRTP-TR gain dispersion: `{json.dumps(dispersion_tr)}`.

NO-GO reasons: `{', '.join(no_go_reasons) if no_go_reasons else 'none'}`. Upper-tail reference seeds: `{[row['seed'] for row in upper_seeds]}`.
"""
    (report_dir / "S1_05M_GATE_REPORT.md").write_text(text, encoding="utf-8")
    print(json.dumps({"decision": decision, "report": str(report_dir / "S1_05M_GATE_REPORT.md")}, indent=2))


if __name__ == "__main__":
    main()
