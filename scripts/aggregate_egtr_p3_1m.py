"""Aggregate the frozen EGTR P3 1M development-only evaluation.

This program performs no evaluation or training.  It validates the already
written 10,800 episode records, computes seed-level metrics, and applies only
the P3 1M technical/learnability stop rules in the frozen contract.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
import statistics


PROTOCOL = "EGTR-P3-1M-AGGREGATION-V1"
ARMS = ("utr_sg", "drtp_sg", "egtr_sg")
SEEDS = (2501, 2502, 2503)
CONDITIONS = (
    "nominal", "f0_seen_44_80", "timing_28_80", "timing_36_80",
    "timing_52_80", "timing_60_80", "duration_44_40", "duration_44_60",
    "duration_44_100", "duration_44_120", "compound_28_120", "compound_60_120",
)
OOD_CONDITIONS = CONDITIONS[2:]
FAILURE_CONDITIONS = CONDITIONS[1:]
EPISODES_PER_CONDITION = 100
EXPECTED_ROWS = len(ARMS) * len(SEEDS) * len(CONDITIONS) * EPISODES_PER_CONDITION


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def mean(values: list[float]) -> float:
    finite = [value for value in values if math.isfinite(value)]
    return sum(finite) / len(finite) if finite else math.nan


def summary_row(rows: list[dict[str, str]], arm: str, seed: int, condition: str) -> dict[str, str]:
    matches = [
        row for row in rows
        if row["method"] == arm and int(row["train_seed"]) == seed and row["condition"] == condition
    ]
    if len(matches) != 1:
        raise RuntimeError(f"expected one summary row for {arm}/seed{seed}/{condition}, got {len(matches)}")
    return matches[0]


def metric_cell(summary: list[dict[str, str]], arm: str, seed: int) -> dict[str, float | int | str]:
    nominal = summary_row(summary, arm, seed, "nominal")
    f0 = summary_row(summary, arm, seed, "f0_seen_44_80")
    ood = [summary_row(summary, arm, seed, condition) for condition in OOD_CONDITIONS]
    failure = [f0, *ood]
    value = lambda row, key: float(row[key])
    return {
        "arm": arm,
        "seed": seed,
        "J_nominal": value(nominal, "J"),
        "J_F0": value(f0, "J"),
        "J_OOD_mean": mean([value(row, "J") for row in ood]),
        "J_OOD_worst": min(value(row, "J") for row in ood),
        "collision": mean([value(row, "collision") for row in failure]),
        "timeout": mean([value(row, "timeout") for row in failure]),
        "constraint_violation": mean([value(row, "constraint_violation") for row in failure]),
        "failure_exposure_all_scheduled": mean([value(row, "failure_exposure") for row in failure]),
    }


def pooled(cells: list[dict[str, float | int | str]]) -> dict[str, float]:
    numeric = [key for key in cells[0] if key not in {"arm", "seed"}]
    return {key: mean([float(cell[key]) for cell in cells]) for key in numeric}


def paired(candidate: dict[str, float | int | str], reference: dict[str, float | int | str]) -> dict[str, float | int | bool | str]:
    f0_ratio = float(candidate["J_F0"]) / float(reference["J_F0"])
    worst_ratio = float(candidate["J_OOD_worst"]) / float(reference["J_OOD_worst"])
    performance_collapse = (f0_ratio < 0.70 and worst_ratio < 0.85) or (worst_ratio < 0.70 and f0_ratio < 0.85)
    timeout_difference = float(candidate["timeout"]) - float(reference["timeout"])
    safety_associated_collapse = timeout_difference > 0.20 and (f0_ratio < 0.85 or worst_ratio < 0.85)
    return {
        "seed": int(candidate["seed"]),
        "J_nominal_difference": float(candidate["J_nominal"]) - float(reference["J_nominal"]),
        "J_F0_difference": float(candidate["J_F0"]) - float(reference["J_F0"]),
        "J_OOD_mean_difference": float(candidate["J_OOD_mean"]) - float(reference["J_OOD_mean"]),
        "J_OOD_worst_difference": float(candidate["J_OOD_worst"]) - float(reference["J_OOD_worst"]),
        "collision_difference": float(candidate["collision"]) - float(reference["collision"]),
        "timeout_difference": timeout_difference,
        "J_F0_ratio": f0_ratio,
        "J_OOD_worst_ratio": worst_ratio,
        "performance_collapse": performance_collapse,
        "safety_associated_collapse": safety_associated_collapse,
        "catastrophic": performance_collapse or safety_associated_collapse,
    }


def risk_set_audit(raw: list[dict[str, str]]) -> dict:
    failures = [row for row in raw if row["topology_condition"] != "nominal"]
    grouped: dict[tuple[str, int], list[dict[str, str]]] = {}
    for row in failures:
        grouped.setdefault((row["method"], int(row["train_seed"])), []).append(row)
    per_cell = []
    all_risk_exposed = True
    all_unexposed_pretrigger_collision = True
    for (arm, seed), rows in sorted(grouped.items()):
        risk = [row for row in rows if int(row["terminal_step"]) >= int(row["scheduled_failure_onset"])]
        exposed = [row for row in risk if int(row["failure_exposed"]) == 1]
        unexposed = [row for row in rows if int(row["failure_exposed"]) == 0]
        pretrigger_collision = [
            row for row in unexposed
            if int(row["terminal_step"]) < int(row["scheduled_failure_onset"]) and float(row["collision"]) == 1.0
        ]
        all_risk_exposed &= len(exposed) == len(risk)
        all_unexposed_pretrigger_collision &= len(pretrigger_collision) == len(unexposed)
        per_cell.append({
            "arm": arm,
            "seed": seed,
            "scheduled_failure_episodes": len(rows),
            "risk_set_size": len(risk),
            "survival_to_onset_fraction": len(risk) / len(rows),
            "triggered_in_risk_set": len(exposed),
            "failure_trigger_success_rate_risk_set": len(exposed) / len(risk) if risk else math.nan,
            "pretrigger_termination_count": len(unexposed),
            "pretrigger_collision_count": len(pretrigger_collision),
        })
    return {
        "per_cell": per_cell,
        "risk_set_trigger_validity": all_risk_exposed,
        "all_unexposed_are_pretrigger_collisions": all_unexposed_pretrigger_collision,
    }


def fmt(value: float) -> str:
    return f"{value:.3f}" if math.isfinite(value) else "NA"


def render_report(result: dict) -> str:
    metrics = "\n".join(
        f"| {row['arm']} | {row['seed']} | {fmt(float(row['J_nominal']))} | {fmt(float(row['J_F0']))} | {fmt(float(row['J_OOD_mean']))} | {fmt(float(row['J_OOD_worst']))} | {fmt(float(row['collision']))} | {fmt(float(row['timeout']))} |"
        for row in result["per_seed_metrics"]
    )
    comparisons = "\n".join(
        f"| {row['seed']} | {fmt(float(row['J_F0_difference']))} | {fmt(float(row['J_OOD_mean_difference']))} | {fmt(float(row['J_OOD_worst_difference']))} | {fmt(float(row['collision_difference']))} | {fmt(float(row['timeout_difference']))} | {row['catastrophic']} |"
        for row in result["egtr_minus_utr"]
    )
    risk = "\n".join(
        f"| {row['arm']} | {row['seed']} | {row['risk_set_size']}/{row['scheduled_failure_episodes']} | {fmt(float(row['survival_to_onset_fraction']))} | {row['triggered_in_risk_set']}/{row['risk_set_size']} | {row['pretrigger_collision_count']} |"
        for row in result["risk_set_audit"]["per_cell"]
    )
    return f"""# EGTR P3 — 1M Development 评估与阶段门报告

**裁决：** `{result['decision']}`。

本报告仅覆盖 development-only 的 1M 可学习性/机制筛查，不构成论文 superiority、confirmatory 或 held-out 结论。未发生 checkpoint promotion，本次汇总未启动 3M 续训。

## 完整性与 evaluator 有效性

- 要求的 final-checkpoint cells：`9/9`；原始记录：`{result['integrity']['raw_rows']}/10,800`。
- 冻结 development tape SHA256：`{result['tape_hash']}`；未使用 canonical 或 held-out。
- 9 条 manifest 均记录 from-scratch 的 1,000,192-step completion、116,728 参数、final checkpoint only 和 runtime-state persistence：`{result['integrity']['source_contracts_valid']}`。
- 对于 alive-at-onset risk set 的 trigger success：`{result['risk_set_audit']['risk_set_trigger_validity']}`。所有未暴露记录均为 onset 前 collision：`{result['risk_set_audit']['all_unexposed_are_pretrigger_collisions']}`。

| Arm | Seed | Risk set / scheduled | Survival to onset | Triggered / risk set | Pre-trigger collisions |
|---|---:|---:|---:|---:|---:|
{risk}

onset 前 collision 保留在所有无条件 return 与 safety 指标中；没有被删除，也没有被重新标记为 failure exposure。

## 每个 seed 的 1M final-checkpoint 指标

| Arm | Seed | J nominal | J F0 | J pert mean | J pert worst | Collision | Timeout |
|---|---:|---:|---:|---:|---:|---:|---:|
{metrics}

## EGTR 相对 paired UTR

| Seed | ΔF0 | Δpert mean | Δpert worst | Δcollision | Δtimeout | Existing catastrophic definition |
|---:|---:|---:|---:|---:|---:|---|
{comparisons}

既有 catastrophic definition 原样保留；它在 EGTR 的 1M 结果中没有触发。但 seed2503 的 collision 明显上升（`{fmt(float(result['egtr_minus_utr'][2]['collision_difference']))}`），同时 timeout 下降。这是 safety trade-off，不是 evaluator defect，也不能被 pooled return 掩盖。

## 冻结的 1M 机制审计

已完成的训练审计记录了每个 EGTR seed 在 122 个 boundary 中有 118 次 adaptive sampler update，存在非零但有界的 uniform 偏移，无 simplex/trust-region 违规，并且 runtime state 已持久化。因此 EGTR 既不是静默的 uniform fallback，也不是 technical invalid 实现。本次评估补齐了完整且 risk-set-valid 的性能和 safety records。

## 阶段门解释与停止状态

`{result['decision']}` 表示 1M 的 technical 与 mechanism 部分有效，但 P3 合同没有量化“明显 safety warning”的判据。seed2503 已观察到的 collision trade-off 阻止我们把它自动写成 clean safety PASS；不得在看到结果后临时发明新的冻结阈值。

因此本报告**不授权 3M**。后续必须依据既有冻结合同作出明确决定：要么把已记录的 collision trade-off 视为合同中的 safety warning 并停止 P3；要么在任何续训前以 prospective amendment 明确 safety decision rule。两种路径均不允许调参、替换 seed、checkpoint promotion 或 EGTR-v2。
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evaluation-root", type=Path, required=True)
    parser.add_argument("--report-path", type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads((args.evaluation_root / "evaluation_manifest.json").read_text(encoding="utf-8"))
    raw = read_csv(args.evaluation_root / "raw_episode_metrics.csv")
    summary = read_csv(args.evaluation_root / "per_seed_condition_summary.csv")
    if manifest.get("status") != "completed" or manifest.get("raw_rows") != EXPECTED_ROWS or len(raw) != EXPECTED_ROWS:
        raise RuntimeError("TECHNICAL INVALID: incomplete P3 evaluation")
    if manifest.get("cells") != len(ARMS) * len(SEEDS) or manifest.get("episodes_per_condition") != EPISODES_PER_CONDITION:
        raise RuntimeError("TECHNICAL INVALID: P3 cell or episode count mismatch")
    expected_summary = {(arm, seed, condition) for arm in ARMS for seed in SEEDS for condition in CONDITIONS}
    found_summary = {(row["method"], int(row["train_seed"]), row["condition"]) for row in summary}
    if found_summary != expected_summary or len(summary) != len(expected_summary):
        raise RuntimeError("TECHNICAL INVALID: summary condition/cell mismatch")
    expected_raw = {(arm, seed, condition) for arm in ARMS for seed in SEEDS for condition in CONDITIONS}
    found_raw = {(row["method"], int(row["train_seed"]), row["topology_condition"]) for row in raw}
    if found_raw != expected_raw:
        raise RuntimeError("TECHNICAL INVALID: raw condition/cell mismatch")
    source_runs = manifest.get("source_runs", [])
    source_contracts_valid = len(source_runs) == 9 and all(
        run.get("status") == "completed"
        and run.get("updates") == 3907
        and run.get("environment_steps") == 1000192
        and run.get("parameter_count") == 116728
        and run.get("from_scratch") is True
        and run.get("resume") is False
        and run.get("checkpoint_promotion") is False
        and run.get("runtime_state_persistence_from_step_zero") is True
        for run in source_runs
    )
    cells = [metric_cell(summary, arm, seed) for arm in ARMS for seed in SEEDS]
    by_arm = {arm: [cell for cell in cells if cell["arm"] == arm] for arm in ARMS}
    egtr_minus_utr = [
        paired(next(cell for cell in by_arm["egtr_sg"] if cell["seed"] == seed), next(cell for cell in by_arm["utr_sg"] if cell["seed"] == seed))
        for seed in SEEDS
    ]
    egtr_minus_drtp = [
        paired(next(cell for cell in by_arm["egtr_sg"] if cell["seed"] == seed), next(cell for cell in by_arm["drtp_sg"] if cell["seed"] == seed))
        for seed in SEEDS
    ]
    risk = risk_set_audit(raw)
    catastrophic_count = sum(bool(row["catastrophic"]) for row in egtr_minus_utr)
    integrity = {
        "raw_rows": len(raw),
        "source_contracts_valid": source_contracts_valid,
        "manifest_completed": manifest.get("status") == "completed",
        "canonical_seeds_used": manifest.get("canonical_seeds_used"),
        "held_out_tape_used": manifest.get("held_out_tape_used"),
    }
    technical_pass = source_contracts_valid and risk["risk_set_trigger_validity"] and risk["all_unexposed_are_pretrigger_collisions"]
    if not technical_pass:
        decision = "P3_1M_TECHNICAL_INVALID"
    elif catastrophic_count:
        decision = "P3_1M_STOP__CATASTROPHIC_PATTERN"
    else:
        decision = "P3_1M_TECHNICAL_AND_MECHANISM_PASS__SAFETY_REVIEW_REQUIRED"
    result = {
        "protocol": PROTOCOL,
        "decision": decision,
        "tape_hash": manifest["tape_hash"],
        "primary_inference_unit": "training_seed",
        "n_paired_training_seeds": len(SEEDS),
        "integrity": integrity,
        "per_seed_metrics": cells,
        "pooled_descriptive_metrics": {arm: pooled(by_arm[arm]) for arm in ARMS},
        "egtr_minus_utr": egtr_minus_utr,
        "egtr_minus_drtp": egtr_minus_drtp,
        "egtr_catastrophic_seed_count": catastrophic_count,
        "risk_set_audit": risk,
        "three_m_started": False,
        "automatic_follow_on_started": False,
    }
    (args.evaluation_root / "EGTR_P3_1M_GATE_DECISION.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    args.report_path.parent.mkdir(parents=True, exist_ok=True)
    with args.report_path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(render_report(result))
    print(json.dumps({"decision": decision, "report": str(args.report_path)}, indent=2))


if __name__ == "__main__":
    main()
