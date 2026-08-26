"""Aggregate MAPPO-NoGraph as an external reference without revising DRTP's formal verdict."""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
import statistics
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))

import aggregate_drtp_sg_development as base  # noqa: E402
from create_drtp_utr_q2_formal_tape import SEEDS, frozen_manifest  # noqa: E402


PROTOCOL = "DRTP-MAPPO-NOGRAPH-EXTERNAL-REFERENCE-5SEED-AGGREGATION-V1"
FINAL_LABEL = "10m"
ARMS = ("utr_sg", "drtp_sg", "mappo_ng")
ENDPOINTS = ("J_nominal", "J_F0", "J_OOD_mean", "J_OOD_worst")


def paired(values: list[float]) -> dict:
    return {"n": len(values), "mean": statistics.mean(values), "median": statistics.median(values),
            "sample_sd": statistics.stdev(values), "wins": sum(value > 0 for value in values),
            "worst": min(values), "best": max(values), "values": values}


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--results-root", type=Path, required=True)
    parser.add_argument("--report-path", type=Path, required=True); args = parser.parse_args()
    tape = frozen_manifest()
    result_root = args.results_root / "evaluations" / "final_10m"
    manifest = json.loads((result_root / "evaluation_manifest.json").read_text(encoding="utf-8"))
    if manifest.get("status") != "completed" or manifest.get("raw_rows") != 6000 or manifest.get("tape_hash") != tape["tape_hash"]:
        raise RuntimeError("incomplete or mismatched MAPPO external evaluation")
    source = ROOT / "paper" / "q2_final_zh" / "formal_results" / "source_data"
    existing_manifest = json.loads((source / "evaluation_manifest.json").read_text(encoding="utf-8"))
    if existing_manifest.get("tape_hash") != tape["tape_hash"]:
        raise RuntimeError("UTR/DRTP source evaluation is not on the same frozen tape")
    rows = base.rows_from(source / "per_seed_condition_summary.csv") + base.rows_from(result_root / "per_seed_condition_summary.csv")
    ood = tuple(item["name"] for item in tape["conditions"][2:])
    cells = [base.metrics(rows, arm, seed, FINAL_LABEL, ood) for arm in ARMS for seed in SEEDS]
    by_arm = {arm: [cell for cell in cells if cell["arm"] == arm] for arm in ARMS}
    pooled = {arm: base.pooled(by_arm[arm]) for arm in ARMS}
    pair_rows = []
    summaries = {}
    for comparator in ("utr_sg", "drtp_sg"):
        for endpoint in ENDPOINTS:
            values = []
            for seed in SEEDS:
                ref = next(item for item in by_arm[comparator] if item["seed"] == seed)
                candidate = next(item for item in by_arm["mappo_ng"] if item["seed"] == seed)
                delta = candidate[endpoint] - ref[endpoint]; values.append(delta)
                pair_rows.append({"comparison": f"mappo_ng_minus_{comparator}", "seed": seed, "endpoint": endpoint,
                                  "reference": ref[endpoint], "mappo_ng": candidate[endpoint], "delta": delta,
                                  "ratio": candidate[endpoint] / ref[endpoint] if ref[endpoint] else math.nan})
            summaries[f"mappo_ng_minus_{comparator}:{endpoint}"] = paired(values)
    write_csv(result_root / "external_reference_paired_effects.csv", pair_rows)
    result = {"protocol": PROTOCOL, "status": "EXTERNAL_REFERENCE_COMPLETE", "tape_hash": tape["tape_hash"],
              "independent_inference_unit": "training_seed", "n_paired_seeds": 5, "pooled": pooled,
              "paired_external_effects": summaries, "historical_utr_drtp_formal_verdict_preserved": True,
              "external_reference_not_a_causal_ablation": True, "automatic_follow_on_started": False}
    (result_root / "DRTP_MAPPO_EXTERNAL_REFERENCE_DECISION.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    lines = ["# DRTP 与 MAPPO-NoGraph 外部参考比较", "", "**状态：** `EXTERNAL_REFERENCE_COMPLETE`", "",
             "该分析将新训练的 MAPPO-NoGraph 与已冻结的 UTR/DRTP 正式五种子结果置于同一 490000–490099 评价 tape。",
             "UTR–DRTP 仍是同构训练设计下的主消融；MAPPO-NoGraph 是外部参考，架构差异不得用于归因 DRTP 的自适应加权效应。", "",
             "## 汇总性能", "", "| 方法 | J_nominal | J_F0 | J_OOD_mean | J_OOD_worst | 碰撞(故障均值) | 超时(故障均值) |", "|---|---:|---:|---:|---:|---:|---:|"]
    for arm in ARMS:
        item = pooled[arm]
        lines.append(f"| {arm} | {item['J_nominal']:.4g} | {item['J_F0']:.4g} | {item['J_OOD_mean']:.4g} | {item['J_OOD_worst']:.4g} | {item['collision_failure_mean']:.4g} | {item['timeout_failure_mean']:.4g} |")
    lines += ["", "## MAPPO-NoGraph 的配对差（MAPPO − reference）", "", "| 对比 | 指标 | mean | median | wins/5 | worst |", "|---|---|---:|---:|---:|---:|"]
    for name, item in summaries.items():
        comparison, endpoint = name.split(":")
        lines.append(f"| {comparison} | {endpoint} | {item['mean']:.4g} | {item['median']:.4g} | {item['wins']}/5 | {item['worst']:.4g} |")
    lines += ["", "所有五个训练种子、最终 10M checkpoint 与全部已计划 episode 均被保留；本报告不改写历史 DRTP/UTR 正式结论，也不授权后续训练。", ""]
    args.report_path.parent.mkdir(parents=True, exist_ok=True); args.report_path.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__": main()
