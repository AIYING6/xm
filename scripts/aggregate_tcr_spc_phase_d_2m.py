"""Apply the pre-registered Phase-D 2M interim stop-loss gate."""
from __future__ import annotations

import argparse
import json
import math
import statistics
from pathlib import Path

from scripts.aggregate_tcr_spc_phase_d import catastrophic, cell, mean, pooled, rows
from scripts.run_tcr_spc_phase_c_single import ARMS, SEEDS


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-root", type=Path, required=True)
    parser.add_argument("--report-path", type=Path, required=True)
    args = parser.parse_args()
    root = args.results_root.resolve()
    evaluation = root / "evaluations" / "final_2m"
    manifest = json.loads((evaluation / "evaluation_manifest.json").read_text(encoding="utf-8"))
    tape = json.loads((root / "tape_manifest.json").read_text(encoding="utf-8"))
    if (
        manifest.get("status") != "completed"
        or manifest.get("phase_d") is not True
        or manifest.get("phase_d_stage") != "2m"
        or manifest.get("cells") != 15
    ):
        raise RuntimeError("TECHNICAL INVALID: incomplete Phase-D 2M evaluation")
    raw = rows(evaluation / "raw_episode_metrics.csv")
    if len(raw) != 18_000:
        raise RuntimeError(f"TECHNICAL INVALID: expected 18000 raw rows, got {len(raw)}")

    per_seed = [cell(raw, arm, seed) for arm in ARMS for seed in SEEDS]
    by_key = {(row["arm"], row["seed"]): row for row in per_seed}
    by_arm = {arm: [row for row in per_seed if row["arm"] == arm] for arm in ARMS}
    pooled_metrics = {arm: pooled(by_arm[arm]) for arm in ARMS}
    tcr_catastrophic = [
        catastrophic(by_key["tcr_sg", seed], by_key["utr_sg", seed]) for seed in SEEDS
    ]
    spc_catastrophic = [
        catastrophic(by_key["spc_sg", seed], by_key["utr_sg", seed]) for seed in SEEDS
    ]
    tcr_vs_utr = {
        str(seed): by_key["tcr_sg", seed]["J_OOD_worst"] - by_key["utr_sg", seed]["J_OOD_worst"]
        for seed in SEEDS
    }
    tcr_vs_spc = {
        str(seed): by_key["tcr_sg", seed]["J_OOD_worst"] - by_key["spc_sg", seed]["J_OOD_worst"]
        for seed in SEEDS
    }
    tcr_values = [by_key["tcr_sg", seed]["J_OOD_worst"] for seed in SEEDS]
    utr_values = [by_key["utr_sg", seed]["J_OOD_worst"] for seed in SEEDS]
    tcr_range, utr_range = max(tcr_values) - min(tcr_values), max(utr_values) - min(utr_values)
    tcr_sd, utr_sd = statistics.stdev(tcr_values), statistics.stdev(utr_values)
    bifurcation = (
        tcr_range > 2 * max(utr_range, 1e-12)
        and tcr_sd > 2 * max(utr_sd, 1e-12)
        and any(row["OOD_worst_ratio"] < 0.85 for row in tcr_catastrophic)
    )
    timeout_diffs = [
        by_key["tcr_sg", seed]["timeout"] - by_key["utr_sg", seed]["timeout"] for seed in SEEDS
    ]
    systemic_safety = pooled_metrics["tcr_sg"]["constraint"] > 0 or (
        pooled_metrics["tcr_sg"]["timeout"] - pooled_metrics["utr_sg"]["timeout"] > 0.05
        and sum(value > 0.05 for value in timeout_diffs) >= 3
    )
    technical = all(row["risk_set_size"] > 0 and row["trigger_success"] == 1.0 for row in per_seed)
    tcr_catastrophic_count = sum(row["catastrophic"] for row in tcr_catastrophic)
    stress_seed_2002 = next(row for row in tcr_catastrophic if row["seed"] == 2002)
    tcr_positive = sum(value > 0 for value in tcr_vs_utr.values())
    tcr_systematically_below_utr = (
        pooled_metrics["tcr_sg"]["J_OOD_mean"] < pooled_metrics["utr_sg"]["J_OOD_mean"]
        and pooled_metrics["tcr_sg"]["J_OOD_worst"] < pooled_metrics["utr_sg"]["J_OOD_worst"]
        and tcr_positive < 3
    )
    tcr_systematically_below_spc = (
        sum(value < 0 for value in tcr_vs_spc.values()) >= 4
        and mean(list(tcr_vs_spc.values())) < 0
    )

    reasons = []
    if not technical:
        reasons.append("technical validity failure")
    if tcr_catastrophic_count >= 1:
        reasons.append("at least one catastrophic TCR seed")
    if stress_seed_2002["catastrophic"]:
        reasons.append("stress seed 2002 catastrophic")
    if bifurcation:
        reasons.append("cross-seed bifurcation")
    if systemic_safety:
        reasons.append("systemic safety deterioration")
    if tcr_systematically_below_utr:
        reasons.append("TCR systematically below UTR on OOD robustness")
    if tcr_systematically_below_spc:
        reasons.append("TCR systematically below SPC on OOD-worst")
    decision = "STOP_AT_2M" if reasons else "CONTINUE_TO_3M"
    result = {
        "protocol": "TCR-SPC-PHASE-D-2M-INTERIM-FUTILITY-V1",
        "decision": decision,
        "stop_reasons": reasons,
        "source_update": 3907,
        "interim_update": 7813,
        "interim_steps": 2_000_128,
        "tape_hash": tape["tape_hash"],
        "per_seed": per_seed,
        "pooled": pooled_metrics,
        "tcr_catastrophic": tcr_catastrophic,
        "spc_catastrophic": spc_catastrophic,
        "tcr_catastrophic_count": tcr_catastrophic_count,
        "stress_seed_2002_catastrophic": stress_seed_2002["catastrophic"],
        "tcr_ood_worst_positive_count": tcr_positive,
        "tcr_vs_spc_ood_worst": tcr_vs_spc,
        "technical_validity": technical,
        "cross_seed_bifurcation": bifurcation,
        "systemic_safety_deterioration": systemic_safety,
        "tcr_systematically_below_utr": tcr_systematically_below_utr,
        "tcr_systematically_below_spc": tcr_systematically_below_spc,
        "milestones_for_curve_only": True,
    }
    evaluation.joinpath("PHASE_D_2M_INTERIM_DECISION.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    args.report_path.parent.mkdir(parents=True, exist_ok=True)
    args.report_path.write_text(
        "# TCR/SPC Phase-D 2M Interim Stop-Loss Review\n\n"
        f"Decision: **{decision}**\n\n"
        "This is a pre-registered interim stop-loss check. It does not select a "
        "checkpoint, alter the Phase-D final 3M endpoint, or authorize any later phase.\n\n"
        f"Reasons: {', '.join(reasons) if reasons else 'none; all stop-loss conditions absent'}\n\n"
        f"Technical risk-set trigger validity: `{technical}`\n\n"
        "```json\n" + json.dumps(result, indent=2, sort_keys=True) + "\n```\n",
        encoding="utf-8", newline="\n"
    )
    print(json.dumps({"decision": decision, "reasons": reasons}, indent=2))


if __name__ == "__main__":
    main()
