"""Aggregate the additional unseen-condition evaluation without pooling cohorts."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from create_drtp_additional_unseen_tape import CONDITIONS, EPISODES


PROTOCOL = "DRTP-ADDITIONAL-UNSEEN-CONDITION-AGGREGATION-V1"
COHORTS = ("formal_2301_2305", "independent_2401_2405")


def read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("NO-GO: explicit --execute is required")
    root = args.output_root
    manifest = json.loads((root / "evaluation_manifest.json").read_text(encoding="utf-8"))
    raw = read_csv(root / "raw_episode_metrics.csv")
    effects = read_csv(root / "paired_effects_by_cohort_condition.csv")
    expected = 20 * len(CONDITIONS) * EPISODES
    checks = {
        "evaluation_completed": manifest.get("status") == "completed",
        "no_training_started": manifest.get("training_started") is False,
        "complete_raw_records": len(raw) == expected == int(manifest.get("expected_rows", -1)),
        "all_conditions_present": {row["topology_condition"] for row in raw} == set(CONDITIONS),
        "both_cohorts_present": {row["training_cohort"] for row in raw} == set(COHORTS),
        "cross_cohort_pooling_prohibited": manifest.get("cross_cohort_pooling_prohibited") is True,
        "all_scheduled_retained": manifest.get("all_scheduled_episodes_retained") is True,
    }
    if not all(checks.values()):
        raise RuntimeError(f"technical validity failure: {checks}")
    report = [
        "# DRTP 附加未见条件评价报告", "",
        "**状态：** `ADDITIONAL_UNSEEN_EVALUATION_COMPLETE`", "",
        "本报告为一次性、零训练、post hoc 的附加未见条件评价；它不是原始前瞻性确认合同的一部分。"
        "正式 cohort 与独立 cohort 分层报告，不合并为同质训练 seed 样本。", "",
        "## DRTP--UTR 配对差", "",
        "| cohort | condition | metric | mean | median | wins/5 | worst |",
        "|---|---|---|---:|---:|---:|---:|",
    ]
    for row in effects:
        report.append(
            f"| {row['training_cohort']} | {row['condition']} | {row['metric']} | "
            f"{float(row['mean_drtp_minus_utr']):.3f} | {float(row['median_drtp_minus_utr']):.3f} | "
            f"{row['wins_over_zero']}/5 | {float(row['worst_drtp_minus_utr']):.3f} |"
        )
    report += [
        "", "## 解释边界", "",
        "该结果仅更新既有最终 checkpoint 在训练采样支持集之外六个 onset--duration 条件上的表现边界。"
        "它不修改历史正式/独立 cohort 的原有结论，不证明一般分布鲁棒性或训练种子稳定性，也不授权进一步训练或方法修改。", "",
    ]
    (root / "DRTP_ADDITIONAL_UNSEEN_EVALUATION_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    decision = {"protocol": PROTOCOL, "status": "ADDITIONAL_UNSEEN_EVALUATION_COMPLETE", "checks": checks,
                "training_started": False, "follow_on_training_authorized": False,
                "interpretation": "additional post hoc unseen-condition evidence only; cohorts remain stratified"}
    (root / "DRTP_ADDITIONAL_UNSEEN_EVALUATION_DECISION.json").write_text(
        json.dumps(decision, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(decision, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
