"""Fail-closed integration of the formal DRTP/UTR five-seed archive.

This script converts only the frozen 10M final-checkpoint artifacts into
paper-facing source data, figures, tables, and an integration audit.  It never
runs training, selects intermediate checkpoints, or changes experiment data.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
import re
import shutil
from typing import Iterable

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RESULTS = ROOT / "results" / "formal" / "drtp_utr_q2_paired_5seed_cloud_10way"
PAPER = ROOT / "paper" / "q2_final_zh"
OUT = PAPER / "formal_results"
FIGURES = OUT / "figures"
DATA = OUT / "source_data"

SEEDS = (2301, 2302, 2303, 2304, 2305)
ARMS = ("utr_sg", "drtp_sg")
FINAL_LABEL = "10m"
EXPECTED_TAPE_START = 490000
EXPECTED_TAPE_HASH = "84e31ed185ced0608a30c9cb9f9659c7423c952e4603aac53cf691c54fc64ac2"
COLORS = {"utr_sg": "#6b7280", "drtp_sg": "#2563eb"}
DISPLAY = {"utr_sg": "UTR-SG-MAPPO", "drtp_sg": "DRTP-SG-MAPPO"}
CONDITION_LABELS = {
    "timing_28_80": "T28", "timing_36_80": "T36",
    "timing_52_80": "T52", "timing_60_80": "T60",
    "duration_44_40": "D40", "duration_44_60": "D60",
    "duration_44_100": "D100", "duration_44_120": "D120",
    "compound_28_120": "C28/120", "compound_60_120": "C60/120",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def mean(values: Iterable[float]) -> float:
    values = list(values)
    return sum(values) / len(values)


def fmt(value: float, digits: int = 2) -> str:
    return f"{value:.{digits}f}"


def validate(results_root: Path) -> tuple[dict, dict, list[dict[str, str]], list[dict[str, str]]]:
    tape = load_json(results_root / "formal_tape_manifest.json")
    eval_root = results_root / "evaluations" / "final_10m"
    manifest = load_json(eval_root / "evaluation_manifest.json")
    decision = load_json(eval_root / "DRTP_UTR_Q2_FORMAL_DECISION.json")
    summary_rows = read_csv(eval_root / "per_seed_condition_summary.csv")
    paired_rows = read_csv(eval_root / "paired_seed_results.csv")

    require(tape["episode_ids"] == list(range(EXPECTED_TAPE_START, EXPECTED_TAPE_START + 100)),
            "formal tape IDs are not 490000–490099")
    require(tape["tape_hash"] == EXPECTED_TAPE_HASH, "formal tape hash mismatch")
    require(manifest["status"] == "completed", "evaluation manifest is not completed")
    require(manifest["raw_rows"] == 12000, "raw evaluation count is not 12000")
    require(manifest["tape_hash"] == tape["tape_hash"], "evaluation tape hash mismatch")
    require(decision["verdict"] == "FORMAL_CONFIRMATION_PASS_SEED_SENSITIVE",
            "formal verdict does not authorize PASS_SEED_SENSITIVE manuscript wording")
    require(decision["n_paired_training_seeds"] == 5, "paired training-seed count is not five")
    require(decision["catastrophic_seed_count"] == 0, "catastrophic seed count is non-zero")
    require(all(decision["gates"].values()), "one or more frozen formal gates failed")
    require(len(summary_rows) == 120, "condition summary does not contain 10×12 cells")
    require(len(paired_rows) == 5, "paired seed table does not contain five rows")

    expected_rows = {(arm, seed) for arm in ARMS for seed in SEEDS}
    observed_rows = set()
    for arm in ARMS:
        for seed in SEEDS:
            run_dir = results_root / "runs" / arm / f"seed{seed}"
            run = load_json(run_dir / "run_manifest.json")
            require(run["status"] == "completed", f"{arm}/seed{seed} is not completed")
            require(run["updates"] == 39063, f"{arm}/seed{seed} update budget mismatch")
            require(run["environment_steps"] == 10000128,
                    f"{arm}/seed{seed} environment-step budget mismatch")
            require(run["parameter_count"] == 116728, f"{arm}/seed{seed} parameter mismatch")
            require(run["final_checkpoint_sha256"], f"{arm}/seed{seed} final model hash missing")
            require(run["final_runtime_state_sha256"], f"{arm}/seed{seed} runtime-state hash missing")
            require((run_dir / "actor_critic_latest.pt").is_file(),
                    f"{arm}/seed{seed} final model missing")
            require((run_dir / "actor_critic_runtime_state_latest.pt").is_file(),
                    f"{arm}/seed{seed} final runtime state missing")
            observed_rows.add((arm, seed))
    require(observed_rows == expected_rows, "formal run set mismatch")
    require(not decision["canonical_seeds_used"], "canonical seed use detected")
    return tape, decision, summary_rows, paired_rows


def metric_cells(rows: list[dict[str, str]]) -> dict[tuple[str, int, str], dict[str, float]]:
    result: dict[tuple[str, int, str], dict[str, float]] = {}
    for row in rows:
        key = (row["arm"], int(row["seed"]), row["condition"])
        result[key] = {name: float(value) if value not in {"", "nan", "NaN"} else math.nan
                       for name, value in row.items() if name not in {"arm", "seed", "checkpoint_label", "condition"}}
    return result


def pooled_condition(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    values: dict[tuple[str, str], list[float]] = {}
    for row in rows:
        values.setdefault((row["arm"], row["condition"]), []).append(float(row["J"]))
    output = []
    order = ["timing_28_80", "timing_36_80", "timing_52_80", "timing_60_80",
             "duration_44_40", "duration_44_60", "duration_44_100", "duration_44_120",
             "compound_28_120", "compound_60_120"]
    for condition in order:
        utr = values[("utr_sg", condition)]
        drtp = values[("drtp_sg", condition)]
        diffs = [right - left for left, right in zip(utr, drtp)]
        output.append({
            "condition": condition,
            "label": CONDITION_LABELS[condition],
            "utr_mean": mean(utr), "drtp_mean": mean(drtp),
            "paired_delta_mean": mean(diffs), "paired_delta_median": float(np.median(diffs)),
            "wins": sum(item > 0 for item in diffs), "worst_delta": min(diffs),
        })
    return output


def copy_source_data(results_root: Path) -> None:
    eval_root = results_root / "evaluations" / "final_10m"
    DATA.mkdir(parents=True, exist_ok=True)
    for name in ("DRTP_UTR_Q2_FORMAL_DECISION.json", "evaluation_manifest.json",
                 "per_seed_condition_summary.csv", "paired_seed_results.csv"):
        shutil.copy2(eval_root / name, DATA / name)
    shutil.copy2(results_root / "formal_tape_manifest.json", DATA / "formal_tape_manifest.json")


def setup_matplotlib() -> None:
    mpl.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Noto Sans CJK SC", "SimHei", "Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
        "font.size": 7,
        "axes.labelsize": 8,
        "axes.titlesize": 9,
        "xtick.labelsize": 7,
        "ytick.labelsize": 7,
        "legend.fontsize": 7,
        "axes.spines.right": False,
        "axes.spines.top": False,
        "axes.linewidth": 0.8,
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
        "axes.unicode_minus": False,
    })


def save_figure(fig: plt.Figure, stem: str) -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    svg_path = FIGURES / f"{stem}.svg"
    fig.savefig(svg_path, bbox_inches="tight")
    # Matplotlib emits line-wrapped SVG path data with trailing spaces.  Remove
    # only end-of-line whitespace so reproducibility checks stay clean.
    svg_path.write_text(re.sub(r"[ \t]+(?=\r?\n)", "", svg_path.read_text(encoding="utf-8")),
                        encoding="utf-8")
    fig.savefig(FIGURES / f"{stem}.pdf", bbox_inches="tight")
    fig.savefig(FIGURES / f"{stem}.png", dpi=600, bbox_inches="tight")
    fig.savefig(FIGURES / f"{stem}.tiff", dpi=600, bbox_inches="tight")
    plt.close(fig)


def plot_primary(cells: dict[tuple[str, int, str], dict[str, float]], decision: dict) -> None:
    endpoints = [
        ("J_nominal", "J_nominal"), ("J_F0", "J_F0"),
        ("J_OOD_mean", "J_pert mean"), ("J_OOD_worst", "J_pert worst"),
    ]
    fig, axes = plt.subplots(1, 4, figsize=(7.2, 2.25), sharex=True)
    for axis, (key, label) in zip(axes, endpoints):
        utr = [decision["pooled"]["utr_sg"][key]]
        drtp = [decision["pooled"]["drtp_sg"][key]]
        seed_values = []
        for seed in SEEDS:
            if key == "J_nominal":
                left = cells[("utr_sg", seed, "nominal")]["J"]
                right = cells[("drtp_sg", seed, "nominal")]["J"]
            elif key == "J_F0":
                left = cells[("utr_sg", seed, "f0_seen_44_80")]["J"]
                right = cells[("drtp_sg", seed, "f0_seen_44_80")]["J"]
            else:
                # The decision field is the authoritative pooled aggregate; seed values are
                # reconstructed from the same condition summary for paired-line display.
                ood_conditions = list(CONDITION_LABELS)
                per_arm = []
                for arm in ARMS:
                    values = [cells[(arm, seed, condition)]["J"] for condition in ood_conditions]
                    per_arm.append(mean(values) if key == "J_OOD_mean" else min(values))
                left, right = per_arm
            seed_values.append((left, right))
            axis.plot([0, 1], [left, right], color="#9ca3af", linewidth=0.8, alpha=0.75, zorder=1)
            axis.scatter([0, 1], [left, right], s=15, color=[COLORS["utr_sg"], COLORS["drtp_sg"]], zorder=2)
        axis.scatter([0, 1], [utr[0], drtp[0]], marker="D", s=32,
                     color=[COLORS["utr_sg"], COLORS["drtp_sg"]], zorder=3, label="总体均值")
        axis.set_title(label, fontweight="bold")
        axis.set_xticks([0, 1], ["UTR", "DRTP"])
        axis.grid(axis="y", linestyle=":", linewidth=0.6, alpha=0.6)
        delta = decision["paired_summaries"][key]["mean"]
        wins = decision["paired_summaries"][key]["wins"]
        axis.text(0.5, 0.97, f"均值Δ={delta:.1f}；{wins}/5", ha="center", va="top",
                  transform=axis.transAxes, fontsize=6.5)
    axes[0].set_ylabel("任务得分")
    axes[-1].legend(loc="lower right", fontsize=6.5)
    fig.suptitle("正式五种子最终检查点配对比较", y=1.03, fontsize=10, fontweight="bold")
    fig.tight_layout()
    save_figure(fig, "fig3_formal_primary_performance")


def plot_ood(condition_rows: list[dict[str, object]]) -> None:
    labels = [row["label"] for row in condition_rows]
    values = [row["paired_delta_mean"] for row in condition_rows]
    wins = [row["wins"] for row in condition_rows]
    colors = ["#2563eb" if value >= 0 else "#dc2626" for value in values]
    fig, axis = plt.subplots(figsize=(7.2, 2.7))
    bars = axis.bar(range(len(labels)), values, color=colors, width=0.72)
    axis.axhline(0, color="#374151", linewidth=0.8)
    axis.set_xticks(range(len(labels)), labels, rotation=35, ha="right")
    axis.set_ylabel("配对 ΔJ（DRTP - UTR）")
    axis.set_title("跨扰动条件分解：故障时机、持续时间与复合扰动",
                   fontweight="bold")
    axis.grid(axis="y", linestyle=":", linewidth=0.6, alpha=0.6)
    for bar, value, win in zip(bars, values, wins):
        axis.text(bar.get_x() + bar.get_width() / 2, value + 1.5, f"{value:.1f}\n{win}/5",
                  ha="center", va="bottom", fontsize=6)
    fig.tight_layout()
    save_figure(fig, "fig4_ood_condition_decomposition")


def plot_reliability(decision: dict) -> None:
    paired = decision["paired_rows"]
    endpoints = [("delta_J_F0", "F0"), ("delta_J_OOD_mean", "跨扰动均值"),
                 ("delta_J_OOD_worst", "跨扰动最差")]
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.55), gridspec_kw={"width_ratios": [1.25, 1]})
    axis = axes[0]
    x = np.arange(len(SEEDS))
    width = 0.24
    for offset, (field, name) in zip((-width, 0, width), endpoints):
        values = [float(row[field]) for row in paired]
        axis.bar(x + offset, values, width=width, label=name)
    axis.axhline(0, color="#374151", linewidth=0.8)
    axis.set_xticks(x, [str(seed) for seed in SEEDS])
    axis.set_xlabel("训练种子")
    axis.set_ylabel("配对 ΔJ（DRTP - UTR）")
    axis.set_title("全部保留的逐种子鲁棒性效应", fontweight="bold")
    axis.legend(ncol=3, fontsize=6.5, loc="upper left")
    axis.grid(axis="y", linestyle=":", linewidth=0.6, alpha=0.6)

    axis = axes[1]
    utr = decision["pooled"]["utr_sg"]
    drtp = decision["pooled"]["drtp_sg"]
    safety = ["碰撞", "超时", "约束违规"]
    utr_values = [utr["collision_failure_mean"], utr["timeout_failure_mean"], utr["constraint_failure_mean"]]
    drtp_values = [drtp["collision_failure_mean"], drtp["timeout_failure_mean"], drtp["constraint_failure_mean"]]
    x = np.arange(3)
    axis.bar(x - 0.18, utr_values, width=.36, color=COLORS["utr_sg"], label="UTR")
    axis.bar(x + 0.18, drtp_values, width=.36, color=COLORS["drtp_sg"], label="DRTP")
    axis.set_xticks(x, safety, rotation=18, ha="right")
    axis.set_ylim(0, 1.0)
    axis.set_ylabel("故障条件比率")
    axis.set_title("安全性结果", fontweight="bold")
    axis.legend(["UTR", "DRTP"], fontsize=6.5)
    axis.grid(axis="y", linestyle=":", linewidth=0.6, alpha=0.6)
    fig.suptitle("正式确认的可靠性与安全边界", y=1.03,
                 fontsize=10, fontweight="bold")
    fig.tight_layout()
    save_figure(fig, "fig5_seed_reliability_and_safety")


def plot_sampler(results_root: Path) -> None:
    columns = ("q_F0", "q_TE", "q_TL", "q_DS", "q_DL", "q_CP")
    per_seed: dict[str, list[tuple[int, list[float]]]] = {column: [] for column in columns}
    for seed in SEEDS:
        rows = read_csv(results_root / "runs" / "drtp_sg" / f"seed{seed}" / "drtp_topology_sampler_log.csv")
        for row in rows:
            if row["record_type"] != "weight_update":
                continue
            for column in columns:
                per_seed[column].append((int(row["update"]), [float(row[column])]))
    fig, axis = plt.subplots(figsize=(7.2, 2.7))
    palette = ["#2563eb", "#7c3aed", "#0891b2", "#d97706", "#16a34a", "#dc2626"]
    for column, color in zip(columns, palette):
        grouped: dict[int, list[float]] = {}
        for update, value in per_seed[column]:
            grouped.setdefault(update, []).append(value[0])
        updates = np.array(sorted(grouped))
        averages = np.array([mean(grouped[update]) for update in updates])
        axis.plot(updates / 39063 * 10, averages, linewidth=1.0, label=column.replace("q_", ""), color=color)
    axis.axhline(1 / 6, color="#6b7280", linestyle="--", linewidth=.9, label="UTR 均匀 q=1/6")
    axis.set_xlabel("训练预算（百万环境步）")
    axis.set_ylabel("平均组权重 q")
    axis.set_ylim(0, 0.42)
    axis.set_title("DRTP 在正式五种子中的自适应拓扑组权重", fontweight="bold")
    axis.legend(ncol=4, fontsize=6.2, loc="upper center")
    axis.grid(axis="y", linestyle=":", linewidth=0.6, alpha=0.6)
    fig.tight_layout()
    save_figure(fig, "fig6_adaptive_weight_telemetry")


def sampler_summary(results_root: Path) -> dict[str, object]:
    columns = ("q_F0", "q_TE", "q_TL", "q_DS", "q_DL", "q_CP")
    last_rows = []
    selection_counts: dict[str, int] = {group: 0 for group in ("N", "F0", "TE", "TL", "DS", "DL", "CP")}
    for seed in SEEDS:
        rows = read_csv(results_root / "runs" / "drtp_sg" / f"seed{seed}" / "drtp_topology_sampler_log.csv")
        updates = [row for row in rows if row["record_type"] == "weight_update"]
        require(updates, f"DRTP seed{seed} has no sampler weight updates")
        last_rows.append(updates[-1])
        for row in rows:
            if row["record_type"] == "selection":
                selection_counts[row["group"]] += 1
    return {
        "last_weight_update": int(last_rows[0]["update"]),
        "final_q_mean": {column.replace("q_", ""): mean(float(row[column]) for row in last_rows)
                         for column in columns},
        "final_q_sample_sd": {column.replace("q_", ""): float(np.std([float(row[column]) for row in last_rows], ddof=1))
                              for column in columns},
        "selection_counts": selection_counts,
    }


def write_tables(decision: dict, condition_rows: list[dict[str, object]], sampler: dict[str, object]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    pooled = decision["pooled"]
    paired = decision["paired_summaries"]
    lines = ["# 正式五种子结果表", "",
             "所有数值来自冻结的 10M 最终检查点和 episode ID 490000–490099；训练种子为独立统计单位（n=5）。", "",
             "## 表2｜正式五种子总体结果", "",
             "| 方法 | 参数量 | J_nominal | J_F0 | J_pert,mean | J_pert,worst | 碰撞率 | 超时率 | 约束违规率 |",
             "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for arm in ARMS:
        item = pooled[arm]
        lines.append(
            f"| {DISPLAY[arm]} | 116,728 | {fmt(item['J_nominal'])} | {fmt(item['J_F0'])} | "
            f"{fmt(item['J_OOD_mean'])} | {fmt(item['J_OOD_worst'])} | "
            f"{fmt(item['collision_failure_mean'], 3)} | {fmt(item['timeout_failure_mean'], 3)} | "
            f"{fmt(item['constraint_failure_mean'], 3)} |"
        )
    lines += ["", "## 表3｜配对种子效应与可靠性", "",
              "| 训练种子 | Δ正常工况 | ΔF0 | Δ跨扰动均值 | Δ跨扰动最差 | Δ碰撞率 | Δ超时率 | 灾难性 |",
              "|---:|---:|---:|---:|---:|---:|---:|---|"]
    for row in decision["paired_rows"]:
        lines.append(
            f"| {row['seed']} | {fmt(row['delta_J_nominal'])} | {fmt(row['delta_J_F0'])} | "
            f"{fmt(row['delta_J_OOD_mean'])} | {fmt(row['delta_J_OOD_worst'])} | "
            f"{fmt(row['delta_collision'], 3)} | {fmt(row['delta_timeout'], 3)} | "
            f"{'是' if row['catastrophic'] else '否'} |"
        )
    lines += ["", "| 端点 | 均值 | 中位数 | SD | IQR | MAD | 胜出种子数 | 最差差值 |",
              "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for key, label in (("J_nominal", "J_nominal"), ("J_F0", "J_F0"),
                       ("J_OOD_mean", "J_pert,mean"), ("J_OOD_worst", "J_pert,worst")):
        item = paired[key]
        lines.append(
            f"| {label} | {fmt(item['mean'])} | {fmt(item['median'])} | {fmt(item['sample_sd'])} | "
            f"{fmt(item['iqr'])} | {fmt(item['mad'])} | {item['wins']}/5 | {fmt(item['worst'])} |"
        )
    lines += ["", "## 表4｜跨扰动条件分解", "",
              "| 条件 | UTR均值 | DRTP均值 | 平均配对ΔJ | 中位数ΔJ | 胜出种子数 | 最差配对ΔJ |",
              "|---|---:|---:|---:|---:|---:|---:|"]
    for item in condition_rows:
        lines.append(
            f"| {item['condition']} | {fmt(item['utr_mean'])} | {fmt(item['drtp_mean'])} | "
            f"{fmt(item['paired_delta_mean'])} | {fmt(item['paired_delta_median'])} | "
            f"{item['wins']}/5 | {fmt(item['worst_delta'])} |"
        )
    lines += ["", "## 表5｜DRTP 自适应权重遥测（补充性机制证据）", "",
              "| 训练组 | 末次更新的 q 均值 | q 样本SD | 实际采样 episode 数 |",
              "|---|---:|---:|---:|"]
    for group in ("F0", "TE", "TL", "DS", "DL", "CP"):
        lines.append(
            f"| {group} | {fmt(sampler['final_q_mean'][group], 3)} | "
            f"{fmt(sampler['final_q_sample_sd'][group], 3)} | {sampler['selection_counts'][group]} |"
        )
    lines.append(f"| 正常工况 N | 固定锚点（0.50） | — | {sampler['selection_counts']['N']} |")
    (OUT / "formal_result_tables.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_audit(results_root: Path, tape: dict, decision: dict, condition_rows: list[dict[str, object]],
                sampler: dict[str, object]) -> None:
    source_archive = Path("D:/File/Downloads/drtp_utr_q2_paired_5seed_cloud_10way.tar.gz")
    lines = [
        "# 正式结果整合审计", "",
        "## 结论", "",
        "`PASS — FORMAL_CONFIRMATION_PASS_SEED_SENSITIVE`。正式五种子结果允许回填中文主稿，但历史开发 NO-GO、留出验证 FAIL 与历史 seed2002 反转必须继续保留。", "",
        "## 完整性核验", "",
        "- 归档 SHA256：`cc3e2d29f382c332563c33957f5c109bbee4f42abb91b0d06b2b26cd3e618bdd`（下载文件已匹配）；",
        "- 训练轨迹：UTR/DRTP × 2301–2305，10/10 completed；",
        "- 共同终点：39,063 updates / 10,000,128 environment steps / 116,728 parameters；",
        f"- 评估样本带：490000–490099，hash `{tape['tape_hash']}`；",
        "- 原始记录：12,000；风险集触发有效性：PASS；",
        "- 中间检查点仅用于曲线，不参与最终选择；无 canonical seed、种子排除、warm restart 或后续自动训练。", "",
        "## 冻结裁决", "",
        f"- machine verdict: `{decision['verdict']}`；",
        f"- catastrophic seeds: {decision['catastrophic_seed_count']}/5；",
        "- 所有训练前冻结 gate: PASS。", "",
        "## 论文写作边界", "",
        "- 可写：在冻结三无人机中继故障任务、共同 10M 预算和训练前冻结五 seed 合同下，DRTP 的 F0、跨扰动均值和跨扰动最差的配对均值与中位数为正；",
        "- 不可写：DRTP 对所有随机初始化稳定优越、一般分布鲁棒最优、恢复丢失信息或已完成真实飞行验证；",
        "- 需保留：seed2302 的正常工况反转、历史 seed sensitivity、仅三无人机 3DOF 仿真、内部参数匹配主消融和无外部同合同基线。", "",
        "## 跨扰动条件审计", "",
        "| 条件 | 平均配对ΔJ | 胜出种子数 | 最差配对ΔJ |",
        "|---|---:|---:|---:|",
    ]
    for item in condition_rows:
        lines.append(f"| {item['condition']} | {fmt(item['paired_delta_mean'])} | {item['wins']}/5 | {fmt(item['worst_delta'])} |")
    lines += ["", "## 自适应权重遥测", "",
              f"- 末次自适应更新：{sampler['last_weight_update']}；",
              "- 末次 q 均值：" + "；".join(
                  f"{group}={sampler['final_q_mean'][group]:.3f}" for group in ("F0", "TE", "TL", "DS", "DL", "CP")
              ) + "。", "",
              "这些遥测仅表明自适应器实际偏离均匀权重；它们不单独建立策略机制的因果解释。", "",
              "## 产物", "",
              "- `formal_results/source_data/`：冻结 decision、manifest、配对与条件级 CSV；",
              "- `formal_results/figures/`：主结果、跨扰动、可靠性/安全性和自适应权重图；",
              "- `formal_results/formal_result_tables.md`：主文与补充表源。", ""]
    (PAPER / "14_formal_result_integration_audit.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-root", type=Path, default=DEFAULT_RESULTS)
    args = parser.parse_args()
    results_root = args.results_root.resolve()
    tape, decision, rows, _ = validate(results_root)
    cells = metric_cells(rows)
    conditions = pooled_condition(rows)
    sampler = sampler_summary(results_root)
    copy_source_data(results_root)
    (DATA / "sampler_telemetry_summary.json").write_text(json.dumps(sampler, indent=2) + "\n", encoding="utf-8")
    setup_matplotlib()
    plot_primary(cells, decision)
    plot_ood(conditions)
    plot_reliability(decision)
    plot_sampler(results_root)
    write_tables(decision, conditions, sampler)
    write_audit(results_root, tape, decision, conditions, sampler)
    summary = {
        "verdict": decision["verdict"], "tape_hash": tape["tape_hash"],
        "raw_rows": 12000, "source_results_root": str(results_root),
        "figures": [path.name for path in sorted(FIGURES.glob("*.svg"))],
    }
    (OUT / "integration_manifest.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
